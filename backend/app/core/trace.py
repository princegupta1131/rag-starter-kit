"""
Records each pipeline step (name, detail, time) so the API can return it and the UI can show it.

    trace = Trace()
    with trace.step("chunk") as step:
        chunks = make_chunks(...)
        step["detail"] = f"{len(chunks)} chunks"
"""
import time
from contextlib import contextmanager

from pydantic import BaseModel


class TraceStep(BaseModel):
    step: str
    detail: str = ""
    ms: int = 0
    ok: bool = True


class Trace:
    def __init__(self) -> None:
        self.steps: list[dict] = []
        self._started = time.perf_counter()

    @property
    def total_ms(self) -> int:
        return round((time.perf_counter() - self._started) * 1000)

    @contextmanager
    def step(self, name: str):
        record = {"step": name, "detail": "", "ms": 0, "ok": True}
        started = time.perf_counter()
        try:
            yield record
        except Exception as e:
            record["ok"] = False
            record["detail"] = record["detail"] or f"{type(e).__name__}: {e}"
            raise
        finally:
            record["ms"] = round((time.perf_counter() - started) * 1000)
            self.steps.append(record)
