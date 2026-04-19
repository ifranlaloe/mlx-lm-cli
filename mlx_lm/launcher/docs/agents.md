# Launcher implementation guide

## Mission
Implement **Ollama launch parity** for `mlx-lm` so coding CLIs can be launched with predictable model/provider wiring.

## Product target
`mlx_lm launch <integration>` should match the practical behavior of `ollama launch <integration>` for:
1. Codex
2. GitHub Copilot CLI
3. Claude Code
4. OpenCode

## Source-of-truth references
Use these as implementation specs:
- `ollama/ollama`:
  - `cmd/launch/launch.go`
  - `cmd/launch/{codex,claude,copilot,opencode}.go`
  - `cmd/launch/*_test.go`
  - `cmd/config/config.go`
  - `docs/integrations/{codex,claude-code,copilot-cli,opencode}.mdx`
  - `docs/api/{openai-compatibility,anthropic-compatibility}.mdx`
- `openai/codex` config reference (Responses-only provider wire API)
- `anomalyco/opencode` provider docs for OpenAI-compatible backends

## Compatibility contract (non-negotiable)
1. Preserve `launch` UX split: launcher args before `--`, integration args after `--`.
2. Preserve headless behavior: `--yes` in non-interactive mode requires explicit `--model`.
3. Keep configure-only mode (`--config`) and model persistence semantics.
4. Keep install/availability checks explicit and fail with actionable errors.
5. No silent fallbacks for missing endpoints, unsupported fields, or invalid model config.

## API surface required in MLX-LM
| Integration | API contract |
|---|---|
| Codex | OpenAI Responses API (`/v1/responses`) + model listing |
| Copilot CLI | OpenAI Responses API (`/v1/responses`) + model listing |
| Claude Code | Anthropic Messages API (`/v1/messages`) with streaming + tools |
| OpenCode (default Ollama-style setup) | OpenAI-compatible chat path (`/v1/chat/completions`) + model listing |

Notes:
- Responses support should follow Ollama's non-stateful subset (`previous_response_id` / `conversation` not required for MVP).
- Claude compatibility should follow Ollama's documented field support and streaming event shape.

## Config persistence requirements
1. Persist per-integration model selections in one canonical MLX config file (JSON).
2. Persist launcher-level defaults (`last_model`, `last_selection`) for menu behavior parity.
3. Preserve integration aliases/onboarding metadata if introduced.

## Implementation constraints
1. Keep integration-specific wiring isolated from core server logic.
2. Reuse shared helpers for arg parsing, readiness checks, and config I/O.
3. Do not hardcode model aliases; always keep full model IDs.
4. Keep docs and behavior in lockstep; update `mlx_lm/launcher/docs/*.md` when behavior changes.
5. Keep launcher implementation native Python under `mlx_lm/launcher/*` (no shell launcher scripts).

## Feature specs in this repo
- `mlx_lm/launcher/docs/codex.md`
- `mlx_lm/launcher/docs/github-copilot.md`
- `mlx_lm/launcher/docs/claude-code.md`
- `mlx_lm/launcher/docs/open-code.md`

## Validation baseline
After launch-related changes:
1. Verify launcher command/flag behavior and `--` passthrough.
2. Verify required env/config mutations per integration.
3. Verify endpoint-level compatibility against each integration's minimum contract.
