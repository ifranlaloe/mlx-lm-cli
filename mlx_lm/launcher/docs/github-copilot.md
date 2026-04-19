# GitHub Copilot CLI launch feature spec

## Goal
Make `mlx_lm launch copilot` behave like `ollama launch copilot`, targeting Copilot CLI provider mode.

## Required launch behavior
1. Command shape: `mlx_lm launch copilot [--model <id>] [--config] [--yes] [-- <copilot args...>]`
2. Interactive selection when integration/model are not explicitly provided.
3. `--config` writes launcher state and exits without starting Copilot CLI.
4. Arguments after `--` are forwarded unchanged to the Copilot CLI binary.

## Required Copilot wiring
Set runtime environment expected by Copilot provider mode:

- `COPILOT_PROVIDER_BASE_URL=<mlx-host>/v1`
- `COPILOT_PROVIDER_API_KEY=` (empty is valid for local mode)
- `COPILOT_PROVIDER_WIRE_API=responses`
- `COPILOT_MODEL=<selected-model>` when a model is selected

Binary behavior:
- launch `copilot` CLI command after env setup
- fail clearly if Copilot CLI is not installed

## Required backend API contract
Because Copilot is wired to Responses, MLX-LM must support:

1. `POST /v1/responses`
   - streaming and non-streaming
   - tool call and tool result blocks
2. `GET /v1/models` for model discovery/validation
3. OpenAI-style error format for invalid requests/models

MVP compatibility stance:
- non-stateful Responses support is acceptable.

## Acceptance criteria
1. `mlx_lm launch copilot --model <id>` starts Copilot CLI against local MLX-LM.
2. Copilot prompt/response round-trip works through `/v1/responses`.
3. Tool-calling flow works without provider protocol mismatches.
4. `mlx_lm launch copilot --model <id> -- --help` preserves argument passthrough.

## Non-goals (MVP)
- support for non-Responses wire APIs in Copilot launcher
- cloud auth/token management for Copilot-hosted providers
