import os
import sys
import signal
import time
from app import App
from httpapi import FastAPI, FastAPIThreadedServer
from worker import Worker, WorkerQueue

# Create a base app object
app = App(num_queues=3)
api = None
queues = ["main"]
queue_workers = {}


def shutdown(exit_code: int = 0, error_msg: str = None, sig_id: int = None) -> None:
    for name, worker in queue_workers.items():
        app.logger.info(f"Stopping queue worker '{worker.name}' with ID '{worker.id}'")
        worker.stop()
        worker.join(timeout=5.0)
        app.logger.info(f"Worker '{worker.name}' stopped")

    if api:
        api.stop()
    sys.exit(exit_code)

# Signal Handler: capture ctrl-C and clean exit
def signal_handler(sig_id, frame):
    shutdown(exit_code=0, sig_id=sig_id)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    # Perform build test and exit
    if app.args.build_test:
        app.logger.info("Build test complete")
        sys.exit(0)

    
    for qname in queues:
        worker_queue = WorkerQueue(state_dir=app.args.data_dir)
        worker = Worker(name=f"{qname}", worker_queue=worker_queue, interval=2.0)
        worker.start()
        queue_workers[qname] = worker
        app.logger.info(f"Started queue worker '{worker.name}' with ID '{worker.id}'")
    
    # Start the FastAPI server in a background thread
    api = FastAPIThreadedServer(
        log_opts = app.log_opts,
        api_opts = app.api_opts,
        uvc_opts = app.uvc_opts,
        meta = app.meta,
        queue_workers = queue_workers,
        )
    api.start()

    app.logger.info(f"API Server running – hit {app.uvc_opts.docs_url}")
    app.logger.info("Press Ctrl-C to stop the server")

    
    
    # Do something else while the server lives
    for i in range(35):
        print(f"Main thread doing work… ({i})")
        time.sleep(30)

    # Shut everything down
    api.stop()
    app.logger.info("Server stopped")