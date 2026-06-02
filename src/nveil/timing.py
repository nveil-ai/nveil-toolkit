# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Lightweight timing instrumentation for the NVEIL Toolkit.

Controlled via ``nveil.configure(timing=True)``. When disabled (default),
all operations are no-ops with zero overhead.
"""

import time


class Timer:
    """Tracks named durations as an ordered list of (label, seconds) pairs."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._entries: list[tuple[str, float]] = []

    def measure(self, label: str):
        """Context manager that records the duration of a block.

        Usage::

            with timer.measure("API call"):
                response = client.post(...)
        """
        if not self.enabled:
            return _NOOP
        return _TimerContext(self, label)

    def record(self, label: str, duration: float):
        """Manually record a duration."""
        if self.enabled:
            self._entries.append((label, duration))

    def summary(self) -> str:
        """Return a formatted terminal table of all recorded timings."""
        if not self._entries:
            return ""
        max_label = max(len(label) for label, _ in self._entries)
        total = sum(d for _, d in self._entries)
        width = max_label + 14
        lines = ["", "\u2500" * width]
        for label, dur in self._entries:
            lines.append(f"  {label:<{max_label}}  {dur:>6.2f}s")
        lines.append("\u2500" * width)
        lines.append(f"  {'Total':<{max_label}}  {total:>6.2f}s")
        lines.append("")
        return "\n".join(lines)

    def clear(self):
        """Reset all recorded entries."""
        self._entries.clear()


class _TimerContext:
    __slots__ = ("_timer", "_label", "_t0")

    def __init__(self, timer: Timer, label: str):
        self._timer = timer
        self._label = label

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *_):
        self._timer.record(self._label, time.perf_counter() - self._t0)


class _NoOp:
    """Singleton no-op context manager — zero allocation when timing is off."""
    __slots__ = ()
    def __enter__(self): return self
    def __exit__(self, *_): pass


_NOOP = _NoOp()
