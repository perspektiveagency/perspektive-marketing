"""OpenAI provider — photos via `gpt-image-1`, video via Sora (TODO).

Requires the `openai` extra:  pip install 'perspektive-content[openai]'
and the OPENAI_API_KEY environment variable.
"""

from __future__ import annotations

import base64
import os

from ..models import GeneratedAsset, GenerationRequest, MediaType
from .base import ContentProvider

_DEFAULT_PHOTO_MODEL = "gpt-image-1"

_ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "4:5": "1024x1536",
}


class OpenAIProvider(ContentProvider):
    name = "openai"
    media_types = {MediaType.photo, MediaType.video}

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai not installed. Run: pip install 'perspektive-content[openai]'"
            ) from exc
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return OpenAI(api_key=api_key)

    def generate(self, request: GenerationRequest) -> list[GeneratedAsset]:
        if request.deliverable.type is MediaType.photo:
            return self._generate_photo(request)
        return self._generate_video(request)

    def _generate_photo(self, request: GenerationRequest) -> list[GeneratedAsset]:
        client = self._client()
        d = request.deliverable
        aspect = d.aspect_ratio or request.brand.default_aspect_ratio
        model = request.model or _DEFAULT_PHOTO_MODEL
        result = client.images.generate(
            model=model,
            prompt=request.prompt,
            size=_ASPECT_TO_SIZE.get(aspect, "1024x1024"),
            n=d.count,
        )
        assets: list[GeneratedAsset] = []
        for i, item in enumerate(result.data, start=1):
            path = request.output_dir / f"{d.id}-{i:02d}.png"
            path.write_bytes(base64.b64decode(item.b64_json))
            assets.append(
                GeneratedAsset(
                    deliverable_id=d.id,
                    media_type=MediaType.photo,
                    provider=self.name,
                    path=path,
                    prompt=request.prompt,
                    metadata={"model": model, "aspect_ratio": aspect},
                )
            )
        return assets

    def _generate_video(self, request: GenerationRequest) -> list[GeneratedAsset]:
        # TODO: Wire up OpenAI Sora video generation once enabled for your account.
        # Typical shape: create a video job, poll for completion, download the bytes.
        raise NotImplementedError(
            "OpenAI video (Sora) is not wired up yet. Use provider 'google' or "
            "'runway' for video, or implement _generate_video here."
        )
