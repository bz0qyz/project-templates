import threading
import signal
import sys
from typing import Optional, List, Tuple

import uvicorn
from fastapi import FastAPI
from .routes import router

from .config import LOGGING_CONFIG
from app.constants import LOG_LEVELS, LOG_FORMATS

class FastAPIThreadedServer:
    """
    Encapsulates a FastAPI app and runs uvicorn in a background thread.
    """

    def __init__(
        self,
        log_opts: Optional[object] = None,
        tls_opts: Optional[object] = None,
        title: str = "API Service",
        version: str = "1.0.0",
        description: str = "API Service Description",
        copywrite: str = "None",
        host: str = "127.0.0.1",
        port: int = 3000,
        *,
        reload: bool = False,
        workers: int = 1,
    ):
        self.title = title
        self.version = version
        self.description = description
        self.copywrite = copywrite
        self.host = host
        self.port = port
        self.reload = reload
        self.tls_opts = tls_opts
        self.log_opts = log_opts
        self.log_config = LOGGING_CONFIG.copy()
        self.workers = workers

        # Configure logging according to log_opts
        for key, config in self.log_config["formatters"].items():
            config["datefmt"] = self.log_opts.date_format
            if key == "json":
                continue  # json formatter is custom class
            config["format"] = LOG_FORMATS[key] if key in LOG_FORMATS else self.log_opts.format
        self.log_config["handlers"]["default"]["formatter"] = self.log_opts.format_key
        self.log_config["loggers"]["uvicorn"]["level"] = self.log_opts.level.upper()
        

        # ------------------------------------------------------------------
        # Build the FastAPI instance – you can customise it before starting.
        # ------------------------------------------------------------------
        # self.app = FastAPI(title=f"{title}")
        self.app =FastAPI(
            title = self.title,
            version = self.version,
            description = self.description,
            reload=self.reload
        )
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
            log_level=self.log_opts.level,
            access_log=self.log_opts.access_log,
            log_config=LOGGING_CONFIG,
            proxy_headers=True,
            reload=self.reload,
            workers=self.workers,
            ssl_keyfile=self.tls_opts.key,
            ssl_certfile=self.tls_opts.cert,
            ssl_ca_certs=self.tls_opts.ca,
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