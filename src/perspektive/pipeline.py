"""Orchestration: brief -> per-deliverable jobs -> provider -> saved assets."""

from __future__ import annotations

from pathlib import Path

from .config import PipelineConfig, company_dir, load_brand, load_brief
from .logging import get_logger
from .models import Brand, Brief, Deliverable, GeneratedAsset, GenerationRequest
from .providers.registry import get_provider
from .storage import deliverable_output_dir, write_manifest

log = get_logger(__name__)


def build_prompt(brand: Brand, deliverable: Deliverable) -> str:
    """Enrich the deliverable prompt with brand context."""
    parts = [deliverable.prompt.strip()]
    if brand.brand_voice:
        parts.append(f"Brand voice: {brand.brand_voice}.")
    if brand.keywords:
        parts.append("Themes: " + ", ".join(brand.keywords) + ".")
    if brand.colors:
        parts.append("Brand colors: " + ", ".join(brand.colors) + ".")
    if brand.negative_prompts:
        parts.append("Avoid: " + ", ".join(brand.negative_prompts) + ".")
    return " ".join(parts)


def resolve_provider_name(deliverable: Deliverable, config: PipelineConfig) -> str:
    if deliverable.provider:
        return deliverable.provider
    return getattr(config.providers, deliverable.type.value)


def resolve_model(deliverable: Deliverable, config: PipelineConfig) -> str | None:
    """Per-deliverable model override, else the config default, else None
    (let the provider pick its own default)."""
    if deliverable.model:
        return deliverable.model
    return getattr(config.models, deliverable.type.value)


def resolve_image_path(
    deliverable: Deliverable, brand: Brand, config: PipelineConfig
) -> Path | None:
    """Resolve a deliverable's input image (for image-to-video) relative to the
    company directory. Returns None when no image is set."""
    if not deliverable.image:
        return None
    return company_dir(brand.slug, config) / deliverable.image


def run_deliverable(
    brand: Brand,
    brief: Brief,
    deliverable: Deliverable,
    config: PipelineConfig,
    *,
    dry_run: bool = False,
) -> list[GeneratedAsset]:
    # In dry-run we always use the stub provider so the pipeline runs without keys.
    provider_name = "stub" if dry_run else resolve_provider_name(deliverable, config)
    provider = get_provider(provider_name)
    if not provider.supports(deliverable.type):
        raise ValueError(
            f"Provider '{provider_name}' does not support {deliverable.type.value} "
            f"(deliverable '{deliverable.id}')."
        )

    output_dir = deliverable_output_dir(brand, brief, deliverable, config)
    output_dir.mkdir(parents=True, exist_ok=True)

    request = GenerationRequest(
        deliverable=deliverable,
        brand=brand,
        prompt=build_prompt(brand, deliverable),
        output_dir=output_dir,
        model=resolve_model(deliverable, config),
        image_path=resolve_image_path(deliverable, brand, config),
        dry_run=dry_run,
    )
    log.info(
        "Generating %s '%s' via %s (%d asset(s))",
        deliverable.type.value,
        deliverable.id,
        provider_name,
        deliverable.count,
    )
    assets = provider.generate(request)
    write_manifest(output_dir, assets)
    return assets


def run_brief(
    slug: str,
    brief_name: str,
    config: PipelineConfig,
    *,
    dry_run: bool = False,
    only: set[str] | None = None,
) -> list[GeneratedAsset]:
    """Run every deliverable in a brief (optionally filtered by id)."""
    brand = load_brand(slug, config)
    brief = load_brief(slug, brief_name, config)
    results: list[GeneratedAsset] = []
    for deliverable in brief.deliverables:
        if only and deliverable.id not in only:
            continue
        results.extend(run_deliverable(brand, brief, deliverable, config, dry_run=dry_run))
    return results
