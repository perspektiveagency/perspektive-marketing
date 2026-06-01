"""Google provider — photos via Imagen, video via Veo (TODO).

Requires the `google` extra:  pip install 'perspektive-content[google]'
and GOOGLE_API_KEY (or Vertex AI env vars; see .env.example).
"""

from __future__ import annotations

import os
import time

from ..logging import get_logger
from ..models import GeneratedAsset, GenerationRequest, MediaType
from .base import ContentProvider

log = get_logger(__name__)

# How long to wait between polls of a Veo long-running operation.
_VIDEO_POLL_SECONDS = 10

# Provider defaults, used when neither the deliverable nor pipeline.yaml sets a model.
_DEFAULT_PHOTO_MODEL = "imagen-4.0-generate-001"
_DEFAULT_VIDEO_MODEL = "veo-3.0-generate-001"
# Used for photos that supply a reference image (image-to-image / editing).
_DEFAULT_EDIT_MODEL = "gemini-2.5-flash-image"


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
        # A reference image means image-to-image / editing — keep the real
        # product and compose a new scene around it.
        if request.image_path is not None:
            return self._edit_photo(request)
        return self._generate_photo_text(request)

    def _generate_photo_text(self, request: GenerationRequest) -> list[GeneratedAsset]:
        client = self._client()
        d = request.deliverable
        aspect = d.aspect_ratio or request.brand.default_aspect_ratio
        model = request.model or _DEFAULT_PHOTO_MODEL
        result = client.models.generate_images(
            model=model,
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
                    metadata={"model": model, "aspect_ratio": aspect},
                )
            )
        return assets

    def _edit_photo(self, request: GenerationRequest) -> list[GeneratedAsset]:
        """Reference-image generation: feed the input image + prompt to the
        Gemini image model and keep the real product in a new scene."""
        client = self._client()
        d = request.deliverable
        model = request.model or _DEFAULT_EDIT_MODEL
        image_part = self._image_part(request.image_path)

        assets: list[GeneratedAsset] = []
        for i in range(1, d.count + 1):
            response = client.models.generate_content(
                model=model,
                contents=[request.prompt, image_part],
            )
            path = request.output_dir / f"{d.id}-{i:02d}.png"
            image_bytes = self._first_image_bytes(response)
            if image_bytes is None:
                raise RuntimeError(
                    f"Model '{model}' returned no image for deliverable '{d.id}'."
                )
            path.write_bytes(image_bytes)
            assets.append(
                GeneratedAsset(
                    deliverable_id=d.id,
                    media_type=MediaType.photo,
                    provider=self.name,
                    path=path,
                    prompt=request.prompt,
                    metadata={"model": model, "source_image": str(request.image_path)},
                )
            )
        return assets

    @staticmethod
    def _image_part(path):
        from google.genai import types

        if not path.exists():
            raise RuntimeError(
                f"Input image not found: {path}. Place the image there or fix the "
                f"deliverable's `image:` path."
            )
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime)

    @staticmethod
    def _first_image_bytes(response):
        """Pull the first inline image out of a Gemini generate_content response."""
        for candidate in getattr(response, "candidates", None) or []:
            for part in getattr(candidate.content, "parts", None) or []:
                inline = getattr(part, "inline_data", None)
                if inline is not None and getattr(inline, "data", None):
                    return inline.data
        return None

    def _generate_video(self, request: GenerationRequest) -> list[GeneratedAsset]:
        client = self._client()
        d = request.deliverable
        aspect = d.aspect_ratio or request.brand.default_aspect_ratio
        model = request.model or _DEFAULT_VIDEO_MODEL

        config: dict = {"aspect_ratio": aspect}
        if d.duration_seconds:
            config["duration_seconds"] = d.duration_seconds

        # Optional starting frame: turns text-to-video into image-to-video.
        generate_kwargs: dict = {"model": model, "prompt": request.prompt, "config": config}
        if request.image_path is not None:
            generate_kwargs["image"] = self._load_image(request.image_path)

        # Veo generation is a long-running operation: start it, then poll.
        operation = client.models.generate_videos(**generate_kwargs)
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
                        "model": model,
                        "aspect_ratio": aspect,
                        "duration_seconds": d.duration_seconds,
                        "source_image": str(request.image_path) if request.image_path else None,
                    },
                )
            )
        return assets

    @staticmethod
    def _load_image(path):
        from google.genai import types

        if not path.exists():
            raise RuntimeError(
                f"Input image not found: {path}. Place the image there or fix the "
                f"deliverable's `image:` path."
            )
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return types.Image(image_bytes=path.read_bytes(), mime_type=mime)
