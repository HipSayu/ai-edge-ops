from fastapi import Depends, Request

from cloud.bootstrap.container import Container
from shared.http import bearer_token
from shared.roles import Role
from shared.viewer import Viewer


def get_container(request: Request) -> Container:
    return request.app.state.container


def current_user(request: Request, container: Container = Depends(get_container)) -> Viewer:
    return container.auth.authenticate(bearer_token(request))


def require_role(minimum: Role):
    def checker(viewer: Viewer = Depends(current_user)) -> Viewer:
        viewer.require_role(minimum)
        return viewer

    return checker
