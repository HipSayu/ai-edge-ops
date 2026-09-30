import asyncio
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_url

from src.cloud.domain.value_objects.model_location import ModelLocation
from src.cloud.domain.value_objects.model_ref import ModelRef


class HuggingFaceModelRepository:
    """ModelRepository backed by a Hugging Face Hub model repo (huggingface.co, a mirror or self-hosted endpoint)."""

    def __init__(self, token: str | None, endpoint: str = "https://huggingface.co") -> None:
        self._endpoint = endpoint
        self._api = HfApi(endpoint=endpoint, token=token or None)

    async def resolve(self, ref: ModelRef) -> ModelLocation:
        info = await asyncio.to_thread(self._api.model_info, ref.repo_id, revision=ref.revision)
        return self._location(ref, info.sha)

    async def upload(self, local_path: Path, ref: ModelRef) -> ModelLocation:
        commit = await asyncio.to_thread(
            self._api.upload_file,
            path_or_fileobj=str(local_path),
            path_in_repo=ref.filename,
            repo_id=ref.repo_id,
            revision=ref.revision,
            repo_type="model",
        )
        return self._location(ref, commit.oid)

    async def ping(self) -> bool:
        try:
            await asyncio.to_thread(self._api.whoami)
            return True
        except Exception:
            return False

    def _location(self, ref: ModelRef, sha: str) -> ModelLocation:
        url = hf_hub_url(ref.repo_id, ref.filename, revision=sha, endpoint=self._endpoint)
        return ModelLocation(ref=ref, url=url, commit_sha=sha)
