"""Offline stub provider used for `--dry-run` and tests.

Writes lightweight placeholder files instead of calling any API, so the whole
pipeline can be exercised end-to-end without keys or network.
"""

from __future__ import annotations

from .base import ContentProvider
from ..models import GeneratedAsset, GenerationRequest, MediaType


class StubProvider(ContentProvider):
    name = "stub"
    media_types = {MediaType.photo, MediaType.video}

    def generate(self, request: GenerationRequest) -> list[GeneratedAsset]:
        d = request.deliverable
        assets: list[GeneratedAsset] = []
        for i in range(1, d.count + 1):
            path = request.output_dir / f"{d.id}-{i:02d}.txt"
            path.write_text(
                "PERSPEKTIVE placeholder asset (dry run)\n"
                f"media_type: {d.type.value}\n"
                f"company:    {request.brand.slug}\n"
                f"aspect:     {d.aspect_ratio or request.brand.default_aspect_ratio}\n"
                f"prompt:     {request.prompt}\n"
            )
            assets.append(
                GeneratedAsset(
                    deliverable_id=d.id,
                    media_type=d.type,
                    provider=self.name,
                    path=path,
                    prompt=request.prompt,
                    metadata={"placeholder": True, "index": i},
                )
            )
        return assets
