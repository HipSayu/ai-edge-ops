"""Version 1 of the REST API: every v1 router, declared one by one.

`routes` is the set of v1 endpoints without a prefix; `router` is the same set under /v1.
"""

from fastapi import APIRouter

from cloud.interface.rest.routers.v1.admin import clusters, nodes, users
from cloud.interface.rest.routers.v1.auth import router as auth
from cloud.interface.rest.routers.v1.cameras import router as cameras
from cloud.interface.rest.routers.v1.chat import router as chat
from cloud.interface.rest.routers.v1.detect import router as detect
from cloud.interface.rest.routers.v1.monitoring import router as monitoring
from cloud.interface.rest.routers.v1.reports import router as reports
from cloud.interface.rest.routers.v1.violations import analytics
from cloud.interface.rest.routers.v1.violations import router as violations

routes = APIRouter()
routes.include_router(auth)
routes.include_router(users)
routes.include_router(clusters)
routes.include_router(nodes)
routes.include_router(cameras)
routes.include_router(monitoring)
routes.include_router(violations)
routes.include_router(analytics)
routes.include_router(detect)
routes.include_router(chat)
routes.include_router(reports)

router = APIRouter(prefix="/v1")
router.include_router(routes)
