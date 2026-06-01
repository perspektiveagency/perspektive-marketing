from perspektive import config as cfg


def test_default_config_lists_seed_companies():
    config = cfg.load_pipeline_config()
    companies = cfg.list_companies(config)
    assert "acme-co" in companies
    assert "northwind-foods" in companies


def test_load_brand_and_briefs():
    config = cfg.load_pipeline_config()
    brand = cfg.load_brand("acme-co", config)
    assert brand.name == "Acme Athletics"
    assert brand.slug == "acme-co"

    briefs = cfg.list_briefs("acme-co", config)
    assert "summer-launch" in briefs

    brief = cfg.load_brief("acme-co", "summer-launch", config)
    assert brief.deliverables
    assert {d.type.value for d in brief.deliverables} == {"photo", "video"}
