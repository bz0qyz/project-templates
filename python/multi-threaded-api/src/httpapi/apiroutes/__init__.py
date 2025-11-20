import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Depends, Request, Response, HTTPException, Header, middleware
from .handler import Handler, STATUS_PENDING, STATUS_READY, STATUS_FAILED, STATUS_COMPLETED

logger = None
handler = Handler(name="route-handler", interval=1.0)

@asynccontextmanager
async def router_lifespan(app: FastAPI):
    """Lifespan context manager for the router."""
    # create and start the handler
    logger = logging.getLogger(router.logger_name if hasattr(router, 'logger_name') else __name__)
    logger.debug(f"Initializing the API router.")
    
    handler.start()
    logger.info(f"Started queue handler '{handler.name}' with ID '{handler.id}'")

    yield
    # Shut down the handler
    logger.debug(f"Closing down the router and stopping the '{handler.name}' handler with ID '{handler.id}'.")
    handler.stop()
    handler.join(timeout=5.0)
    logger.debug(f"Handler '{handler.name}' stopped")


router = APIRouter(lifespan=router_lifespan)

@router.get("/poop", name="poop", tags=["fun"])
async def poop(request: Request):
    """Just for fun endpoint."""
    return {"message": "💩"}

@router.put("/task/queue", name="put_task_queue", tags=["tasks"])
async def enqueue_task(request: Request):
    """
    Enqueue a task to be processed by the handler.
    Returns a transaction ID for tracking. and a 202 Accepted status.
    
    """
    payload = await request.json()
    transaction_id = handler.put_task_queue(route_name=request.scope['route'].name, payload=payload)
    return Response(
        status_code=202, 
        content=json.dumps({"transaction_id": transaction_id}),
        media_type="application/json"
    )


@router.get("/task/queue/all", name="get_task_queue_all", tags=["tasks"])
async def task_queue_all(request: Request):
    """Get all tasks in the response queue."""
    tasks = handler.get_response_queue()
    return {"tasks": tasks}

@router.get("/task/queue/{transaction_id}", name="get_task_queue_task", tags=["tasks"])
async def task_queue_status(transaction_id: str, request: Request):
    """Get the status of a specific task in the response queue."""
    task = handler.get_task_status(transaction_id=transaction_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if "status" in task and task["status"] == STATUS_PENDING:
        raise HTTPException(status_code=202, detail=f"transaction_id: {transaction_id} is {task['status']}")

    if "status" in task and task["status"] == STATUS_READY:
        handler.set_task_done(transaction_id=transaction_id)
    
    return task


    