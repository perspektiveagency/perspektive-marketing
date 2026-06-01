"""Output-path conventions and manifest writing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import PipelineConfig, company_dir
from .models import Brand, Brief, Deliverable, GeneratedAsset


def deliverable_output_dir(
    brand: Brand, brief: Brief, deliverable: Deliverable, config: PipelineConfig
) -> Path:
    """`companies/<slug>/outputs/<brief>/<deliverable-id>/`."""
    return company_dir(brand.slug, config) / config.output_subdir / brief.name / deliverable.id


def write_manifest(output_dir: Path, assets: list[GeneratedAsset]) -> Path:
    """Write a `manifest.json` describing what was generated, for traceability."""
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(assets),
        "assets": [a.model_dump(mode="json") for a in assets],
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path
