"""Validate secret isolation and persistence without a running desktop."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("init_runtime", Path(__file__).parents[1] / "init-runtime.py")
module = importlib.util.module_from_spec(spec)
# Read source directly so a same-size negative mutation cannot reuse stale .pyc.
exec(compile(Path(spec.origin).read_text(), spec.origin, "exec"), module.__dict__)


class InitTests(unittest.TestCase):
    def test_persistence_override_and_secret_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            saved = Path(directory) / "saved"
            first = module.password("RUSTDESK_PASSWORD", saved)
            self.assertEqual(module.password("RUSTDESK_PASSWORD", saved), first)
            self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
            source = Path(directory) / "input"
            source.write_text("new-secret-from-file\n")
            os.environ["RUSTDESK_PASSWORD_FILE"] = str(source)
            self.assertEqual(module.password("RUSTDESK_PASSWORD", saved), "new-secret-from-file")

    def test_flags_and_bad_passwords(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            self.assertTrue(module.enabled("ENABLE_RUSTDESK", "true"))
            os.environ["ENABLE_RUSTDESK"] = "false"
            self.assertFalse(module.enabled("ENABLE_RUSTDESK", "true"))
            os.environ["ENABLE_RUSTDESK"] = "typo"
            with self.assertRaises(ValueError):
                module.enabled("ENABLE_RUSTDESK", "true")
            for value in ("", "short", "invalid\npassword"):
                os.environ["VNC_PASSWORD"] = value
                with self.assertRaises(ValueError):
                    module.password("VNC_PASSWORD", Path(directory) / "vnc")

    def test_disabled_rustdesk_creates_no_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {"CONFIG_DIR": directory + "/config", "RUNTIME_DIR": directory + "/runtime", "ENABLE_RUSTDESK": "false"}
            with patch.dict(os.environ, env, clear=True), patch.object(module.subprocess, "run"):
                module.main()
            self.assertFalse((Path(directory) / "config/rustdesk").exists())


if __name__ == "__main__":
    unittest.main()
