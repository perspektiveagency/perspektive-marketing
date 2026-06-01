# Perspektive — Content Generation Pipeline

An automation pipeline that turns per-company creative **briefs** into
batch-generated **photo and video** assets, using pluggable AI providers
(OpenAI, Google, Runway, …).

Built for running content for several client companies side by side: each
company lives in its own folder with a brand kit and a set of briefs, and the
pipeline fans those briefs out to the right generation provider.

## How it works

```
companies/<slug>/brand.yaml          brand kit (voice, colors, keywords)
companies/<slug>/briefs/<name>.yaml  a campaign: a list of deliverables
        │
        ▼
   perspektive generate <company> <brief>
        │   builds a brand-enriched prompt per deliverable
        │   picks a provider (per-deliverable override, else config default)
        ▼
companies/<slug>/outputs/<brief>/<deliverable>/   generated files + manifest.json
```

## Quick start

```bash
# 1. Install (editable, with all provider SDKs + dev tools)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,all]"

# 2. Configure API keys
cp .env.example .env   # then fill in the keys you have

# 3. Explore
perspektive companies              # list configured companies
perspektive briefs acme-co         # list a company's briefs
perspektive providers              # list available generation backends
perspektive validate               # validate all brand/brief config

# 4. Dry run — no API calls, writes placeholder files end-to-end
perspektive generate acme-co summer-launch --dry-run

# 5. Real run (needs the relevant API keys)
perspektive generate acme-co summer-launch
perspektive generate acme-co summer-launch -d hero-photo   # one deliverable
```

`make demo` runs the dry run above; `make test` runs the test suite.

## Adding a company

```
companies/<your-slug>/
├── brand.yaml          # see companies/acme-co/brand.yaml
├── briefs/
│   └── <campaign>.yaml # see companies/acme-co/briefs/summer-launch.yaml
└── outputs/.gitkeep    # generated assets land here (git-ignored)
```

## Providers

| name     | photo            | video            | env var              |
|----------|------------------|------------------|----------------------|
| `openai` | gpt-image-1 ✅   | Sora (TODO)      | `OPENAI_API_KEY`     |
| `google` | Imagen ✅        | Veo (TODO)       | `GOOGLE_API_KEY`     |
| `runway` | —                | Gen-3/4 (TODO)   | `RUNWAYML_API_SECRET`|
| `stub`   | placeholder      | placeholder      | none (used by `--dry-run`) |

Photo generation is wired up for OpenAI and Google. Video adapters and the
Sora photo-to-video path are left as clearly-marked skeletons (`NotImplementedError`
with guidance) — fill them in against the current SDK once you pick your
primary video tool. See `docs/ARCHITECTURE.md` to add or extend a provider.

> Model names (e.g. `gpt-image-1`, `imagen-4.0-generate-001`) are set in the
> provider modules — bump them as the APIs evolve.

## Layout

```
config/pipeline.yaml      default provider per media type
companies/                one folder per client (brand kit + briefs + outputs)
src/perspektive/          the pipeline package (CLI, config, providers)
tests/                    pytest suite (runs offline via the stub provider)
docs/ARCHITECTURE.md      design notes & extension guide
```
