"""Content-based duplicate input detection (no deletion of source files)."""
import hashlib
from pathlib import Path
from settings import get_bool

def file_digest(path, block_size=1024*1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()

class DuplicateDetector:
    def __init__(self, enabled=None):
        self.enabled = get_bool("Operations", "detect_duplicates", True) if enabled is None else enabled
        self.seen = {}  # (file length, SHA256) -> first path

    def check(self, path):
        if not self.enabled:
            return None
        path = Path(path)
        fingerprint = (path.stat().st_size, file_digest(path))
        existing = self.seen.get(fingerprint)
        if existing is None:
            self.seen[fingerprint] = str(path)
        return existing

def duplicate_groups(paths):
    detector = DuplicateDetector(enabled=True)
    groups = {}
    for path in paths:
        original = detector.check(path)
        if original is not None:
            groups.setdefault(original, []).append(str(path))
    return groups
