# Architecture

A small, file-driven pipeline. Configuration lives in version-controlled YAML;
code is a thin orchestration layer over swappable provider adapters.

## Data flow

1. **Config** (`config.py`) loads `config/pipeline.yaml` and `.env`, then reads
   a company's `brand.yaml` and a `briefs/<name>.yaml`.
2. **Models** (`models.py`) validate that data into `Brand`, `Brief`,
   `Deliverable` (Pydantic).
3. **Pipeline** (`pipeline.py`):
   - `build_prompt` merges the deliverable prompt with brand voice, keywords,
     colors and negative prompts.
   - `resolve_provider_name` chooses the provider: the deliverable's `provider`
     override, else the `config.providers` default for that media type.
   - `run_deliverable` builds a `GenerationRequest`, calls the provider, and
     writes a `manifest.json` next to the assets.
4. **Providers** (`providers/`) implement `ContentProvider.generate()` and write
   files into `request.output_dir`.
5. **Storage** (`storage.py`) owns the output path convention and the manifest.

```
companies/<slug>/outputs/<brief>/<deliverable-id>/
    <deliverable-id>-01.png
    <deliverable-id>-02.png
    manifest.json
```

## Providers & the registry

`providers/registry.py` maps a provider name to `"module:Class"` and imports it
lazily, so:

- importing the package never pulls in optional SDKs, and
- `--dry-run` (which forces the `stub` provider) works with zero dependencies.

A provider declares which `media_types` it supports; the pipeline refuses a
deliverable whose type isn't supported.

### Add a provider

1. Create `providers/<name>_provider.py` with a `ContentProvider` subclass:
   - set `name` and `media_types`,
   - implement `generate(request) -> list[GeneratedAsset]`,
   - import the SDK lazily inside the method and read the API key from `os.environ`.
2. Register it in `providers/registry.py`.
3. (Optional) add its SDK to a `[project.optional-dependencies]` extra in
   `pyproject.toml`.

The bundled `openai`/`google`/`runway` modules show the pattern; `stub.py` is
the minimal reference implementation.

## Design choices

- **Per-company folders + config**, not a database — content briefs and brand
  kits are reviewable in PRs and trivially diff-able. Add a client by adding a
  folder.
- **Provider-agnostic adapters** — the brief says *what*; the provider says
  *how*. Swap or add backends without touching briefs.
- **Generated outputs are git-ignored** (`companies/*/outputs/*`) — the repo
  holds inputs and code, not large binary artifacts. Wire `outputs/` to object
  storage (S3/GCS) when you move beyond local runs.

## Where to extend next

- Implement the video paths (Veo / Runway / Sora) — marked with `TODO` /
  `NotImplementedError`.
- Add asset post-processing (resize/crop per platform, watermarking).
- Add a `--concurrency` option to fan out deliverables in parallel.
- Push outputs to cloud storage and record URLs in the manifest.
