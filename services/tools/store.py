from collections import deque
from threading import Lock

WINDOW = 60  # 5s * 60 = 5 min


class MetricsStore:
    def __init__(self):
        self._data: dict[str, deque] = {}
        self._lock = Lock()

    def push(self, host: str, snapshot: dict):
        with self._lock:
            if host not in self._data:
                self._data[host] = deque(maxlen=WINDOW)
            self._data[host].append(snapshot)

    def latest(self, host: str) -> dict | None:
        with self._lock:
            buf = self._data.get(host)
            return buf[-1] if buf else None

    def history(self, host: str) -> list:
        with self._lock:
            return list(self._data.get(host, []))


store = MetricsStore()
