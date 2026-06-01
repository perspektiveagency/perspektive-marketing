"""Pydantic data models shared across the pipeline."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    photo = "photo"
    video = "video"


class Brand(BaseModel):
    """A company's brand kit — drives prompt enrichment and defaults."""

    name: str
    slug: str
    description: str | None = None
    brand_voice: str | None = None
    colors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    negative_prompts: list[str] = Field(default_factory=list)
    default_aspect_ratio: str = "16:9"


class Deliverable(BaseModel):
    """A single asset (or set of assets) requested in a brief."""

    id: str
    type: MediaType
    prompt: str
    provider: str | None = None  # overrides the per-media-type default
    model: str | None = None  # overrides the provider/config default model
    count: int = 1
    aspect_ratio: str | None = None
    duration_seconds: int | None = None  # video only
    extra: dict = Field(default_factory=dict)  # provider-specific knobs


class Brief(BaseModel):
    """A campaign brief for one company, listing the deliverables to generate."""

    name: str
    company: str
    campaign: str | None = None
    deliverables: list[Deliverable]


class GenerationRequest(BaseModel):
    """Everything a provider needs to produce one deliverable."""

    deliverable: Deliverable
    brand: Brand
    prompt: str  # final, brand-enriched prompt
    output_dir: Path
    model: str | None = None  # resolved model name; None => provider default
    dry_run: bool = False


class GeneratedAsset(BaseModel):
    """A single produced file plus the metadata to trace how it was made."""

    deliverable_id: str
    media_type: MediaType
    provider: str
    path: Path
    prompt: str
    metadata: dict = Field(default_factory=dict)
