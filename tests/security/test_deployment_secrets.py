"""Exercise the legacy secret generator without Kubernetes or real credentials."""
import base64
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DeploymentSecretTests(unittest.TestCase):
    def test_password_is_stdin_data_and_manifest_private_no_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "infra/scripts"
            scripts.mkdir(parents=True)
            output_dir = root / "infra/k3s/base"
            output_dir.mkdir(parents=True)
            script = scripts / "generate_k3s_secrets.sh"
            shutil.copyfile(ROOT / "infra/scripts/generate_k3s_secrets.sh", script)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            helper = bin_dir / "htpasswd"
            # Stub asserts the exact stdin protocol, and rejects password argv exposure.
            helper.write_text(
                "#!/bin/sh\n"
                '[ "$#" -eq 2 ] && [ "$1" = -niB ] && [ "$2" = admin ] || exit 91\n'
                "IFS= read -r value\n"
                '[ "$value" = "$ADMIN_PASSWORD" ] || exit 92\n'
                "printf 'admin:$2y$test-hash\\n'\n"
            )
            helper.chmod(0o700)
            marker = root / "injected"
            password = "safe'password;$(touch " + str(marker) + ")"
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"], ADMIN_PASSWORD=password)
            first = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertFalse(marker.exists())
            output = output_dir / "admin-credentials-secret.yaml"
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            encoded = output.read_text().split("users: ", 1)[1].splitlines()[0]
            self.assertEqual(base64.b64decode(encoded).decode(), "admin:$2y$test-hash")
            original = output.read_bytes()
            second = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            self.assertNotIn(password, first.stdout + first.stderr)

    @unittest.skipUnless(shutil.which("htpasswd"), "apache2-utils required")
    def test_real_bcrypt_accepts_password_metacharacters_as_data(self):
        password = "test-only'$(not-a-command);abcdef"
        generated = subprocess.run(
            ["htpasswd", "-niB", "admin"], input=password + "\n",
            capture_output=True, text=True, check=True,
        )
        self.assertTrue(generated.stdout.startswith("admin:$2"))
        with tempfile.NamedTemporaryFile(mode="w") as file:
            file.write(generated.stdout)
            file.flush()
            checked = subprocess.run(
                ["htpasswd", "-vi", file.name, "admin"], input=password + "\n",
                capture_output=True, text=True,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_workflow_does_not_interpolate_password_into_remote_code(self):
        workflow = (ROOT / ".github/workflows/deploy-k3s.yml").read_text()
        remote_script = workflow.split("          script: |", 1)[1]
        self.assertNotIn("${{ secrets.", remote_script)
        self.assertNotIn("workflow_run:", workflow)
        self.assertIn("envs: ADMIN_PASSWORD", workflow)


if __name__ == "__main__":
    unittest.main()
