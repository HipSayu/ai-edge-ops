"""Violation events and the numbers over them. Every route applies the viewer's camera scope."""

from dataclasses import asdict

from fastapi import APIRouter, Depends

from cloud.interface.rest.deps import current_user, get_container
from cloud.interface.rest.schemas.responses import (
    CompareOut,
    FrameOut,
    RankItemOut,
    TrendPointOut,
    ViolationSummaryOut,
)
from cloud.bootstrap.container import Container
from shared.viewer import Viewer

router = APIRouter(prefix="/violations", tags=["violations"])
analytics = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=ViolationSummaryOut)
def find(
    since_minutes: int = 60,
    camera_id: int | None = None,
    cluster_id: int | None = None,
    violation_type: str | None = None,
    limit: int = 10,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return asdict(container.violations.find(viewer, since_minutes, camera_id, cluster_id, violation_type, limit))


@router.get("/{event_id}/frame", response_model=FrameOut)
def frame(event_id: int, viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    return container.violations.frame(viewer, event_id)


@analytics.get("/trend", response_model=list[TrendPointOut])
def trend(
    hours: int = 24,
    bucket: str = "hour",
    cluster_id: int | None = None,
    camera_id: int | None = None,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return container.analytics.trend(viewer, hours, bucket, cluster_id, camera_id)


@analytics.get("/rank", response_model=list[RankItemOut])
def rank(
    by: str = "camera",
    since_minutes: int = 60,
    cluster_id: int | None = None,
    limit: int = 5,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return container.analytics.rank(viewer, by, since_minutes, cluster_id, limit)


@analytics.get("/compare", response_model=CompareOut)
def compare(
    window_minutes: int = 60,
    cluster_id: int | None = None,
    viewer: Viewer = Depends(current_user),
    container: Container = Depends(get_container),
):
    return container.violations.compare(viewer, window_minutes, cluster_id)
