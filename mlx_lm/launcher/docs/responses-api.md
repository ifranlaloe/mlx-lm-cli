# Responses API feature spec

## Goal
Implement `POST /v1/responses` in local `mlx_lm` so Responses-wire clients (Codex and Copilot CLI) work without launcher workarounds.

## Trigger
Current local server behavior is missing `/v1/responses` and returns 404, while launcher docs/specs for Codex and Copilot require Responses wire compatibility.

## Research summary
1. **Current local gap (`mlx_lm/server.py`)**
   - Supported today: `POST /v1/completions`, `POST /v1/chat/completions`, `GET /v1/models`, `GET /health`.
   - Missing: `POST /v1/responses`.
2. **Codex compatibility requirements (openai/codex)**
   - Provider wire mode is Responses-focused.
   - Requests are streamed (`stream: true`) for normal operation.
   - Stream termination must include a final `response.completed` event; early EOF is treated as failure.
3. **Copilot CLI compatibility requirements (Ollama integration docs + launcher env contract)**
   - Provider mode expects `COPILOT_PROVIDER_WIRE_API=responses` against an OpenAI-compatible `/v1` base URL.
4. **Ollama reference design (ollama/server + openai adapters)**
   - Implements `/v1/responses` as a conversion layer over chat-generation internals.
   - Supports a non-stateful subset for MVP.
   - Explicitly rejects stateful fields (`previous_response_id`, `conversation`) with clear errors.

## MVP compatibility scope
### Endpoint
1. Add `POST /v1/responses`.
2. Support both `stream: false` and `stream: true`.
3. Return OpenAI-style error payloads and status codes for invalid requests.

### Request field support
| Field | MVP behavior |
|---|---|
| `model` | Validate against available model IDs; preserve explicit request model when present. |
| `input` | Accept string and array forms; convert to internal message list. |
| `instructions` | Convert to a leading `system` message. |
| `tools` | Pass through to existing tool-calling path. |
| `stream` | Select JSON response or SSE event stream mode. |
| `temperature`, `top_p` | Map directly to existing sampling params. |
| `max_output_tokens` | Map to existing `max_tokens`. |
| `text` | Accept known subfields; unsupported controls are ignored for MVP unless unsafe. |

### Explicitly unsupported in MVP
1. `previous_response_id`
2. `conversation`
3. Stateful server-side conversation persistence
4. WebSocket Responses transport
5. Multimodal/file inputs not already supported by local generation path

Unsupported fields must fail with clear `400` errors where appropriate (especially stateful fields), not silent success.

## Conversion rules
### Responses request -> internal generation request
1. Normalize `input` into chat-style messages:
   - string input -> single `user` message
   - message items -> corresponding role/content message entries
   - function call output items -> `tool` messages with `tool_call_id`
2. Apply `instructions` as a `system` preamble message.
3. Preserve tools and generation params.

### Internal generation output -> Responses output
1. Normal assistant text -> `message` output item with `output_text` content.
2. Tool call output -> `function_call` output item(s) with `name` and `arguments`.
3. Reasoning text (if present) -> Responses reasoning item shape compatible with client parsers.
4. Usage mapping:
   - prompt tokens -> `input_tokens`
   - completion tokens -> `output_tokens`
   - total -> `total_tokens`

## Streaming contract (`stream: true`)
Emit SSE events in Responses format (event-typed JSON), not chat delta chunks and not `[DONE]`.

Minimum event sequence for a successful text response:
1. `response.created`
2. `response.in_progress`
3. `response.output_item.added` (message item)
4. `response.output_text.delta` (one or more)
5. `response.output_item.done`
6. `response.completed` (terminal event, includes final response object/usage)

For tool-call responses, include corresponding function-call events/items and still terminate with `response.completed`.

If generation fails after stream start, emit `response.failed` with a structured error payload.

## Non-streaming contract (`stream: false`)
Return a single JSON `response` object containing:
1. `id`, `object`, `created_at`, `model`, `status`
2. `output` array with message/function_call/reasoning items
3. `usage` object

## Launcher follow-up after endpoint lands
Restore Copilot default env wiring to Responses mode in `mlx_lm/launcher/cli.py`:
1. set `COPILOT_PROVIDER_WIRE_API=responses` by default
2. preserve explicit user overrides if already present

## Implementation notes for this repo
1. Add Responses route handling in `mlx_lm/server.py` without breaking existing chat/completions behavior.
2. Reuse existing generation path; add conversion/serialization helpers instead of duplicating model generation logic.
3. Keep request validation and error handling explicit; no broad silent fallbacks.

## Acceptance criteria
1. Codex and Copilot can complete a prompt round-trip through local `/v1/responses`.
2. Streaming sessions end with `response.completed` reliably.
3. Tool-call responses are parseable by Responses clients.
4. Launcher tests enforce Responses wire default for Copilot after rollout.
5. Existing chat/completions endpoints remain unchanged.

## Validation targets
1. `tests/test_server.py`
   - add `/v1/responses` streaming and non-streaming coverage
   - add unsupported-field error coverage (`previous_response_id`, `conversation`)
2. `tests/test_launcher_cli.py`
   - restore expectation that Copilot defaults `COPILOT_PROVIDER_WIRE_API=responses`
   - keep override behavior tests

## Source references used
- `mlx_lm/server.py` (current local API routing and generation flow)
- `mlx_lm/launcher/docs/codex.md`
- `mlx_lm/launcher/docs/github-copilot.md`
- `ollama/ollama`:
  - `server/routes.go`
  - `middleware/openai.go`
  - `openai/responses.go`
  - `docs/api/openai-compatibility.mdx`
  - `docs/integrations/copilot-cli.mdx`
- `openai/codex`:
  - Responses request/stream client handling (provider wire behavior and SSE event expectations)
