"""Runway provider — text/image-to-video (Gen-3 / Gen-4).

Also serves as the template slot for other dedicated video platforms
(Pika, Kling): copy this module and register the new name in registry.py.

Requires the `runway` extra:  pip install 'perspektive-content[runway]'
and the RUNWAYML_API_SECRET environment variable.
"""

from __future__ import annotations

import os

from .base import ContentProvider
from ..models import GeneratedAsset, GenerationRequest, MediaType


class RunwayProvider(ContentProvider):
    name = "runway"
    media_types = {MediaType.video}

    def generate(self, request: GenerationRequest) -> list[GeneratedAsset]:
        try:
            from runwayml import RunwayML  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "runwayml not installed. Run: pip install 'perspektive-content[runway]'"
            ) from exc
        if not os.environ.get("RUNWAYML_API_SECRET"):
            raise RuntimeError("RUNWAYML_API_SECRET is not set.")

        # TODO: Runway generation is async. Sketch:
        #   client = RunwayML()
        #   task = client.text_to_video.create(model="gen4_turbo",
        #                                       prompt_text=request.prompt,
        #                                       duration=request.deliverable.duration_seconds or 5,
        #                                       ratio=...)
        #   task = task.wait_for_task_output()
        #   download task.output[*] urls into request.output_dir
        # See https://docs.dev.runwayml.com for the current surface.
        raise NotImplementedError(
            "Runway video generation skeleton — create task, poll, download here."
        )
