"""Provider interface every generation backend implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import GeneratedAsset, GenerationRequest, MediaType


class ContentProvider(ABC):
    """Base class for a photo/video generation backend."""

    name: str = "base"
    media_types: set[MediaType] = set()

    def supports(self, media_type: MediaType) -> bool:
        return media_type in self.media_types

    @abstractmethod
    def generate(self, request: GenerationRequest) -> list[GeneratedAsset]:
        """Produce the deliverable's assets, write them under
        `request.output_dir`, and return their metadata."""
        raise NotImplementedError
