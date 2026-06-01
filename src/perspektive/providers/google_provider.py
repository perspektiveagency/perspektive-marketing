"""Google provider — photos via Imagen, video via Veo (TODO).

Requires the `google` extra:  pip install 'perspektive-content[google]'
and GOOGLE_API_KEY (or Vertex AI env vars; see .env.example).
"""

from __future__ import annotations

import os
import time

from .base import ContentProvider
from ..logging import get_logger
from ..models import GeneratedAsset, GenerationRequest, MediaType

log = get_logger(__name__)

# How long to wait between polls of a Veo long-running operation.
_VIDEO_POLL_SECONDS = 10


class GoogleProvider(ContentProvider):
    name = "google"
    media_types = {MediaType.photo, MediaType.video}

    def _client(self):
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai not installed. Run: pip install 'perspektive-content[google]'"
            ) from exc
        # google-genai picks up GOOGLE_API_KEY or the Vertex AI env vars automatically.
        if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_PROJECT")):
            raise RuntimeError("Set GOOGLE_API_KEY (or the Vertex AI env vars).")
        return genai.Client()

    def generate(self, request: GenerationRequest) -> list[GeneratedAsset]:
        if request.deliverable.type is MediaType.photo:
            return self._generate_photo(request)
        return self._generate_video(request)

    def _generate_photo(self, request: GenerationRequest) -> list[GeneratedAsset]:
        client = self._client()
        d = request.deliverable
        aspect = d.aspect_ratio or request.brand.default_aspect_ratio
        result = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=request.prompt,
            config={"number_of_images": d.count, "aspect_ratio": aspect},
        )
        assets: list[GeneratedAsset] = []
        for i, generated in enumerate(result.generated_images, start=1):
            path = request.output_dir / f"{d.id}-{i:02d}.png"
            path.write_bytes(generated.image.image_bytes)
            assets.append(
                GeneratedAsset(
                    deliverable_id=d.id,
                    media_type=MediaType.photo,
                    provider=self.name,
                    path=path,
                    prompt=request.prompt,
                    metadata={"model": "imagen-4.0-generate-001", "aspect_ratio": aspect},
                )
            )
        return assets

    def _generate_video(self, request: GenerationRequest) -> list[GeneratedAsset]:
        client = self._client()
        d = request.deliverable
        aspect = d.aspect_ratio or request.brand.default_aspect_ratio

        config: dict = {"aspect_ratio": aspect}
        if d.duration_seconds:
            config["duration_seconds"] = d.duration_seconds

        # Veo generation is a long-running operation: start it, then poll.
        operation = client.models.generate_videos(
            model="veo-3.0-generate-001",
            prompt=request.prompt,
            config=config,
        )
        while not operation.done:
            log.info("Waiting for Veo video '%s'...", d.id)
            time.sleep(_VIDEO_POLL_SECONDS)
            operation = client.operations.get(operation)

        assets: list[GeneratedAsset] = []
        for i, generated in enumerate(operation.response.generated_videos, start=1):
            path = request.output_dir / f"{d.id}-{i:02d}.mp4"
            # Download the file bytes from the API, then save to disk.
            client.files.download(file=generated.video)
            generated.video.save(str(path))
            assets.append(
                GeneratedAsset(
                    deliverable_id=d.id,
                    media_type=MediaType.video,
                    provider=self.name,
                    path=path,
                    prompt=request.prompt,
                    metadata={
                        "model": "veo-3.0-generate-001",
                        "aspect_ratio": aspect,
                        "duration_seconds": d.duration_seconds,
                    },
                )
            )
        return assets
