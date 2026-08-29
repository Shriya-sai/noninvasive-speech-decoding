"""Dataset inventory helpers that do not load signal arrays."""

from pathlib import Path


def require_bids_metadata(dataset_root: Path) -> tuple[Path, Path]:
    """Return required top-level BIDS metadata paths or raise clearly."""
    description = dataset_root / "dataset_description.json"
    participants = dataset_root / "participants.tsv"
    missing = [path.name for path in (description, participants) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing BIDS metadata: {', '.join(missing)}")
    return description, participants
