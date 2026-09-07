"""Camera API schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=512)
    zone: str = Field(default="default", max_length=128)
    device_id: int | None = None
    enabled: bool = True
    metadata_json: dict = Field(default_factory=dict)


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    source: str | None = Field(default=None, min_length=1, max_length=512)
    zone: str | None = Field(default=None, max_length=128)
    device_id: int | None = None
    enabled: bool | None = None
    metadata_json: dict | None = None


class CameraOut(CameraCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime


class CameraGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    site: str = Field(default="default", max_length=128)
    camera_ids: list[int] = Field(default_factory=list)


class CameraGroupOut(CameraGroupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    camera_id: int | None
    image_path: str
    captured_at: str
    labels: list
