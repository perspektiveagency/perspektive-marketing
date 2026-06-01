"""Google provider — photos via Imagen, video via Veo (TODO).

Requires the `google` extra:  pip install 'perspektive-content[google]'
and GOOGLE_API_KEY (or Vertex AI env vars; see .env.example).
"""

from __future__ import annotations

import os

from .base import ContentProvider
from ..models import GeneratedAsset, GenerationRequest, MediaType


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
        # TODO: Veo is a long-running operation. Sketch:
        #   op = client.models.generate_videos(model="veo-3.0-generate-001",
        #                                       prompt=request.prompt, config={...})
        #   while not op.done: time.sleep(10); op = client.operations.get(op)
        #   download op.result.generated_videos[*].video bytes into output_dir
        # See https://ai.google.dev/gemini-api/docs/video for the current surface.
        raise NotImplementedError(
            "Veo video generation skeleton — implement the long-running operation "
            "poll + download here."
        )
