# OpenCode launch feature spec

## Goal
Make `mlx_lm launch opencode` behave like `ollama launch opencode`, using OpenCode provider config injection.

## Required launch behavior
1. Command shape: `mlx_lm launch opencode [--model <id>] [--config] [--yes] [-- <opencode args...>]`
2. Interactive integration/model selection when omitted.
3. `--config` updates launcher/config state and exits.
4. Arguments after `--` are passed unchanged to OpenCode.

## Required OpenCode wiring
Mirror Ollama launch strategy:

1. Provide provider/model config through `OPENCODE_CONFIG_CONTENT` (inline JSON), not by mutating project config files.
2. Inject provider entry for local backend:
   - provider package: `@ai-sdk/openai-compatible`
   - base URL: `<mlx-host>/v1`
   - model namespace: `ollama/<model>`-style logical IDs (or equivalent local namespace strategy)
3. Set selected model as OpenCode default in injected config.
4. Maintain OpenCode model history state file (`~/.local/state/opencode/model.json`) with dedupe and bounded recents behavior.

Binary behavior:
- launch `opencode` after env setup
- fail clearly if binary is missing

## Required backend API contract
For the default OpenCode provider wiring above, MLX-LM must support:

1. `POST /v1/chat/completions` (OpenAI-compatible path)
   - streaming and non-streaming
   - tool call support required by OpenCode workflows
2. `GET /v1/models` for model listing

Important note:
- OpenCode can also use OpenAI Responses through `@ai-sdk/openai`, but Ollama's current launch integration targets `@ai-sdk/openai-compatible`. Match that first for parity.

## Acceptance criteria
1. `mlx_lm launch opencode --model <id>` starts OpenCode with injected local provider config.
2. OpenCode prompt/response works against local MLX-LM without manual config edits.
3. Model history/state is updated in a stable deduped manner.
4. `mlx_lm launch opencode --model <id> -- --help` preserves arg passthrough.

## Non-goals (MVP)
- replacing OpenCode's persistent project config model
- implementing alternate provider packages beyond the parity target path
