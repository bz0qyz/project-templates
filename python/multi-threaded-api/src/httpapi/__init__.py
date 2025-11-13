import threading
import signal
import sys
from typing import Optional, List, Tuple

import uvicorn
from fastapi import FastAPI
from .routes import router

class FastAPIThreadedServer:
    """
    Encapsulates a FastAPI app and runs uvicorn in a background thread.
    """

    def __init__(
        self,
        title: str = "API Service",
        version: str = "1.0.0",
        copywrite: str = "None",
        host: str = "127.0.0.1",
        port: int = 3000,
        *,
        reload: bool = False,
        log_level: str = "info",
        workers: int = 1,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
    ):
        self.title = title
        self.version = version
        self.copywrite = copywrite
        self.host = host
        self.port = port
        self.reload = reload
        self.log_level = log_level
        self.workers = workers
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile

        # ------------------------------------------------------------------
        # Build the FastAPI instance – you can customise it before starting.
        # ------------------------------------------------------------------
        self.app = FastAPI(title=f"{title}")
        self._register_builtin_routes()
        # import external routers:
        self.app.include_router(router)

        # Thread control
        self._server_thread: Optional[threading.Thread] = None
        self._should_stop = threading.Event()

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """Launch uvicorn in a daemon thread."""
        if self._server_thread and self._server_thread.is_alive():
            raise RuntimeError("Server already running")

        # Build uvicorn config – we pass a custom `lifespan` hook that
        # watches the `_should_stop` event.
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level=self.log_level,
            reload=self.reload,
            workers=self.workers,
            ssl_keyfile=self.ssl_keyfile,
            ssl_certfile=self.ssl_certfile,
        )
        self.server = uvicorn.Server(config)

        # Wrap the server.run() call in a thread target.
        def _run():
            # uvicorn.Server.run() blocks until `self.should_exit` becomes True.
            # We forward our own stop flag.
            while not self._should_stop.is_set():
                # `run` returns only when the server shuts down; we invoke it once.
                # The loop exists solely to allow us to break early via the event.
                self.server.run()
                break

        self._server_thread = threading.Thread(target=_run, daemon=True, name="uvicorn-thread")
        self._server_thread.start()

        # Small pause to give uvicorn a chance to bind the socket.
        # In production you’d poll `self.server.started` or similar.
        import time
        time.sleep(0.1)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal uvicorn to shut down and wait for the thread to finish."""
        if not self._server_thread:
            return  # nothing to stop

        # Signal the server to exit.
        self._should_stop.set()
        self.server.should_exit = True   # uvicorn checks this flag

        # Wait for the background thread to terminate.
        self._server_thread.join(timeout=timeout)

        # Reset state so the instance can be started again if desired.
        self._should_stop.clear()
        self._server_thread = None
        self.server = None

    # ----------------------------------------------------------------------
    # Helper methods – feel free to extend or replace them.
    # ----------------------------------------------------------------------
    def _register_builtin_routes(self) -> None:
        """Add a few default endpoints (health, version, etc.)."""

        @self.app.get("/healthz")
        async def health():
            return {"status": "ok"}

        @self.app.get("/version")
        async def version():
            return {"name": f"{self.title}", "version": f"{self.version}", "copyright": f"{self.copywrite}"}

    # ----------------------------------------------------------------------
    # Convenience dunder methods
    # ----------------------------------------------------------------------
    def __enter__(self):
        """Allow usage as a context manager: `with FastAPIThreadedServer() as srv:`"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatic shutdown when leaving the context."""
        self.stop()


# ----------------------------------------------------------------------
# Example usage (run directly with `python -m myservice.service`)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple demo – start the server, wait for Ctrl‑C, then shut down cleanly.
    server = FastAPIThreadedServer(host="0.0.0.0", port=self.port, reload=self.reload)

    def _handle_sigint(signum, frame):
        print("\nReceived interrupt – stopping server…")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)

    print(f"🚀 Starting FastAPI on http://{server.host}:{server.port}")
    server.start()

    # Keep the main thread alive while the server runs in the background.
    # In a real app you could do other work here.
    try:
        while True:
            signal.pause()  # wait for signals (Ctrl‑C)
    except KeyboardInterrupt:
        pass