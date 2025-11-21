import os
import threading
import signal
import sys
import json
import logging
import uvicorn
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse
from .apiroutes import router
from typing import Optional, List, Tuple
from .helpers import verify_sha256


class FastAPIThreadedServer():
    """
    Encapsulates a FastAPI app and runs uvicorn in a background thread.
    """

    def __init__(
        self,
        logger_config: Optional[object] = None,
        uvc_config: Optional[object] = None,
        api_config: Optional[object] = None,
        meta: Optional[object] = None,
    ):
        self.uvc_config = uvc_config
        self.api_config = api_config
        self.logger_config = logger_config
        self.meta = meta
        self._logger = logging.getLogger("uvicorn")
        self._logger.info("Initializing FastAPIThreadedServer instance.")

        # ------------------------------------------------------------------
        # Build the FastAPI instance and register routes
        # ------------------------------------------------------------------
        self.app = FastAPI(
            docs_url=None,
            dependencies=[Depends(self.before_handler)],
            **self.api_config.__dict__

        )
        # register static files
        print(f"Mounting static files from: {self.meta.static_dir}")
        self.app.mount("/static", StaticFiles(directory=f"{self.meta.static_dir}"), name="static")
        # register built-in routes
        self._register_builtin_routes()
        # import external routers:
        router.logger_name = self.logger_config.name if self.logger_config and hasattr(self.logger_config, 'name') else __name__
        self.app.include_router(router)

        # Thread control
        self._server_thread: Optional[threading.Thread] = None
        self._should_stop = threading.Event()

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    async def before_handler(self, request: Request):
        # Fetch the route name
        route = request.scope.get("route", None)
        route_name = route.name if route else "unknown"
        self._logger.debug(f"Handling request for route: {route_name}")
        
        # Try reading JSON safely
        if request.method not in ("POST", "PUT", "PATCH"):
            return  route_name # only validate bodies for these methods

        data = {}
        try:
            data = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in request body"
            )

        # Verify SHA256 header if present
        if "x_payload_sha256" in request.headers:
            sha256_header = request.headers["x_payload_sha256"]
            if not verify_sha256(data=json.dumps(data), expected_hash=sha256_header):
                raise HTTPException(
                    status_code=400,
                    detail="SHA256 hash mismatch for request body"
                )

        return route_name
        
    def start(self) -> None:
        """Launch uvicorn in a daemon thread."""
        if self._server_thread and self._server_thread.is_alive():
            raise RuntimeError("Server already running")

        # Build uvicorn config – we pass a custom `lifespan` hook that
        # watches the `_should_stop` event.
        config = uvicorn.Config(
            app=self.app,
            log_config=None, # we set up logging ourselves
            **self.uvc_config.__dict__
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
    # Default methods (routes)
    # ----------------------------------------------------------------------
    def _register_builtin_routes(self) -> None:
        """Add a few default endpoints (health, version, etc.)."""

        @self.app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(os.path.join(self.meta.static_dir, "favicon.ico"), 
            media_type="image/vnd.microsoft.icon")

        @self.app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui():
            return get_swagger_ui_html(
                openapi_url=self.app.openapi_url,
                title=self.app.title + " - Swagger UI",
                swagger_css_url="/static/swagger-dark.css",
                swagger_favicon_url="/static/favicon.ico",
                swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}
            )

        @self.app.get("/ping", name="ping", tags=["health"])
        async def ping():
            return {f"{self.meta.name}": "pong"}

        @self.app.get("/healthz", tags=["health"])
        async def health():
            return {"status": "ok"}

        @self.app.get("/version", tags=["health"])
        async def version():
            return {"name": f"{self.meta.name}", "version": f"{self.meta.version}", "copyright": f"{self.meta.copyright}"}

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