import os
import pickle
import queue
import uuid
import threading
import logging

class WorkerQueue(queue.Queue):
    """
    A simple threaded worker queue for processing tasks in the background.
    """
    def __init__(self, state_dir=None, maxsize: int = 0) -> None:
        self.id = str(uuid.uuid4())
        self.state_dir = os.path.join(state_dir, self.id) if state_dir else None
        super().__init__(maxsize=maxsize)

class Worker(threading.Thread):
    """
    A worker that processes tasks from a WorkerQueue.
    """
    def __init__(self, name: str, worker_queue: WorkerQueue, interval: float = 1.0) -> None:
        self.id = str(uuid.uuid4())
        self.queue = worker_queue
        super().__init__(name=name)
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                task = self.queue.get(timeout=self.interval)
                self.process_task(task)
                self.queue.task_done()
            except queue.Empty:
                continue

    
    def stop(self) -> None:
      self._stop_event.set()

    def process_task(self, task) -> None:
        print(f"Worker {self.name} processing task: {task}")

    