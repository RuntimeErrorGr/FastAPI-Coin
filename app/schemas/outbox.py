from typing import Any

from pydantic import BaseModel, ConfigDict


class OutboxEventRead(BaseModel):
    """An event waiting to be published."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    payload: dict[str, Any]
