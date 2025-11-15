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
    if api:
        api.stop()
    sys.exit(exit_code)

# Signal Handler: capture ctrl-C and clean exit
def signal_handler(sig_id, frame):
    shutdown(exit_code=0, sig_id=sig_id)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    # Spin up the server in the background
    app.logger.info(f"Starting {app.name} v{app.version} [{app.license}]")
    proto = "http"
    if app.tls_opts.enabled:
        app.logger.info("TLS is enabled for the server")
        proto = "https"
    reload = True if app.args.log_level in ["debug"] else False
    app.logger.info(f"Log Level: {app.args.log_level}")
    if reload:
        app.logger.debug(f"Reloading on changes.")
    app.logger.debug(f"Base Directory: {app.base_dir}")

    api = FastAPIThreadedServer(
        title = f"{app.name}",
        version = f"{app.version}",
        description = f"{app.description}",
        copywrite = f"{app.copyright}",
        host="0.0.0.0", port=app.args.http_port,
        log_opts=app.log_opts,
        tls_opts=app.tls_opts,
        reload=reload
        )
    api.start()

    
    app.logger.info(f"API Server running – hit {proto}://127.0.0.1:{app.args.http_port}/healthz")
    app.logger.info("Press Ctrl-C to stop the server")
    
    # Do something else while the server lives
    for i in range(35):
        print(f"Main thread doing work… ({i})")
        time.sleep(30)

    # Shut everything down
    api.stop()
    app.logger.info("Server stopped")