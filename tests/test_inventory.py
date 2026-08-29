from pathlib import Path

import pytest

from japaneeg_audit.inventory import require_bids_metadata


def test_required_metadata(tmp_path: Path) -> None:
    (tmp_path / "dataset_description.json").write_text("{}")
    (tmp_path / "participants.tsv").write_text("participant_id\nsub-01\n")
    description, participants = require_bids_metadata(tmp_path)
    assert description.name == "dataset_description.json"
    assert participants.name == "participants.tsv"


def test_missing_metadata_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="dataset_description.json"):
        require_bids_metadata(tmp_path)
