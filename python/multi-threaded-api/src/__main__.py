import os
import sys
import signal
import time
from app import App
from httpapi import FastAPIThreadedServer

# Create a base app object
app = App()
api = None

def shutdown(exit_code: int = 0, error_msg: str = None, sig_id: int = None) -> None:
    if api:
        api.stop()
    sys.exit(exit_code)

# Signal Handler: capture ctrl-C and clean exit
def signal_handler(sig_id, frame):
    shutdown(exit_code=0, sig_id=sig_id)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    # Spin up the server in the background
    
    reload = True if app.args.log_level in ["debug"] else False
    print(f"Log Level: {app.args.log_level}")
    print(f"Reload on changes: {reload}")
    api = FastAPIThreadedServer(
        title = app.name,
        version = f"{app.version}",
        copywrite = f"{app.config.copyright}",
        host="0.0.0.0", port=app.args.http_port,
        log_level=app.args.log_level, reload=reload
        )
    api.start()
    print(f"API Server running – hit http://127.0.0.1:{app.args.http_port}/healthz")
    
    # Do something else while the server lives
    for i in range(35):
        print(f"Main thread doing work… ({i})")
        time.sleep(30)

    # Shut everything down
    api.stop()
    print("Server stopped")