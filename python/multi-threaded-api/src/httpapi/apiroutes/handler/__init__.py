import os
import pickle
import queue
import sqlite3
import json
from uuid import uuid4, UUID
import threading
import logging
from time import sleep
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Any
from .tasks import TaskProcessor

STATUS_PENDING = "pending"
STATUS_READY = "ready"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

class HandlerQueue(queue.Queue):
    """
    A simple threaded worker queue for processing tasks in the background.
    """
    def __init__(self, state_dir=None, maxsize: int = 0) -> None:
        self.id = str(uuid4())
        self.state_dir = os.path.join(state_dir, self.id) if state_dir else None
        super().__init__(maxsize=maxsize)

class ResponseQueue:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._init_table()

    def _init_table(self):
        with self.lock:
            self.conn.execute(f"""
                CREATE TABLE queue (
                    transaction_id TEXT PRIMARY KEY,
                    route TEXT,
                    payload BLOB,
                    status TEXT DEFAULT {STATUS_PENDING}
                )
            """)
            self.conn.commit()

    def qsize(self) -> int:
        with self.lock:
            count = self.conn.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
            return count

    def put(self, transaction_id: UUID, route: str, payload: Any = {}):
        with self.lock:
            if isinstance(payload, (dict, list, tuple)):
                payload = json.dumps(payload)
            self.conn.execute(
                "INSERT INTO queue (transaction_id, route, payload) VALUES (?, ?, ?)",
                (transaction_id, route, payload)
            )
            self.conn.commit()
    
    def update_status(self, transaction_id: UUID, status: str, payload: Any = {}) -> None:
        with self.lock:
            self.conn.execute(
                "UPDATE queue SET payload = ?, status = ? WHERE transaction_id = ?",
                (json.dumps(payload), status, transaction_id)
            )
            self.conn.commit()
    
    def get_task(self, transaction_id: UUID) -> Optional[dict]:
        with self.lock:
            cursor = self.conn.execute(
                "SELECT transaction_id, payload, status FROM queue WHERE transaction_id = ?",
                (transaction_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            if row and "payload" in row.keys():
                try:
                    payload = json.loads(row["payload"])
                    row = dict(row)
                    row["payload"] = payload
                except (json.JSONDecodeError, TypeError):
                    pass
                return dict(row)

    def task_done(self, transaction_id: UUID, purge: bool = False) -> None:
        with self.lock:
            if purge:
                self.conn.execute(
                    "DELETE FROM queue WHERE transaction_id = ?",
                    (transaction_id,)
                )
            else:
                self.conn.execute(
                    "UPDATE queue SET status = ? WHERE transaction_id = ?",
                    (STATUS_COMPLETED, transaction_id)
                )
            self.conn.commit()
    
    def dump(self) -> list[dict]:
        with self.lock:
            cursor = self.conn.execute("SELECT * FROM queue")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

class Handler(threading.Thread):
    """
    A worker that processes tasks from a WorkerQueue.
    """
    def __init__(self, name: str, interval: float = 1.0) -> None:
        self.id = str(uuid4())
        self.iqueue = HandlerQueue()
        self.rqueue = ResponseQueue()
        super().__init__(name=name)
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                task = self.iqueue.get(timeout=self.interval)
                self.process_queue_task(task)
                self.iqueue.task_done()
            except queue.Empty:
                continue

    def stop(self) -> None:
      self._stop_event.set()

    def qsize(self) -> int:
        return self.iqueue.qsize()

    def put_task_queue(self, route_name, payload) -> UUID:
        transaction_id = str(uuid4())
        self.iqueue.put((transaction_id, route_name, payload))
        return transaction_id

    def get_response_queue(self) -> list[dict]:
        return self.rqueue.dump()

    def get_task_status(self, transaction_id: UUID) -> Optional[dict]:
        return self.rqueue.get_task(transaction_id)

    def set_task_done(self, transaction_id: UUID, purge: bool = False) -> None:
        self.rqueue.task_done(transaction_id, purge=purge)

    # Function to handle individual tasks that are not queued
    def process_task(self, payload=None) -> None:
        print(f"Handler {self.name} processing task with payload: {payload}")

    # Function to handle queued tasks
    def process_queue_task(self, task) -> None:
        transaction_id, route, payload = task
        self.rqueue.put(transaction_id, route, payload)

        processor = TaskProcessor(transaction_id=transaction_id)
        if not hasattr(processor, f"{route}"):
            self.rqueue.update_status(transaction_id, payload={"error": f"Unknown route: {route}"}, status=STATUS_FAILED)
            return
        with ProcessPoolExecutor() as executor:
            future = executor.submit(getattr(processor, f"{route}"), payload)
            try:
                result = future.result()
                self.rqueue.update_status(transaction_id, payload=result, status=STATUS_READY)
            except Exception as e:
                self.rqueue.update_status(transaction_id, payload={"error": str(e)}, status=STATUS_FAILED)
                return

