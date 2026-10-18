"""Explicit, private evidence files; publish complete files without replacement."""

import json
import os
from pathlib import Path
import tempfile


def save_json(path, value):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".agent-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        # Atomic create-if-absent; unlike replace(), cannot overwrite a symlink/file.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
