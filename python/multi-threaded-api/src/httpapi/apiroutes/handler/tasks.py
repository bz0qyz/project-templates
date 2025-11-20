from time import sleep

class TaskProcessor:
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id

    # Route named methods
    @staticmethod
    def put_task_queue(payload: dict):
        sleep(15.0)
        return {"status": "task completed", "processor": "TaskProcessor"}