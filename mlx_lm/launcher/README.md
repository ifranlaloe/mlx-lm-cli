# mlx-lm launch integration (native Python)

This repo now uses a **native `mlx_lm` Python command flow** for local launcher behavior.

## Target model

- `mlx-community/Qwen3.6-35B-A3B-4bit`

## Architecture

| Path | Responsibility |
|---|---|
| `mlx_lm/cli.py` | Main `mlx_lm` dispatcher |
| `mlx_lm/launch.py` | Public launch entrypoint for `mlx_lm launch ...` |
| `mlx_lm/launcher/cli.py` | Integration launcher logic (Codex/Claude/Copilot) |

## Design contract

1. Keep launch integration in Python (`mlx_lm/launcher/*`), not shell scripts.
2. Keep server runtime native (`mlx_lm server ...`).
3. Preserve `--` argument boundary:
   - before `--` => launcher flags
   - after `--` => forwarded app CLI args
4. Launchers do **not** auto-start/stop the server.

## Prerequisites

- macOS on Apple Silicon
- Python 3.11+
- `mlx-lm` installed in your environment
- CLI(s) installed: `codex`, `claude`, and/or `copilot`

## Usage

### 1) Start MLX server

```bash
mlx_lm server --model mlx-community/Qwen3.6-35B-A3B-4bit
```

Default endpoint:

```text
http://127.0.0.1:8080/v1
```

### 2) Launch a coding CLI against that server

```bash
mlx_lm launch codex   --model mlx-community/Qwen3.6-35B-A3B-4bit
mlx_lm launch claude  --model mlx-community/Qwen3.6-35B-A3B-4bit
mlx_lm launch copilot --model mlx-community/Qwen3.6-35B-A3B-4bit
```

### 3) Pass app args after `--`

```bash
mlx_lm launch codex --model mlx-community/Qwen3.6-35B-A3B-4bit -- --help
mlx_lm launch codex --model mlx-community/Qwen3.6-35B-A3B-4bit -- --full-auto
```

### 4) Override host/port and wait timeout

```bash
mlx_lm launch codex \
  --model mlx-community/Qwen3.6-35B-A3B-4bit \
  --host 127.0.0.1 \
  --port 8081 \
  --wait-seconds 45
```

### 5) Launch in a specific working directory

```bash
mlx_lm launch codex --model mlx-community/Qwen3.6-35B-A3B-4bit --cwd "$PWD"
mlx_lm launch copilot --model mlx-community/Qwen3.6-35B-A3B-4bit --cwd "$PWD"
```

## Environment variables

### Common launcher defaults

| Variable | Default |
|---|---|
| `MODEL` | _(none)_ (model must be provided via `--model` or env `MODEL`) |
| `HOST` | `127.0.0.1` |
| `PORT` | `8080` |
| `MLX_WAIT_SECONDS` | `30` |
| `MLX_LAUNCH_CWD` | current directory |

If the launcher is invoked through a local shell wrapper that temporarily `cd`s
into this repo, launchers will fall back to `$OLDPWD` so Codex/Copilot still
open in your original shell directory.

### Executable override

| Launcher | Variable | Default |
|---|---|---|
| Codex | `CODEX_CMD` | `codex` |
| Claude | `CLAUDE_CMD` | `claude` |
| Copilot | `COPILOT_CMD` | `copilot` |

### Provider env behavior

- `mlx_lm launch codex` / `mlx_lm launch claude` exports `OPENAI_*` to local `/v1`.
- `mlx_lm launch copilot` exports `COPILOT_PROVIDER_*` for local provider mode.

## Quick checks

```bash
python3 -m mlx_lm --help
python3 -m mlx_lm launch --help
python3 -m mlx_lm server --help
```
