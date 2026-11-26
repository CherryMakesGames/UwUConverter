"""Content-based duplicate input detection optimized for large selections."""
import hashlib
from pathlib import Path

from settings import get_bool


def file_digest(path, block_size=4 * 1024 * 1024):
    """Return SHA-256 using the fastest stdlib path available."""
    with Path(path).open("rb") as file:
        if hasattr(hashlib, "file_digest"):
            return hashlib.file_digest(file, "sha256").hexdigest()

        digest = hashlib.sha256()
        for block in iter(lambda: file.read(block_size), b""):
            digest.update(block)
        return digest.hexdigest()


class DuplicateDetector:
    """Detect exact duplicates without hashing files whose sizes are unique."""

    def __init__(self, enabled=None):
        self.enabled = (
            get_bool("Operations", "detect_duplicates", True)
            if enabled is None
            else enabled
        )
        self.by_size = {}

    def check(self, path):
        if not self.enabled:
            return None

        path = Path(path)
        size = path.stat().st_size
        candidates = self.by_size.setdefault(size, [])

        # Most real selections have different file sizes. Do not read the
        # contents at all until there is an actual size collision.
        if not candidates:
            candidates.append({"path": str(path), "digest": None})
            return None

        digest = file_digest(path)

        for candidate in candidates:
            if candidate["digest"] is None:
                candidate["digest"] = file_digest(candidate["path"])

            if candidate["digest"] == digest:
                return candidate["path"]

        candidates.append({"path": str(path), "digest": digest})
        return None


def duplicate_groups(paths):
    detector = DuplicateDetector(enabled=True)
    groups = {}

    for path in paths:
        original = detector.check(path)
        if original is not None:
            groups.setdefault(original, []).append(str(path))

    return groups
