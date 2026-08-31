import pytest

from japaneeg_audit.windowing import annotate_speech, construct_windows


def test_windows_use_common_complete_duration() -> None:
    windows = construct_windows(12.0, 15.0, 2.0, window_seconds=5.0)
    assert len(windows) == 2
    assert windows[0].eeg_start == 0.0
    assert windows[0].audio_start == 2.0
    assert windows[-1].audio_end == 12.0


def test_incomplete_final_window_is_dropped() -> None:
    assert len(construct_windows(14.99, 30.0, 0.0)) == 2


def test_speech_intervals_are_unioned_before_occupancy() -> None:
    window = construct_windows(5.0, 5.0, 0.0)[0]
    result = annotate_speech([window], [(0.0, 0.75), (0.5, 1.0)])[0]
    assert result.speech_seconds == pytest.approx(1.0)
    assert result.speech_fraction == pytest.approx(0.2)
    assert result.retained


def test_below_twenty_percent_is_rejected() -> None:
    window = construct_windows(5.0, 5.0, 0.0)[0]
    assert not annotate_speech([window], [(0.0, 0.999)])[0].retained


def test_invalid_threshold_fails() -> None:
    with pytest.raises(ValueError, match="minimum_speech_fraction"):
        annotate_speech([], [], 1.1)
