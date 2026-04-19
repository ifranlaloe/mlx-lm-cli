# Codex launch feature spec

## Goal
Make `mlx_lm launch codex` behave like `ollama launch codex`, using a local MLX-LM backend.

## Required launch behavior
1. Command shape: `mlx_lm launch codex [--model <id>] [--config] [--yes] [-- <codex args...>]`
2. If integration is omitted, show interactive integration selection.
3. In non-interactive mode, `--yes` must require `--model`.
4. `--config` must update config and exit without launching Codex.
5. Extra args after `--` must be forwarded unchanged to the Codex binary.

## Required Codex config wiring
Update `~/.codex/config.toml` with an MLX profile/provider (Ollama-style).

Minimum settings:
- `forced_login_method = "api"`
- provider base URL points to MLX OpenAI-compatible root with trailing `/v1/`
- provider wire API is Responses (`wire_api = "responses"`)
- profile references that provider and selected model

Launch command target:
- `codex --profile <mlx-profile> [-m <model>] <extra args...>`

Runtime environment:
- `OPENAI_API_KEY=ollama` (placeholder key accepted by local backend)

Version gate:
- enforce minimum Codex version compatible with custom providers and Responses wiring.

## Required backend API contract
MLX-LM must expose OpenAI-compatible endpoints needed by Codex:

1. `POST /v1/responses`
   - streaming and non-streaming
   - tool calls / tool results blocks
   - reasoning/content output blocks Codex expects
2. `GET /v1/models` (or equivalent model listing endpoint Codex uses)
3. Error responses compatible with OpenAI-style status/body patterns

MVP compatibility stance:
- non-stateful Responses is acceptable (no `previous_response_id` / `conversation` persistence requirement for MVP).

## Acceptance criteria
1. `mlx_lm launch codex --model <id>` launches Codex connected to local MLX-LM without manual config edits.
2. `mlx_lm launch codex --config --model <id>` writes config only.
3. `mlx_lm launch codex --model <id> -- --help` passes args through correctly.
4. Codex can complete a normal prompt round-trip via `/v1/responses`.
5. Codex tool-calling sessions run without protocol errors.

## Non-goals (MVP)
- implementing full stateful Responses conversations
- implementing websocket transport unless explicitly required later
