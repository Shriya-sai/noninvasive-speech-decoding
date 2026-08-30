from pathlib import Path

import pandas as pd
import pytest

from japaneeg_audit.pilot import _require_columns


def test_require_columns_accepts_complete_frame() -> None:
    _require_columns(pd.DataFrame({"a": [1], "b": [2]}), {"a", "b"}, "frame")


def test_require_columns_reports_missing_column() -> None:
    with pytest.raises(ValueError, match="frame missing columns: b"):
        _require_columns(pd.DataFrame({"a": [1]}), {"a", "b"}, "frame")


def test_missing_signal_files_fail(tmp_path: Path) -> None:
    from japaneeg_audit.pilot import summarize_run

    with pytest.raises(FileNotFoundError):
        summarize_run(tmp_path / "missing_eeg.edf", tmp_path / "missing.wav")
