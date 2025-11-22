import os
import sys
import signal
import time
from app import App

# Create a base app object
app = App()


def shutdown(exit_code: int = 0, error_msg: str = None, sig_id: int = None) -> None:
    """ Cleanly shutdown the application """
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

    
    # Start the application here
    app.logger.info("Press Ctrl-C to stop the server")

    # Keep the main thread alive while the server is running
    while True:
        time.sleep(30)

    # Shut everything down
    api.stop()
    app.logger.info("Server stopped")