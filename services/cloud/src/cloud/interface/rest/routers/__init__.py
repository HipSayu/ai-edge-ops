"""The index of every router, by version. Add a version here (routers/v2) and include it below."""

from fastapi import APIRouter

from cloud.interface.rest.routers import health
from cloud.interface.rest.routers.v1 import router as v1
from cloud.interface.rest.routers.v1 import routes as v1_routes
from cloud.interface.rest.routers.v1.auth import jwks

router = APIRouter()
router.include_router(health.router, prefix="/api")
router.include_router(jwks)  # /.well-known/jwks.json, outside /api
router.include_router(v1, prefix="/api")  # /api/v1/...
router.include_router(v1_routes, prefix="/api", include_in_schema=False)  # unversioned paths the web app still calls
