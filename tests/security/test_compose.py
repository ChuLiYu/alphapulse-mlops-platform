from pathlib import Path
import unittest
import yaml


class ComposeSafetyTests(unittest.TestCase):
    def test_local_ports_and_no_default_passwords_or_public_bucket(self):
        text = (
            Path(__file__).resolve().parents[2] / "infra" / "docker-compose.yml"
        ).read_text()
        services = yaml.safe_load(text)["services"]
        for service in services.values():
            for port in service.get("ports", []):
                self.assertTrue(port.startswith("127.0.0.1:"), port)
        for secret in (
            "POSTGRES_PASSWORD",
            "MINIO_ROOT_PASSWORD",
            "AIRFLOW_FERNET_KEY",
            "AIRFLOW_PASSWORD",
            "GRAFANA_PASSWORD",
            "SECRET_KEY",
        ):
            self.assertIn("${" + secret + ":?", text)
            self.assertNotIn("${" + secret + ":-", text)
        self.assertNotIn("anonymous set download", text)
