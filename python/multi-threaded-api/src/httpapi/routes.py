from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter


class RouteHandler:
    """ Base class for route handlers. """
    def __init__(self) -> None:
        self.handlers = 0

    def add(self, handlers: dict) -> None:
        """ Add a handler to the collection. """
        for name, handler in handlers.items():
            setattr(self, name, handler)
            self.handlers += 1

    def has(self, name: str) -> bool:
        """ Check if a handler exists by name. """
        return hasattr(self, name)

@asynccontextmanager
async def router_lifespan(app: FastAPI):
    """Lifespan context manager for the router."""
    # Setup code can go here
    print(f"Setting up router lifespan...")
    yield
    # Teardown code can go here
    print("Tearing down router lifespan...")

handler = RouteHandler()
router = APIRouter(lifespan=router_lifespan)

@router.get("/ping")
async def ping():
    """Simple health‑check endpoint."""
    return {"api": "pong"}

@router.get("/poop")
async def poop():
    """Just for fun endpoint."""
    handler.main.queue.put("Sombody pooped!")
    return {"api": "💩"}
    
