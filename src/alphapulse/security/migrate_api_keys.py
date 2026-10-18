"""One-time offline legacy key migration. Back up the DB before running."""

from alphapulse.api.database import SessionLocal
from alphapulse.api.models_user import APIKey
from alphapulse.security.auth import hash_api_key


def migrate_legacy_keys(db):
    count = 0
    for record in db.query(APIKey).all():
        # Legacy generator produced exactly 32 ASCII alphanumeric characters.
        if len(record.key) == 32 and record.key.isascii() and record.key.isalnum():
            record.key = hash_api_key(record.key)
            count += 1
    db.commit()
    return count


def main():
    with SessionLocal() as db:
        count = migrate_legacy_keys(db)
    print(f"Migrated {count} legacy API keys. Rotate keys if the database was exposed.")


if __name__ == "__main__":
    main()
