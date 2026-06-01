import yaml

from perspektive.config import ModelDefaults, PipelineConfig
from perspektive.models import Brand, Deliverable, MediaType
from perspektive.pipeline import build_prompt, resolve_model, run_brief


def _seed_company(tmp_path):
    company = tmp_path / "acme"
    (company / "briefs").mkdir(parents=True)
    (company / "brand.yaml").write_text(
        yaml.safe_dump({"name": "Acme", "keywords": ["bold"]})
    )
    (company / "briefs" / "launch.yaml").write_text(
        yaml.safe_dump(
            {
                "deliverables": [
                    {"id": "hero", "type": "photo", "prompt": "a hero shot", "count": 2},
                    {"id": "promo", "type": "video", "prompt": "a promo", "duration_seconds": 6},
                ]
            }
        )
    )
    return PipelineConfig(companies_dir=tmp_path)


def test_build_prompt_includes_brand_context():
    brand = Brand(name="Acme", slug="acme", keywords=["bold", "modern"], brand_voice="confident")
    deliverable = Deliverable(id="x", type=MediaType.photo, prompt="a running shoe")
    prompt = build_prompt(brand, deliverable)
    assert "a running shoe" in prompt
    assert "bold" in prompt
    assert "confident" in prompt


def test_run_brief_dry_run_writes_assets(tmp_path):
    config = _seed_company(tmp_path)
    assets = run_brief("acme", "launch", config, dry_run=True)

    # 2 photos + 1 video
    assert len(assets) == 3
    for asset in assets:
        assert asset.provider == "stub"
        assert asset.path.exists()

    # manifest written per deliverable
    assert (tmp_path / "acme" / "outputs" / "launch" / "hero" / "manifest.json").exists()


def test_resolve_model_prefers_deliverable_then_config():
    config = PipelineConfig(models=ModelDefaults(video="veo-3.1-fast-generate-001"))
    from_config = Deliverable(id="a", type=MediaType.video, prompt="x")
    assert resolve_model(from_config, config) == "veo-3.1-fast-generate-001"

    override = Deliverable(id="b", type=MediaType.video, prompt="x", model="veo-3.0-generate-001")
    assert resolve_model(override, config) == "veo-3.0-generate-001"

    # No config default and no override -> None (provider picks its own default).
    assert resolve_model(Deliverable(id="c", type=MediaType.photo, prompt="x"), config) is None


def test_run_brief_filter_by_deliverable(tmp_path):
    config = _seed_company(tmp_path)
    assets = run_brief("acme", "launch", config, dry_run=True, only={"promo"})
    assert len(assets) == 1
    assert assets[0].media_type is MediaType.video
