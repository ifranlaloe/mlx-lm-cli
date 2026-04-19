# mlx-lm local launcher stack

Minimal, script-first runtime for serving `mlx-lm` models on Apple Silicon and launching local AI CLIs (Codex, Claude, Copilot) against that server.

## Target model

- `mlx-community/Qwen3.6-35B-A3B-4bit`

No short aliases are used in scripts; always pass the full Hugging Face model ID.

## Architecture

| Path | Responsibility |
|---|---|
| `cli/scripts/mlxlm` | Dispatcher (`server`, `codex`, `claude`, `copilot`, `launch <target>`) |
| `cli/scripts/server` | Provider-agnostic MLX server process (`mlx_lm server ...`) |
| `cli/scripts/launchers/codex` | Attaches to running server, exports Codex/OpenAI env, launches `codex` |
| `cli/scripts/launchers/claude` | Attaches to running server, exports Claude/OpenAI env, launches `claude` |
| `cli/scripts/launchers/copilot` | Attaches to running server, exports Copilot BYOK env, launches `copilot` |
| `cli/scripts/lib.sh` | Shared parsing, validation, and server readiness checks |

## Design contract

1. `cli/scripts/server` and `cli/scripts/lib.sh` stay provider-agnostic.
2. Provider-specific env wiring lives only in `cli/scripts/launchers/*`.
3. `--` is the argument boundary for launchers:  
   - before `--` => launcher args  
   - after `--` => app CLI args
4. Launchers do **not** auto-start or stop the server.
5. `mlxlm server ...` is step 1; `mlxlm codex|claude|copilot ...` is step 2.

## Prerequisites

- macOS on Apple Silicon
- Python 3.11+ (3.13 works)
- installed CLI(s) you want to launch (`codex`, `claude`, `copilot`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -U mlx-lm
chmod +x cli/scripts/mlxlm cli/scripts/server cli/scripts/launchers/codex cli/scripts/launchers/claude cli/scripts/launchers/copilot
```

Optional: wire `mlxlm` in your shell config (no symlinks):

```bash
cat >> ~/.zshrc <<'EOF'
mlxlm() { "/absolute/path/to/mlx-lm/cli/scripts/mlxlm" "$@"; }
EOF
source ~/.zshrc
mlxlm --help
```

Replace `/absolute/path/to/mlx-lm` with your actual repository path.

If you prefer no shell function, run the script directly: `./cli/scripts/mlxlm ...`

Optional first-run warmup:

```bash
source .venv/bin/activate
mlx_lm generate --model mlx-community/Qwen3.6-35B-A3B-4bit --prompt "ready" --max-tokens 1
```

## Usage

### 1) Run persistent server (recommended for multi-session use)

```bash
./cli/scripts/mlxlm server --model mlx-community/Qwen3.6-35B-A3B-4bit
```

Endpoint:

```text
http://127.0.0.1:8080/v1
```

### 2) Launch app against the running server

```bash
./cli/scripts/mlxlm codex   --model mlx-community/Qwen3.6-35B-A3B-4bit
./cli/scripts/mlxlm claude  --model mlx-community/Qwen3.6-35B-A3B-4bit
./cli/scripts/mlxlm copilot --model mlx-community/Qwen3.6-35B-A3B-4bit
```

### 3) Pass app arguments after `--`

```bash
./cli/scripts/mlxlm codex --model mlx-community/Qwen3.6-35B-A3B-4bit -- --help
./cli/scripts/mlxlm codex --model mlx-community/Qwen3.6-35B-A3B-4bit -- --full-auto
```

### 4) Override host/port

```bash
./cli/scripts/mlxlm server --model mlx-community/Qwen3.6-35B-A3B-4bit --host 0.0.0.0 --port 8081
./cli/scripts/mlxlm codex  --model mlx-community/Qwen3.6-35B-A3B-4bit --host 127.0.0.1 --port 8081
```

## Environment variables

### Common

| Variable | Default |
|---|---|
| `MODEL` | `mlx-community/Qwen3.6-35B-A3B-4bit` |
| `HOST` | `127.0.0.1` |
| `PORT` | `8080` |
| `MLX_WAIT_SECONDS` | `30` (launchers) |
| `VENV_DIR` | `./.venv` (server) |

### Launcher-specific executable override

| Launcher | Variable | Default |
|---|---|---|
| Codex | `CODEX_CMD` | `codex` |
| Claude | `CLAUDE_CMD` | `claude` |
| Copilot | `COPILOT_CMD` | `copilot` |

### Provider env behavior

- `launchers/codex` and `launchers/claude` export `OPENAI_*` values for local endpoint use.
- `launchers/copilot` exports `COPILOT_PROVIDER_*` (BYOK/OpenAI-compatible mode).

## Model cache location

By default:

```text
~/.cache/huggingface/hub/models--mlx-community--Qwen3.6-35B-A3B-4bit/
```

If `HF_HOME` or `HUGGINGFACE_HUB_CACHE` is set, cache moves under that location.

## Troubleshooting

- **`Missing virtual environment`**: create `.venv` and install `mlx-lm`.
- **`Required command not found`**: install missing CLI (`codex`, `claude`, or `copilot`) or override `*_CMD`.
- **`Invalid --port`**: must be integer in range `1..65535`.
- **Server readiness timeout**: ensure `mlxlm server ...` is running, then retry launcher (`codex`, `claude`, or `copilot`).

## Script validation

```bash
bash -n cli/scripts/lib.sh cli/scripts/server cli/scripts/mlxlm cli/scripts/launchers/codex cli/scripts/launchers/claude cli/scripts/launchers/copilot
./cli/scripts/mlxlm --help
./cli/scripts/server --help
./cli/scripts/launchers/codex --help
./cli/scripts/launchers/claude --help
./cli/scripts/launchers/copilot --help
```
