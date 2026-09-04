"""Base Pydantic schema classes."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class ORMSchema(BaseModel):
    """Read model serialised from an ORM instance."""

    model_config = ConfigDict(from_attributes=True)


class TimestampFields(BaseModel):
    created_at: dt.datetime
    updated_at: dt.datetime
