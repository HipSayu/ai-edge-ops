from fastapi import APIRouter, Depends, Request

from cloud.interface.rest.deps import current_user, get_container
from cloud.interface.rest.schemas.auth import LoginIn
from cloud.interface.rest.schemas.responses import LoginOut, UserOut, user_out
from cloud.bootstrap.container import Container
from shared.viewer import Viewer

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, container: Container = Depends(get_container)):
    result = container.auth.login(body.username, body.password)
    return {"access_token": result.token, "user": user_out(result.user)}


@router.get("/me", response_model=UserOut)
def me(viewer: Viewer = Depends(current_user), container: Container = Depends(get_container)):
    return user_out(container.auth.profile(viewer))


jwks = APIRouter(tags=["auth"])


@jwks.get("/.well-known/jwks.json")
def public_keys(request: Request):
    """The public key the other services verify tokens with."""
    return request.app.state.container.tokens.jwks()
