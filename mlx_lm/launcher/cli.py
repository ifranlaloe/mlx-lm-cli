# Copyright © 2026 Apple Inc.

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

DEFAULT_MODEL = "mlx-community/Qwen3.6-35B-A3B-4bit"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = "8080"
DEFAULT_WAIT_SECONDS = "30"

TARGET_BINARIES = {
    "codex": ("CODEX_CMD", "codex"),
    "claude": ("CLAUDE_CMD", "claude"),
    "copilot": ("COPILOT_CMD", "copilot"),
}


@dataclass
class LaunchConfig:
    target: str
    model: str
    host: str
    port: int
    wait_seconds: int
    app_args: List[str]


def _validate_non_empty(value: str, flag: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"Invalid {flag}: value cannot be empty.")
    return normalized


def _validate_int(
    raw_value: str, flag: str, *, minimum: int, maximum: Optional[int] = None
) -> int:
    try:
        value = int(raw_value)
    except ValueError as e:
        raise ValueError(f"Invalid {flag} '{raw_value}': must be an integer.") from e

    if value < minimum:
        if maximum is None:
            raise ValueError(f"Invalid {flag} '{raw_value}': must be >= {minimum}.")
        raise ValueError(
            f"Invalid {flag} '{raw_value}': must be between {minimum} and {maximum}."
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"Invalid {flag} '{raw_value}': must be between {minimum} and {maximum}."
        )

    return value


def _base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/v1"


def _server_is_ready(base_url: str) -> bool:
    url = f"{base_url}/models"
    try:
        with urlopen(url, timeout=1.5):
            return True
    except HTTPError as e:
        # The server is reachable even if auth/model checks fail.
        return e.code < 500
    except URLError:
        return False


def _wait_for_server(base_url: str, wait_seconds: int) -> bool:
    for _ in range(wait_seconds):
        if _server_is_ready(base_url):
            return True
        time.sleep(1)
    return _server_is_ready(base_url)


def _split_launcher_args(argv: Sequence[str]) -> Tuple[List[str], List[str]]:
    if "--" not in argv:
        return list(argv), []
    split_index = argv.index("--")
    return list(argv[:split_index]), list(argv[split_index + 1 :])


def _set_default_if_empty(env: Dict[str, str], key: str, value: str):
    if not env.get(key):
        env[key] = value


def _build_env(target: str, model: str, base_url: str) -> Dict[str, str]:
    env = os.environ.copy()
    env["MLX_BASE_URL"] = base_url
    env["MLX_MODEL"] = model

    if target in ("codex", "claude"):
        env["OPENAI_BASE_URL"] = base_url
        env["OPENAI_API_BASE"] = base_url
        _set_default_if_empty(env, "OPENAI_API_KEY", "local")
        _set_default_if_empty(env, "OPENAI_MODEL", model)
    elif target == "copilot":
        env["COPILOT_PROVIDER_BASE_URL"] = base_url
        _set_default_if_empty(env, "COPILOT_PROVIDER_TYPE", "openai")
        if not env.get("COPILOT_PROVIDER_BEARER_TOKEN") and not env.get(
            "COPILOT_PROVIDER_API_KEY"
        ):
            env["COPILOT_PROVIDER_API_KEY"] = "local"
        _set_default_if_empty(env, "COPILOT_MODEL", model)
    else:
        raise ValueError(f"Unsupported launch target: {target}")

    return env


def _command_for_target(target: str) -> str:
    env_key, default = TARGET_BINARIES[target]
    command = os.getenv(env_key, default).strip()
    if not command:
        raise ValueError(f"Invalid ${env_key}: value cannot be empty.")
    if shutil.which(command) is None:
        raise ValueError(f"Required command not found: {command}")
    return command


def _print_launch_message(target: str, env: Dict[str, str]):
    if target == "codex":
        print(
            f"Launching Codex (endpoint: {env['OPENAI_BASE_URL']}, model: {env['OPENAI_MODEL']})"
        )
    elif target == "claude":
        print(
            "Launching Claude CLI "
            f"(endpoint: {env['OPENAI_BASE_URL']}, model: {env['OPENAI_MODEL']})"
        )
    elif target == "copilot":
        print(
            "Launching Copilot CLI "
            f"(provider: {env['COPILOT_PROVIDER_BASE_URL']}, model: {env['COPILOT_MODEL']})"
        )


def _parse_args(argv: Sequence[str]) -> LaunchConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Launch Codex, Claude CLI, or GitHub Copilot against an already-running "
            "mlx_lm server."
        )
    )
    parser.add_argument(
        "target",
        choices=tuple(TARGET_BINARIES),
        help="Integration to launch.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=os.getenv("MODEL", DEFAULT_MODEL),
        help=f"Model ID (default: env MODEL or {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", DEFAULT_HOST),
        help=f"Server host (default: env HOST or {DEFAULT_HOST}).",
    )
    parser.add_argument(
        "--port",
        default=os.getenv("PORT", DEFAULT_PORT),
        help=f"Server port (default: env PORT or {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--wait-seconds",
        default=os.getenv("MLX_WAIT_SECONDS", DEFAULT_WAIT_SECONDS),
        help=(
            "Seconds to wait for server readiness "
            f"(default: env MLX_WAIT_SECONDS or {DEFAULT_WAIT_SECONDS})."
        ),
    )

    launcher_argv, app_args = _split_launcher_args(argv)
    args, unknown = parser.parse_known_args(launcher_argv)
    if unknown:
        parser.error(
            f"Unknown launcher arg(s): {' '.join(unknown)}. "
            f"Use -- to pass args to {args.target}."
        )

    try:
        model = _validate_non_empty(args.model, "--model")
        host = _validate_non_empty(args.host, "--host")
        port = _validate_int(args.port, "--port", minimum=1, maximum=65535)
        wait_seconds = _validate_int(
            args.wait_seconds, "--wait-seconds", minimum=1
        )
    except ValueError as e:
        parser.error(str(e))

    return LaunchConfig(
        target=args.target,
        model=model,
        host=host,
        port=port,
        wait_seconds=wait_seconds,
        app_args=app_args,
    )


def main():
    config = _parse_args(sys.argv[1:])
    base_url = _base_url(config.host, config.port)
    try:
        command = _command_for_target(config.target)
    except ValueError as e:
        raise SystemExit(str(e))

    if not _wait_for_server(base_url, config.wait_seconds):
        raise SystemExit(
            "MLX server is not reachable at "
            f"{base_url}/models. Start it first with: "
            f'mlx_lm server --model "{config.model}" --host "{config.host}" --port "{config.port}"'
        )

    launch_env = _build_env(config.target, config.model, base_url)
    _print_launch_message(config.target, launch_env)
    completed = subprocess.run([command, *config.app_args], env=launch_env, check=False)
    raise SystemExit(completed.returncode)
