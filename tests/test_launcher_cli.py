import importlib.util
import io
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


def load_launcher_module():
    module_path = Path(__file__).resolve().parents[1] / "mlx_lm" / "launcher" / "cli.py"
    spec = importlib.util.spec_from_file_location("mlx_lm_launcher_cli_test", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


launcher_cli = load_launcher_module()


class TestLauncherCLI(unittest.TestCase):
    def test_parse_args_forwards_app_args_after_separator(self):
        with patch.dict(os.environ, {}, clear=True):
            config = launcher_cli._parse_args(
                ["codex", "--model", "repo/model", "--", "--help"]
            )
        self.assertEqual(config.target, "codex")
        self.assertEqual(config.model, "repo/model")
        self.assertEqual(config.app_args, ["--help"])

    def test_parse_args_requires_model_when_missing(self):
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr", stderr):
                with self.assertRaises(SystemExit) as ex:
                    launcher_cli._parse_args(["codex"])
        self.assertEqual(ex.exception.code, 2)
        self.assertIn("Missing required --model.", stderr.getvalue())

    def test_parse_args_uses_model_from_environment(self):
        with patch.dict(os.environ, {"MODEL": "repo/from-env"}, clear=True):
            config = launcher_cli._parse_args(["codex"])
        self.assertEqual(config.model, "repo/from-env")

    def test_parse_args_accepts_explicit_cwd(self):
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {}, clear=True):
                config = launcher_cli._parse_args(
                    ["codex", "--model", "repo/model", "--cwd", tmp]
                )
        self.assertEqual(config.launch_cwd, tmp)

    def test_parse_args_rejects_unknown_launcher_flags(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as ex:
                launcher_cli._parse_args(["codex", "--bad-flag"])
        self.assertEqual(ex.exception.code, 2)
        self.assertIn("Unknown launcher arg(s): --bad-flag", stderr.getvalue())

    def test_default_launch_cwd_falls_back_to_oldpwd_from_repo_wrapper(self):
        repo_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            with (
                patch.object(launcher_cli.Path, "cwd", return_value=repo_root),
                patch.dict(os.environ, {"OLDPWD": tmp}, clear=True),
            ):
                launch_cwd = launcher_cli._default_launch_cwd()
        self.assertEqual(launch_cwd, tmp)

    def test_copilot_env_defaults_to_responses_wire_api(self):
        with patch.dict(os.environ, {}, clear=True):
            env = launcher_cli._build_env(
                "copilot",
                "mlx-community/Qwen3.6-35B-A3B-4bit",
                "http://127.0.0.1:8080/v1",
            )
        self.assertEqual(env["COPILOT_PROVIDER_BASE_URL"], "http://127.0.0.1:8080/v1")
        self.assertEqual(env["COPILOT_PROVIDER_WIRE_API"], "responses")
        self.assertEqual(env["COPILOT_PROVIDER_API_KEY"], "local")

    def test_copilot_env_preserves_wire_api_if_preconfigured(self):
        with patch.dict(
            os.environ,
            {"COPILOT_PROVIDER_WIRE_API": "responses"},
            clear=True,
        ):
            env = launcher_cli._build_env(
                "copilot",
                "mlx-community/Qwen3.6-35B-A3B-4bit",
                "http://127.0.0.1:8080/v1",
            )
        self.assertEqual(env["COPILOT_PROVIDER_WIRE_API"], "responses")

    def test_main_cli_dispatch_supports_launch_subcommand(self):
        cli_module_path = Path(__file__).resolve().parents[1] / "mlx_lm" / "cli.py"
        text = cli_module_path.read_text(encoding="utf-8")
        self.assertIn('"launch"', text)

    def test_codex_launch_command_uses_profile_and_model(self):
        model = "mlx-community/Qwen3.6-35B-A3B-4bit"
        base_url = "http://127.0.0.1:8080/v1"
        launch_cwd = "/tmp/workspace"
        command = launcher_cli._build_launch_command(
            "codex",
            "codex",
            model,
            base_url,
            ["--help"],
            launch_cwd,
        )

        self.assertEqual(command[:3], ["codex", "--profile", launcher_cli.CODEX_PROFILE_NAME])
        self.assertEqual(command[3:5], ["-m", model])
        self.assertEqual(command[5:7], ["--cd", launch_cwd])
        self.assertEqual(command[-1], "--help")

    def test_codex_launch_command_preserves_explicit_cwd_arg(self):
        model = "mlx-community/Qwen3.6-35B-A3B-4bit"
        base_url = "http://127.0.0.1:8080/v1"
        command = launcher_cli._build_launch_command(
            "codex",
            "codex",
            model,
            base_url,
            ["--cd", "/my/project", "--help"],
            "/tmp/workspace",
        )
        self.assertEqual(command.count("--cd"), 1)
        self.assertIn("/my/project", command)

    def test_non_codex_launch_command_is_passthrough(self):
        command = launcher_cli._build_launch_command(
            "copilot",
            "copilot",
            "ignored",
            "http://127.0.0.1:8080/v1",
            ["--help"],
            "/tmp/workspace",
        )
        self.assertEqual(command, ["copilot", "--help"])

    def test_main_runs_target_in_resolved_cwd(self):
        config = launcher_cli.LaunchConfig(
            target="copilot",
            model="mlx-community/Qwen3.6-35B-A3B-4bit",
            host="127.0.0.1",
            port=8080,
            wait_seconds=30,
            launch_cwd="/tmp/workspace",
            app_args=["--help"],
        )
        with (
            patch.object(launcher_cli, "_parse_args", return_value=config),
            patch.object(launcher_cli, "_command_for_target", return_value="copilot"),
            patch.object(launcher_cli, "_wait_for_server", return_value=True),
            patch.object(launcher_cli, "_build_env", return_value={}),
            patch.object(
                launcher_cli,
                "_build_launch_command",
                return_value=["copilot", "--help"],
            ),
            patch.object(launcher_cli, "_print_launch_message"),
            patch.object(launcher_cli.subprocess, "run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            with self.assertRaises(SystemExit) as ex:
                launcher_cli.main()

        self.assertEqual(ex.exception.code, 0)
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["cwd"], "/tmp/workspace")

    def test_ensure_codex_config_writes_profile_and_provider_sections(self):
        with TemporaryDirectory() as tmp:
            with patch.object(launcher_cli.Path, "home", return_value=Path(tmp)):
                launcher_cli._ensure_codex_config("http://127.0.0.1:8080/v1")

            config_path = Path(tmp) / ".codex" / "config.toml"
            content = config_path.read_text(encoding="utf-8")
            self.assertIn(f"[profiles.{launcher_cli.CODEX_PROFILE_NAME}]", content)
            self.assertIn(
                f'model_provider = "{launcher_cli.CODEX_PROFILE_NAME}"',
                content,
            )
            self.assertIn(f"[model_providers.{launcher_cli.CODEX_PROFILE_NAME}]", content)
            self.assertIn('name = "MLX"', content)
            self.assertIn('base_url = "http://127.0.0.1:8080/v1/"', content)

    def test_ensure_codex_config_replaces_existing_sections(self):
        with TemporaryDirectory() as tmp:
            codex_dir = Path(tmp) / ".codex"
            codex_dir.mkdir(parents=True, exist_ok=True)
            config_path = codex_dir / "config.toml"
            config_path.write_text(
                (
                    f"[profiles.{launcher_cli.CODEX_PROFILE_NAME}]\n"
                    'openai_base_url = "http://old:1234/v1/"\n'
                    "\n"
                    f"[model_providers.{launcher_cli.CODEX_PROFILE_NAME}]\n"
                    'name = "Old"\n'
                    'base_url = "http://old:1234/v1/"\n'
                    "\n"
                    "[other]\n"
                    'key = "value"\n'
                ),
                encoding="utf-8",
            )

            with patch.object(launcher_cli.Path, "home", return_value=Path(tmp)):
                launcher_cli._ensure_codex_config("http://127.0.0.1:8080/v1")

            content = config_path.read_text(encoding="utf-8")
            self.assertNotIn("old:1234", content)
            self.assertEqual(
                content.count(f"[profiles.{launcher_cli.CODEX_PROFILE_NAME}]"),
                1,
            )
            self.assertEqual(
                content.count(f"[model_providers.{launcher_cli.CODEX_PROFILE_NAME}]"),
                1,
            )
            self.assertIn("[other]", content)


if __name__ == "__main__":
    unittest.main()
