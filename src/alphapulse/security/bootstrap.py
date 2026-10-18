"""Local operator bootstrap: PYTHONPATH=src python -m alphapulse.security.bootstrap."""

import getpass
from alphapulse.api.database import SessionLocal
from alphapulse.api.models_user import User
from alphapulse.security.auth import AuthService, create_default_roles, signing_key


def main():
    signing_key()
    username = input("Initial administrator username: ").strip()
    email = input("Administrator email: ").strip()
    password = getpass.getpass("New administrator password (12+ characters): ")
    if not username or "@" not in email or not 12 <= len(password.encode()) <= 72:
        raise ValueError("Username, email and password (12 to 72 bytes) required")
    if password != getpass.getpass("Confirm password: "):
        raise ValueError("Passwords do not match")
    with SessionLocal() as db:
        if db.query(User).filter(User.is_superuser == True).first():
            raise RuntimeError(
                "Administrator already exists; use authenticated user management"
            )
        create_default_roles(db)
        db.add(
            User(
                username=username,
                email=email,
                hashed_password=AuthService(db).get_password_hash(password),
                is_active=True,
                is_superuser=True,
            )
        )
        db.commit()
    print("Administrator created. No credentials have been printed.")


if __name__ == "__main__":
    main()
