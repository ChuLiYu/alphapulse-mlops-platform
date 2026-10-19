"""Exercise real FastAPI auth dependencies with an isolated SQLite database."""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-signing-material-32-characters-long"

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch
from fastapi import FastAPI, Depends, Security
from fastapi.testclient import TestClient
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from alphapulse.api.database import Base, get_db
from alphapulse.api.models_user import User, APIKey, RefreshToken, Role, UserRole
from alphapulse.security.auth import (
    AuthService,
    get_current_user_from_api_key,
    get_current_user_from_token,
    require_permission,
    signing_key,
    hash_api_key,
)
from alphapulse.api.routes.auth import router


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(
            username="viewer",
            email="viewer@example.com",
            hashed_password="unused",
            is_active=True,
            is_superuser=False,
        )
        self.db.add(self.user)
        self.db.commit()
        role = Role(name="viewer", permissions='["data:read"]')
        self.db.add(role)
        self.db.flush()
        self.db.add(UserRole(user_id=self.user.id, role_id=role.id))
        self.db.commit()
        self.service = AuthService(self.db)
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: self.db

        @app.get("/protected")
        def protected(user=Depends(get_current_user_from_token)):
            return {"username": user.username}

        @app.get("/admin")
        def admin(user=Depends(require_permission("system:admin"))):
            return {"username": user.username}

        @app.get("/key-protected")
        def key_protected(
            user=Security(get_current_user_from_api_key, scopes=["data:read"])
        ):
            return {"username": user.username}

        from alphapulse.api.routes import prices, signals, indicators, ops

        for data_router in (prices.router, signals.router, indicators.router, ops.router):
            app.include_router(data_router)
        app.include_router(router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def headers(self, token):
        return {"Authorization": "Bearer " + token}

    def test_password_hashing_and_login(self):
        password = "test-password-long-enough"
        self.user.hashed_password = self.service.get_password_hash(password)
        self.db.commit()
        self.assertTrue(
            self.service.verify_password(password, self.user.hashed_password)
        )
        self.assertFalse(
            self.service.verify_password("wrong", self.user.hashed_password)
        )
        response = self.client.post(
            "/auth/login", json={"username": "viewer", "password": password}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(
                "/protected", headers=self.headers(response.json()["access_token"])
            ).status_code,
            200,
        )
        oversized = self.client.post(
            "/auth/login", json={"username": "viewer", "password": "é" * 37}
        )
        self.assertEqual(oversized.status_code, 422)

    def test_jwt_requires_exp_subject_and_type_claims(self):
        key = signing_key()
        incomplete_tokens = (
            jwt.encode({"sub": "viewer", "type": "access"}, key, algorithm="HS256"),
            jwt.encode({"exp": datetime.utcnow() + timedelta(hours=1), "type": "access"}, key, algorithm="HS256"),
            jwt.encode({"sub": "viewer", "exp": datetime.utcnow() + timedelta(hours=1)}, key, algorithm="HS256"),
        )
        for token in incomplete_tokens:
            self.assertIsNone(self.service.verify_token(token))
            self.assertEqual(self.client.get("/protected", headers=self.headers(token)).status_code, 401)

    def test_missing_forged_expired_refresh_and_inactive_rejected(self):
        expired = self.service.create_access_token(
            {"sub": "viewer"}, timedelta(seconds=-1)
        )
        forged = jwt.encode(
            {
                "sub": "viewer",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "type": "access",
            },
            "attacker-key",
            algorithm="HS256",
        )
        refresh = self.service.create_refresh_token({"sub": "viewer"})
        for headers in (
            {},
            self.headers("bad"),
            self.headers(expired),
            self.headers(forged),
            self.headers(refresh),
        ):
            self.assertEqual(
                self.client.get("/protected", headers=headers).status_code, 401
            )
        token = self.service.create_access_token({"sub": "viewer"})
        self.assertEqual(
            self.client.get("/protected", headers=self.headers(token)).status_code, 200
        )
        self.assertEqual(
            self.client.get("/admin", headers=self.headers(token)).status_code, 403
        )
        self.user.is_active = False
        self.db.commit()
        self.assertEqual(
            self.client.get("/protected", headers=self.headers(token)).status_code, 401
        )

    def test_initialization_never_creates_known_admin_or_returns_password(self):
        self.assertEqual(self.client.post("/auth/initialize").status_code, 401)
        self.user.is_superuser = True
        self.db.commit()
        response = self.client.post(
            "/auth/initialize",
            headers=self.headers(self.service.create_access_token({"sub": "viewer"})),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.text)
        self.assertIsNone(self.db.query(User).filter(User.username == "admin").first())

    def test_missing_and_known_signing_secrets_fail_closed(self):
        for value in (
            "",
            "short",
            "your-secret-key-for-development-change-in-production",
        ):
            with patch.dict(os.environ, {"SECRET_KEY": value}), self.assertRaises(
                RuntimeError
            ):
                signing_key()

    def test_api_key_database_stores_digest_and_legacy_keys_fail_closed(self):
        raw = APIKey.generate_key()
        record = APIKey(
            user_id=self.user.id,
            key=hash_api_key(raw),
            name="test",
            scopes="[]",
            is_active=True,
        )
        self.db.add(record)
        self.db.commit()
        self.assertNotEqual(record.key, raw)
        self.assertEqual(self.service.verify_api_key(raw).id, self.user.id)
        self.assertIsNone(self.service.verify_api_key(record.key))
        record.key = raw
        self.db.commit()
        self.assertIsNone(self.service.verify_api_key(raw))
        from alphapulse.security.migrate_api_keys import migrate_legacy_keys

        self.assertEqual(migrate_legacy_keys(self.db), 1)
        self.assertEqual(migrate_legacy_keys(self.db), 0)
        self.assertEqual(self.service.verify_api_key(raw).id, self.user.id)
        self.assertEqual(
            self.client.get("/key-protected", params={"api_key": raw}).status_code, 401
        )
        self.assertEqual(
            self.client.get("/key-protected", headers={"X-API-Key": raw}).status_code,
            401,
        )
        record.scopes = '["data:read"]'
        self.db.commit()
        self.assertEqual(
            self.client.get("/key-protected", headers={"X-API-Key": raw}).status_code,
            200,
        )

    def test_data_routes_and_api_key_scopes_enforce_owner_permissions(self):
        headers = self.headers(self.service.create_access_token({"sub": "viewer"}))
        for path in ("/prices", "/signals", "/indicators"):
            self.assertEqual(self.client.post(path, json={}).status_code, 401)
            self.assertEqual(
                self.client.post(path, json={}, headers=headers).status_code, 403
            )
            self.assertEqual(self.client.get(path).status_code, 401)
        for scope in ("system:admin", "trading:execute"):
            self.assertEqual(
                self.client.post(
                    "/auth/api-keys",
                    headers=headers,
                    json={"name": "escalation", "scopes": [scope]},
                ).status_code,
                403,
            )
        raw = APIKey.generate_key()
        self.db.add(
            APIKey(
                user_id=self.user.id,
                key=hash_api_key(raw),
                name="revoked-role",
                scopes='["data:read"]',
                is_active=True,
            )
        )
        self.db.commit()
        self.assertIsNotNone(self.service.verify_api_key(raw, ["data:read"]))
        self.db.query(UserRole).delete()
        self.db.commit()
        self.assertIsNone(self.service.verify_api_key(raw, ["data:read"]))

    def test_ops_routes_require_access_token(self):
        for path in (
            "/ops/pipeline-status",
            "/ops/models",
            "/ops/drift-analysis",
        ):
            self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(
                self.client.get(
                    path,
                    headers=self.headers(
                        self.service.create_access_token({"sub": "viewer"})
                    ),
                ).status_code,
                200,
            )

    def test_refresh_token_requires_json_body(self):
        token = self.service.create_refresh_token({"sub": "viewer"})
        self.assertEqual(
            self.client.post(
                "/auth/refresh", params={"refresh_token": token}
            ).status_code,
            422,
        )
        first = self.client.post("/auth/refresh", json={"refresh_token": token})
        self.assertEqual(first.status_code, 200)
        rotated = first.json()["refresh_token"]
        replay = self.client.post("/auth/refresh", json={"refresh_token": token})
        self.assertEqual(replay.status_code, 401)
        self.assertEqual(
            self.client.post("/auth/refresh", json={"refresh_token": rotated}).status_code,
            200,
        )

    def test_refresh_jti_is_only_stored_as_digest_and_consume_is_single_use(self):
        token = self.service.create_refresh_token({"sub": "viewer"})
        payload = self.service.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertTrue(self.service.consume_refresh_token(payload, self.user))
        self.assertFalse(self.service.consume_refresh_token(payload, self.user))
        stored = self.db.query(RefreshToken).one()
        self.assertEqual(len(stored.jti_digest), 64)
        self.assertNotEqual(stored.jti_digest, payload["jti"])
