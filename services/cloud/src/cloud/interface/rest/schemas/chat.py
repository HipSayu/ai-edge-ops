from pydantic import BaseModel


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    model: str | None = None  # accepted for the web app's sake; the agent's own model answers
    image_ids: list[str] = []  # pictures uploaded with POST /chat/images, for the assistant to look at


class ChatStartedOut(BaseModel):
    stream_id: str  # read the events at GET /chat/stream/{stream_id}
    session_id: str


class ImageOut(BaseModel):
    image_id: str


class ModelsOut(BaseModel):
    default: str
    models: list[str]


class ApprovalIn(BaseModel):
    approve: bool
