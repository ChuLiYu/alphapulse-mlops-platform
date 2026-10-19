"""Smoke checks for the OrbStack local stack using synthetic, disposable data."""

import os
import json
import secrets
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from alphapulse.api.models import Base as MarketBase, Price
from alphapulse.api.models_user import APIKey, AuditLog, RefreshToken, Role, User, UserRole
from alphapulse.security.auth import AuthService

DATABASE_URL = os.environ["DATABASE_URL"]


class LocalStackSmokeTests(unittest.TestCase):
    def test_api_health_and_protected_route(self):
        api_url = os.environ["API_URL"]
        with urlopen(f"{api_url}/health", timeout=10) as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{api_url}/api/v1/prices", timeout=10)
        self.assertEqual(error.exception.code, 401)

    def test_database_can_write_and_read_disposable_row(self):
        self.assertTrue(DATABASE_URL.startswith("postgresql://"), "local stack smoke tests require Compose Postgres")
        engine = create_engine(DATABASE_URL)
        try:
            # This asserts the API bootstrap created its real schema, including
            # auth tables, before the smoke suite ran.
            table_names = set(inspect(engine).get_table_names())
            self.assertTrue({"prices", "users", "roles", "user_roles"}.issubset(table_names))
            with engine.begin() as connection:
                connection.execute(text("CREATE TEMPORARY TABLE orb_smoke (value integer)"))
                connection.execute(text("INSERT INTO orb_smoke VALUES (73)"))
                value = connection.execute(text("SELECT value FROM orb_smoke")).scalar_one()
                self.assertEqual(value, 73)
        finally:
            engine.dispose()

    def test_authenticated_price_round_trip_uses_database_and_decimal(self):
        """Authenticate a disposable DB user, then insert/read a synthetic price."""
        self.assertTrue(DATABASE_URL.startswith("postgresql://"), "local stack smoke tests require Compose Postgres")
        engine = create_engine(DATABASE_URL)
        suffix = secrets.token_hex(8)
        username = f"stack-smoke-{suffix}"
        email = f"{username}@example.invalid"
        password = secrets.token_urlsafe(24)
        symbol = f"SMOKE{suffix[:8].upper()}-USD"
        api_url = os.environ["API_URL"]
        user_id = None
        price_id = None
        try:
            with Session(engine) as db:
                role = Role(
                    name=f"stack-smoke-{suffix}",
                    description="Disposable local integration-test role",
                    permissions=json.dumps(["data:read", "data:write"]),
                )
                user = User(
                    username=username,
                    email=email,
                    hashed_password=AuthService(db).get_password_hash(password),
                    is_active=True,
                    is_superuser=False,
                )
                db.add_all([role, user])
                db.flush()
                user_id = user.id
                db.add(UserRole(user_id=user.id, role_id=role.id))
                db.commit()

            login_payload = json.dumps({"username": username, "password": password}).encode()
            request = Request(
                f"{api_url}/api/v1/auth/login",
                data=login_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=15) as response:
                self.assertEqual(response.status, 200)
                login_tokens = json.loads(response.read())
                token = login_tokens["access_token"]

            refresh_request = Request(
                f"{api_url}/api/v1/auth/refresh",
                data=json.dumps({"refresh_token": login_tokens["refresh_token"]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(refresh_request, timeout=15) as response:
                self.assertEqual(response.status, 200)
                rotated_tokens = json.loads(response.read())
            self.assertTrue(rotated_tokens["access_token"])
            self.assertTrue(rotated_tokens["refresh_token"])

            with self.assertRaises(HTTPError) as replay_error:
                urlopen(refresh_request, timeout=15)
            self.assertEqual(replay_error.exception.code, 401)

            timestamp = datetime.now(timezone.utc).isoformat()
            price_payload = json.dumps({
                "symbol": symbol,
                "price": "123.45678901",
                "volume": "2.50000000",
                "timestamp": timestamp,
            }).encode()
            request = Request(
                f"{api_url}/api/v1/prices",
                data=price_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with urlopen(request, timeout=15) as response:
                self.assertEqual(response.status, 200)
                created = json.loads(response.read())["data"]
                price_id = created["id"]
                self.assertEqual(Decimal(created["price"]), Decimal("123.45678901"))

            request = Request(
                f"{api_url}/api/v1/prices?symbol={symbol}",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urlopen(request, timeout=15) as response:
                rows = json.loads(response.read())["data"]
            stored = next(row for row in rows if row["id"] == price_id)
            self.assertEqual(Decimal(stored["price"]), Decimal("123.45678901"))
            self.assertEqual(Decimal(stored["volume"]), Decimal("2.50000000"))
            self.assertEqual(stored["symbol"], symbol)
        finally:
            with Session(engine) as db:
                if price_id is not None:
                    db.query(Price).filter(Price.id == price_id).delete()
                if user_id is not None:
                    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
                    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
                    db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
                    db.query(APIKey).filter(APIKey.user_id == user_id).delete()
                    db.query(User).filter(User.id == user_id).delete()
                    db.query(Role).filter(Role.name == f"stack-smoke-{suffix}").delete()
                db.commit()
            engine.dispose()

    def test_frontend_serves_built_application(self):
        frontend_url = os.environ["FRONTEND_URL"].rstrip("/")
        with urlopen(frontend_url, timeout=10) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8", errors="replace")
        self.assertIn("<div id=\"root\">", body)

        # Nginx must proxy API requests to the API service and serve the SPA
        # entry point for client-side routes.
        with urlopen(f"{frontend_url}/api/v1/health", timeout=10) as response:
            self.assertEqual(response.status, 200)
            health = json.loads(response.read())
        self.assertEqual(health.get("status"), "healthy")

        with urlopen(f"{frontend_url}/api/v1/health/detailed", timeout=10) as response:
            self.assertEqual(response.status, 200)
            detailed = json.loads(response.read())
        self.assertEqual(detailed.get("overall"), "healthy")
        self.assertEqual(detailed.get("components", {}).get("database"), "healthy")

        with urlopen(f"{frontend_url}/a/client-side/route", timeout=10) as response:
            self.assertEqual(response.status, 200)
            fallback_body = response.read().decode("utf-8", errors="replace")
        self.assertIn("<div id=\"root\">", fallback_body)


if __name__ == "__main__":
    unittest.main()
