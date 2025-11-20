import os
import sys
import signal
import time
from app import App
from httpapi import FastAPI, FastAPIThreadedServer

# Create a base app object
app = App()
api = None


def shutdown(exit_code: int = 0, error_msg: str = None, sig_id: int = None) -> None:
    """ Cleanly shutdown the application """
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

    
    # Start the FastAPI server in a background thread
    api = FastAPIThreadedServer(
        logger_config = app.logger_config,
        api_config = app.api_config,
        uvc_config = app.uvc_config,
        meta = app.meta,
        )
    api.start()

    app.logger.info(f"API Server running – hit {app.uvc_config.docs_url}")
    app.logger.info("Press Ctrl-C to stop the server")

    # Keep the main thread alive while the server is running
    while True:
        time.sleep(30)

    # Shut everything down
    api.stop()
    app.logger.info("Server stopped")