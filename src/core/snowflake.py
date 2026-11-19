"""雪花 ID（对齐 thirdparty/YitIdHelper 的 yitter SnowWorkerM3 算法）。

 WorkerIdBitLength=5 / SeqBitLength=12；起始纪元 2010-11-04T01:42:54.657Z。
"""

from __future__ import annotations

import threading
import time

EPOCH = 1288834974657
WORKER_ID_BITS = 5
DATACENTER_ID_BITS = 5
SEQUENCE_BITS = 12
MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1
MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1
SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1
WORKER_ID_SHIFT = SEQUENCE_BITS
DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS


class SnowflakeGenerator:
    def __init__(self, worker_id: int = 1, datacenter_id: int = 1) -> None:
        if not 0 <= worker_id <= MAX_WORKER_ID:
            raise ValueError(f"worker_id 须在 0..{MAX_WORKER_ID}")
        if not 0 <= datacenter_id <= MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id 须在 0..{MAX_DATACENTER_ID}")
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self._sequence = 0
        self._last_ts = -1
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            ts = self._current_millis()
            if ts < self._last_ts:
                ts = self._wait_next_millis(self._last_ts)
            if ts == self._last_ts:
                self._sequence = (self._sequence + 1) & SEQUENCE_MASK
                if self._sequence == 0:
                    ts = self._wait_next_millis(ts)
            else:
                self._sequence = 0
            self._last_ts = ts
            return (
                ((ts - EPOCH) << TIMESTAMP_LEFT_SHIFT)
                | (self.datacenter_id << DATACENTER_ID_SHIFT)
                | (self.worker_id << WORKER_ID_SHIFT)
                | self._sequence
            )

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_ts: int) -> int:
        ts = self._current_millis()
        while ts <= last_ts:
            ts = self._current_millis()
        return ts


_default: SnowflakeGenerator | None = None
_default_lock = threading.Lock()


def get_generator(worker_id: int = 1) -> SnowflakeGenerator:
    global _default
    if _default is None:
        with _default_lock:
            if _default is None:
                _default = SnowflakeGenerator(worker_id=worker_id)
    return _default


def next_id(worker_id: int = 1) -> int:
    return get_generator(worker_id).next_id()
