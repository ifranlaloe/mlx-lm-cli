#!/usr/bin/env bash

MLX_DEFAULT_MODEL="mlx-community/Qwen3.6-35B-A3B-4bit"
MLX_DEFAULT_HOST="127.0.0.1"
MLX_DEFAULT_PORT="8080"
MLX_DEFAULT_WAIT_SECONDS="30"

mlx_die() {
  echo "$1" >&2
  exit 1
}

mlx_require_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || mlx_die "Required command not found: $cmd"
}

mlx_validate_non_empty() {
  local value="$1"
  local label="$2"
  [[ -n "${value//[[:space:]]/}" ]] || mlx_die "Invalid $label: value cannot be empty."
}

mlx_validate_port() {
  local port="$1"
  [[ "$port" =~ ^[0-9]+$ ]] || mlx_die "Invalid --port '$port': must be an integer."
  ((port >= 1 && port <= 65535)) || mlx_die "Invalid --port '$port': must be between 1 and 65535."
}

mlx_validate_wait_seconds() {
  local wait_seconds="$1"
  [[ "$wait_seconds" =~ ^[0-9]+$ ]] || mlx_die "Invalid --wait-seconds '$wait_seconds': must be an integer."
  ((wait_seconds >= 1)) || mlx_die "Invalid --wait-seconds '$wait_seconds': must be >= 1."
}

mlx_validate_common_config() {
  mlx_validate_non_empty "$MLX_MODEL" "--model"
  mlx_validate_non_empty "$MLX_HOST" "--host"
  mlx_validate_port "$MLX_PORT"
}

mlx_parse_server_args() {
  MLX_MODEL="${MODEL:-$MLX_DEFAULT_MODEL}"
  MLX_HOST="${HOST:-$MLX_DEFAULT_HOST}"
  MLX_PORT="${PORT:-$MLX_DEFAULT_PORT}"
  MLX_SERVER_ARGS=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -m|--model)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --model"
        MLX_MODEL="$2"
        shift 2
        ;;
      --model=*)
        MLX_MODEL="${1#*=}"
        shift
        ;;
      --host)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --host"
        MLX_HOST="$2"
        shift 2
        ;;
      --host=*)
        MLX_HOST="${1#*=}"
        shift
        ;;
      --port)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --port"
        MLX_PORT="$2"
        shift 2
        ;;
      --port=*)
        MLX_PORT="${1#*=}"
        shift
        ;;
      --)
        shift
        MLX_SERVER_ARGS+=("$@")
        break
        ;;
      *)
        MLX_SERVER_ARGS+=("$1")
        shift
        ;;
    esac
  done

  mlx_validate_common_config
}

mlx_parse_launcher_args() {
  MLX_MODEL="${MODEL:-$MLX_DEFAULT_MODEL}"
  MLX_HOST="${HOST:-$MLX_DEFAULT_HOST}"
  MLX_PORT="${PORT:-$MLX_DEFAULT_PORT}"
  MLX_WAIT_SECONDS="${MLX_WAIT_SECONDS:-$MLX_DEFAULT_WAIT_SECONDS}"
  MLX_SERVER_ARGS=()
  MLX_APP_ARGS=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -m|--model)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --model"
        MLX_MODEL="$2"
        shift 2
        ;;
      --model=*)
        MLX_MODEL="${1#*=}"
        shift
        ;;
      --host)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --host"
        MLX_HOST="$2"
        shift 2
        ;;
      --host=*)
        MLX_HOST="${1#*=}"
        shift
        ;;
      --port)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --port"
        MLX_PORT="$2"
        shift 2
        ;;
      --port=*)
        MLX_PORT="${1#*=}"
        shift
        ;;
      --wait-seconds)
        [[ $# -ge 2 ]] || mlx_die "Missing value for --wait-seconds"
        MLX_WAIT_SECONDS="$2"
        shift 2
        ;;
      --wait-seconds=*)
        MLX_WAIT_SECONDS="${1#*=}"
        shift
        ;;
      --)
        shift
        MLX_APP_ARGS=("$@")
        break
        ;;
      *)
        MLX_SERVER_ARGS+=("$1")
        shift
        ;;
    esac
  done

  mlx_validate_common_config
  mlx_validate_wait_seconds "$MLX_WAIT_SECONDS"
}

mlx_server_base_url() {
  local host="$1"
  local port="$2"
  printf 'http://%s:%s/v1' "$host" "$port"
}

mlx_server_is_ready() {
  local host="$1"
  local port="$2"
  local base_url
  base_url="$(mlx_server_base_url "$host" "$port")"
  curl -fsS --connect-timeout 1 --max-time 2 "${base_url}/models" >/dev/null 2>&1
}

mlx_wait_for_server() {
  local host="$1"
  local port="$2"
  local wait_seconds="$3"
  local pid="${4:-}"
  local i=0

  while [[ $i -lt $wait_seconds ]]; do
    if mlx_server_is_ready "$host" "$port"; then
      return 0
    fi
    if [[ -n "$pid" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
      return 1
    fi
    i=$((i + 1))
    sleep 1
  done

  return 1
}
