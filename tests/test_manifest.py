import pytest

from japaneeg_audit.manifest import manifest_rows, parse_bids_run
from japaneeg_audit.windowing import AlignedWindow


RUN = "sub-01_ses-20230905_task-speechopen_acq-pangolin_run-02"


def test_parse_bids_run() -> None:
    entities = parse_bids_run(RUN)
    assert entities["sub"] == "01"
    assert entities["ses"] == "20230905"
    assert entities["task"] == "speechopen"


def test_missing_bids_entity_fails() -> None:
    with pytest.raises(ValueError, match="missing entities"):
        parse_bids_run("sub-01_task-speechopen")


def test_manifest_preserves_provenance_and_samples() -> None:
    window = AlignedWindow(
        index=3,
        eeg_start=15.0,
        eeg_end=20.0,
        audio_start=43.5,
        audio_end=48.5,
        speech_seconds=2.0,
        speech_fraction=0.4,
        retained=True,
    )
    row = manifest_rows(RUN, [window], "ds007808", "1.0.0", "abc")[0]
    assert row["window_id"] == f"{RUN}_window-00003"
    assert row["participant"] == "sub-01"
    assert row["session"] == "ses-20230905"
    assert row["preprocessed_samples"] == 1200
    assert row["retained"] is True
    assert row["rejection_reason"] == ""


def test_rejected_window_has_reason() -> None:
    window = AlignedWindow(0, 0, 5, 28, 33, 0.5, 0.1, False)
    row = manifest_rows(RUN, [window], "ds", "1", "abc")[0]
    assert row["rejection_reason"] == "speech_fraction_below_0.20"
