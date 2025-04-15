from fastapi import FastAPI, Response, status
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .mq import initialize_rabbitmq, shutdown_rabbitmq
from .mq.consumers import *
import asyncio
import logging
from .llm.gemini import Gemini
from .llm.context import ContextManager
from .llm.message import Message
from pydantic import BaseModel
from datetime import datetime

client = Gemini()
ctx = ContextManager()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup tasks here
    await initialize_rabbitmq(asyncio.get_event_loop())
    yield
    # Perform shutdown tasks here
    await shutdown_rabbitmq()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigRequest(BaseModel):
    max_context_length: int
    context_invalidation_time_seconds: int
    system_instruction: str


# Register an inference user with the given key
# If context already exists, it won't change at all
# Users should call this route before making any completions
@app.post("/inference/{key}/config")
def config(key: str, config: ConfigRequest):
    if not key in ctx.context_configs:
        ctx.add_context_config(key, **config.model_dump())
    return {"config": ctx.context_configs[key]}


class CompleteRequest(BaseModel):
    message: str
    metadata: dict


# Get a completion for the given message
# Fails with a 400 if the key isn't registered
@app.post("/inferece/{key}/complete", status_code=status.HTTP_201_CREATED)
async def complete(key: str, message: CompleteRequest, response: Response):
    try:
        prompt = ctx.contextualize_prompt(key, message.message)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": str(e)}

    model_response = await client.prompt_model(
        prompt, ctx.context_configs[key].system_instruction
    )
    ctx.add_message_to_context(
        key,
        Message(
            message=message.message,
            response=model_response,
            timestamp=datetime.now(),
            metadata=message.metadata,
        ),
    )
    return {"response": model_response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
