# AGENTS.md

## Mission
Build and maintain a minimal, reliable local model runtime for Apple Silicon using `mlx-lm`, with clean launch paths for Codex, Claude, and Copilot.

## Primary goal
Expose a stable OpenAI-compatible local endpoint and make app launchers predictable, explicit, and easy to debug.

## Ground truth
- Runtime: `mlx-lm`
- Default model: `mlx-community/Qwen3.6-35B-A3B-4bit`
- Hardware baseline: Apple M4 Pro, 48 GB unified memory, Metal 4
- Model downloads are cached under Hugging Face Hub (`~/.cache/huggingface/hub/` unless overridden by `HF_HOME` or `HUGGINGFACE_HUB_CACHE`)

## Non-negotiable architecture rules
1. `cli/scripts/server` is provider-agnostic.
2. `cli/scripts/lib.sh` is provider-agnostic.
3. Provider/app-specific env wiring lives only in `cli/scripts/launchers/*`.
4. Do not add model aliases. Always use full Hugging Face model IDs.
5. Preserve the `--` split contract (launcher args before `--`, app args after `--`).

## Script architecture
- `cli/scripts/mlxlm`  
  Dispatcher entrypoint (`server`, `codex`, `claude`, `copilot`, `launch <target>`).
- `cli/scripts/server`  
  Starts `mlx_lm server` only.
- `cli/scripts/launchers/codex`  
  Attaches to running server, then launches Codex.
- `cli/scripts/launchers/claude`  
  Attaches to running server, then launches Claude.
- `cli/scripts/launchers/copilot`  
  Attaches to running server, then launches Copilot (BYOK).
- `cli/scripts/lib.sh`  
  Shared parsing, validation, and server readiness checks.

## CLI contract
- Start server only:
  - `./cli/scripts/mlxlm server --model mlx-community/Qwen3.6-35B-A3B-4bit`
- Launch app (requires server already running):
  - `./cli/scripts/mlxlm codex --model mlx-community/Qwen3.6-35B-A3B-4bit`
  - `./cli/scripts/mlxlm claude --model mlx-community/Qwen3.6-35B-A3B-4bit`
  - `./cli/scripts/mlxlm copilot --model mlx-community/Qwen3.6-35B-A3B-4bit`
- Pass app args after `--`:
  - `./cli/scripts/mlxlm codex --model mlx-community/Qwen3.6-35B-A3B-4bit -- --help`

## Bash quality bar
1. Keep `set -euo pipefail`.
2. Quote all variable expansions unless intentional word splitting is required.
3. Use arrays for downstream arg forwarding.
4. Validate user inputs (`model`, `host`, `port`, timeouts) with explicit error messages.
5. Fail fast; avoid silent fallbacks.
6. Keep help text accurate and synchronized with behavior.

## Change policy for agents
When modifying scripts:
1. Preserve separation of concerns (dispatcher vs server vs launchers vs lib).
2. Prefer extending shared generic helpers in `lib.sh` over duplicating parsing logic.
3. Never move provider-specific logic into `server` or `lib.sh`.
4. Keep behavior backward-compatible unless intentionally changed and documented.
5. Update this file when command contracts or architecture change.

## Validation checklist
Run these after script changes:
- `bash -n cli/scripts/lib.sh cli/scripts/server cli/scripts/mlxlm cli/scripts/launchers/codex cli/scripts/launchers/claude cli/scripts/launchers/copilot`
- `./cli/scripts/mlxlm --help`
- `./cli/scripts/server --help`
- `./cli/scripts/launchers/codex --help`
- `./cli/scripts/launchers/claude --help`
- `./cli/scripts/launchers/copilot --help`

## Security and operational notes
- Do not commit tokens, keys, or private endpoints.
- Keep defaults local-first (`127.0.0.1` and local model IDs unless explicitly changed).
- Prefer deterministic behavior over convenience magic.
