import os
import pickle
import queue
import threading
import uuid

class WorkerQueue:
    """
    A simple threaded worker queue for processing tasks in the background.
    """
    def __init__(self, state_dir=None):
        self.id = str(uuid.uuid4())
        self.state_dir = os.path.join(state_dir, self.id) if state_dir else None
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()