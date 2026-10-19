"""Create the existing AlphaPulse API schema without creating an administrator.

This is safe to run on every API container start. It only creates missing tables;
it never drops, truncates, or alters existing data.
"""

from alphapulse.api.database import Base as AuthBase
from alphapulse.api.database import DATABASE_URL, engine


def initialize_database() -> None:
    # The historical market models and authentication models currently use
    # separate declarative bases. Import both model sets before creating either.
    from alphapulse.api import models as market_models  # noqa: F401
    from alphapulse.api import models_user  # noqa: F401

    market_models.Base.metadata.create_all(bind=engine)
    AuthBase.metadata.create_all(bind=engine)


if __name__ == "__main__":
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured")
    initialize_database()
