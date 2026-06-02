# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for nveil.timing — Timer context manager and no-op mode.

Pure logic, no mocks, no I/O.
"""

import time
import pytest
from nveil.timing import Timer, _NOOP


class TestTimerDisabled:
    def test_measure_returns_noop(self):
        timer = Timer(enabled=False)
        ctx = timer.measure("label")
        assert ctx is _NOOP

    def test_record_does_nothing(self):
        timer = Timer(enabled=False)
        timer.record("label", 1.0)
        assert timer.summary() == ""

    def test_noop_context_manager(self):
        with _NOOP:
            pass  # should not raise


class TestTimerEnabled:
    def test_measure_records_duration(self):
        timer = Timer(enabled=True)
        with timer.measure("sleep"):
            time.sleep(0.01)
        assert len(timer._entries) == 1
        label, dur = timer._entries[0]
        assert label == "sleep"
        assert dur >= 0.005  # at least some measurable time

    def test_record_manual(self):
        timer = Timer(enabled=True)
        timer.record("step1", 0.5)
        timer.record("step2", 1.5)
        assert len(timer._entries) == 2

    def test_summary_format(self):
        timer = Timer(enabled=True)
        timer.record("API call", 0.42)
        timer.record("Render", 0.18)
        s = timer.summary()
        assert "API call" in s
        assert "Render" in s
        assert "Total" in s
        assert "0.60" in s  # total

    def test_summary_empty(self):
        timer = Timer(enabled=True)
        assert timer.summary() == ""

    def test_clear(self):
        timer = Timer(enabled=True)
        timer.record("x", 1.0)
        timer.clear()
        assert timer._entries == []
        assert timer.summary() == ""

    def test_multiple_measures(self):
        timer = Timer(enabled=True)
        with timer.measure("a"):
            pass
        with timer.measure("b"):
            pass
        assert len(timer._entries) == 2
        assert timer._entries[0][0] == "a"
        assert timer._entries[1][0] == "b"
