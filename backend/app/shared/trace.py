"""
A tiny step recorder. Each pipeline wraps its steps like this:

    trace = Trace()
    with trace.step("chunk") as step:
        chunks = make_chunks(...)
        step["detail"] = f"{len(chunks)} chunks"

The UI shows trace.steps so learners can see what each step did and how long it took.
"""
import time
from contextlib import contextmanager


class Trace:
    def __init__(self) -> None:
        self.steps: list[dict] = []

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
