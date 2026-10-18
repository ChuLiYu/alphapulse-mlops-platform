import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from alphapulse.agents.artifacts import save_json
from alphapulse.agents.evaluate import evaluate
from alphapulse.agents.transport import (
    local_endpoint,
    request_json,
    NoRedirect,
    MAX_RESPONSE_BYTES,
)


class SafetyTests(unittest.TestCase):
    def test_endpoint_validation(self):
        for host in ("localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"):
            self.assertTrue(local_endpoint(host).startswith("http://"))
        for host in (
            "https://example.com",
            "http://169.254.169.254",
            "http://localhost.evil",
            "http://user:pw@localhost",
            "http://localhost/path",
            "http://localhost?token=x",
            "http://localhost#x",
            "file:///etc/passwd",
            "http://localhost:99999",
        ):
            with self.subTest(host=host), self.assertRaises(ValueError):
                local_endpoint(host)

    def test_redirects_and_oversized_responses_rejected(self):
        with self.assertRaises(ValueError):
            NoRedirect().redirect_request(
                None, None, 302, None, None, "http://example.com"
            )
        with patch("alphapulse.agents.transport.build_opener") as factory:
            factory.return_value.open.return_value.__enter__.return_value.read.return_value = b"x" * (
                MAX_RESPONSE_BYTES + 1
            )
            with self.assertRaises(ValueError):
                request_json("localhost:11434", "/api/chat", {})
            self.assertEqual(factory.call_args.args[0].proxies, {})

    def test_evidence_does_not_overwrite_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            save_json(path, {"status": "completed"})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                save_json(path, {})
            link = Path(tmp) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                save_json(link, {})
            self.assertEqual(json.loads(path.read_text())["status"], "completed")

    def test_evaluator_keeps_failures_and_requires_fresh_directory(self):
        client = MagicMock(model="test")
        with tempfile.TemporaryDirectory() as tmp, patch(
            "alphapulse.agents.evaluate.run_agent",
            return_value={"status": "incomplete", "error": "timeout"},
        ):
            out = Path(tmp) / "run"
            summary = evaluate(client, out, ["BTCUSDT"], 2, {"model": "test"})
            self.assertEqual(len(summary), 2)
            self.assertTrue(all(r["status"] == "incomplete" for r in summary))
            self.assertTrue((out / "summary.json").exists())
            with self.assertRaises(FileExistsError):
                evaluate(client, out, ["BTCUSDT"], 1, {})
