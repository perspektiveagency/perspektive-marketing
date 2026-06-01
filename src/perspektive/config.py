"""Loading of pipeline config, companies, brands and briefs from disk."""

from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .models import Brand, Brief

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPANIES_DIR = REPO_ROOT / "companies"
DEFAULT_PIPELINE_CONFIG = REPO_ROOT / "config" / "pipeline.yaml"


class ProviderDefaults(BaseModel):
    """Default provider to use per media type when a deliverable doesn't override it."""

    photo: str = "stub"
    video: str = "stub"


class PipelineConfig(BaseModel):
    companies_dir: Path = DEFAULT_COMPANIES_DIR
    output_subdir: str = "outputs"
    providers: ProviderDefaults = Field(default_factory=ProviderDefaults)


def load_pipeline_config(path: Path | None = None) -> PipelineConfig:
    """Load `config/pipeline.yaml` (if present) and `.env` for API keys."""
    load_dotenv()
    path = path or DEFAULT_PIPELINE_CONFIG
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        return PipelineConfig(**data)
    return PipelineConfig()


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Expected config file not found: {path}")
    return yaml.safe_load(path.read_text()) or {}


def company_dir(slug: str, config: PipelineConfig) -> Path:
    return config.companies_dir / slug


def list_companies(config: PipelineConfig) -> list[str]:
    if not config.companies_dir.exists():
        return []
    return sorted(
        p.name for p in config.companies_dir.iterdir() if (p / "brand.yaml").exists()
    )


def load_brand(slug: str, config: PipelineConfig) -> Brand:
    data = _read_yaml(company_dir(slug, config) / "brand.yaml")
    data.setdefault("slug", slug)
    return Brand(**data)


def list_briefs(slug: str, config: PipelineConfig) -> list[str]:
    briefs_dir = company_dir(slug, config) / "briefs"
    if not briefs_dir.exists():
        return []
    return sorted(p.stem for p in briefs_dir.glob("*.y*ml"))


def load_brief(slug: str, brief_name: str, config: PipelineConfig) -> Brief:
    briefs_dir = company_dir(slug, config) / "briefs"
    path = next(
        (
            c
            for c in (briefs_dir / f"{brief_name}.yaml", briefs_dir / f"{brief_name}.yml")
            if c.exists()
        ),
        None,
    )
    if path is None:
        raise FileNotFoundError(f"Brief '{brief_name}' not found for company '{slug}'")
    data = _read_yaml(path)
    data.setdefault("name", brief_name)
    data.setdefault("company", slug)
    return Brief(**data)
