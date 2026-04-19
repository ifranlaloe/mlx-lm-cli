# Claude Code launch feature spec

## Goal
Make `mlx_lm launch claude` behave like `ollama launch claude`, using Anthropic-compatible local endpoints.

## Required launch behavior
1. Command shape: `mlx_lm launch claude [--model <id>] [--config] [--yes] [-- <claude args...>]`
2. Interactive integration/model selection when omitted.
3. `--config` updates launcher config and exits.
4. Arguments after `--` pass through unchanged to `claude`.

## Required Claude wiring
Runtime environment should mirror Ollama launch behavior:

- `ANTHROPIC_BASE_URL=<mlx-host>` (no `/v1` suffix in env value)
- `ANTHROPIC_AUTH_TOKEN=ollama`
- `ANTHROPIC_API_KEY=` (empty)
- model tier env vars set from selected model (fallbacks when exact tier match is unknown)
- `CLAUDE_CODE_ATTRIBUTION_HEADER=0`

Binary behavior:
- launch `claude` CLI after env setup
- fail with actionable message when Claude Code is not installed

## Required backend API contract
MLX-LM must provide Anthropic-compatible message endpoint behavior:

1. `POST /v1/messages`
   - streaming and non-streaming
   - content blocks compatible with Claude Code expectations
   - tool use and tool result turn handling
2. Compatible error body/status structure for invalid requests

MVP compatibility stance:
- follow Ollama-documented Anthropic subset first
- unsupported optional fields (for example advanced metadata/tool-choice variants) may remain out of scope for MVP if clearly documented

## Acceptance criteria
1. `mlx_lm launch claude --model <id>` starts Claude Code against local MLX-LM.
2. Claude can run normal prompt/response sessions through `/v1/messages`.
3. Tool-calling session works end-to-end with local backend.
4. `mlx_lm launch claude --model <id> -- --help` preserves passthrough args.

## Non-goals (MVP)
- full parity with every Anthropic beta/extended field
- cross-provider cloud model routing in the launcher
