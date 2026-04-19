import importlib.util
import io
import os
import sys
import unittest
from pathlib import Path
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

    def test_parse_args_rejects_unknown_launcher_flags(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as ex:
                launcher_cli._parse_args(["codex", "--bad-flag"])
        self.assertEqual(ex.exception.code, 2)
        self.assertIn("Unknown launcher arg(s): --bad-flag", stderr.getvalue())

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

    def test_main_cli_dispatch_supports_launch_subcommand(self):
        cli_module_path = Path(__file__).resolve().parents[1] / "mlx_lm" / "cli.py"
        text = cli_module_path.read_text(encoding="utf-8")
        self.assertIn('"launch"', text)


if __name__ == "__main__":
    unittest.main()
