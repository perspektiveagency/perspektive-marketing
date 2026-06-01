"""Name -> provider lookup with lazy imports.

Real providers import heavy/optional SDKs only when instantiated, so importing
this module (and running `--dry-run`) never requires the optional dependencies.
"""

from __future__ import annotations

import importlib

from .base import ContentProvider

# name -> "module.path:ClassName"
_PROVIDERS: dict[str, str] = {
    "stub": "perspektive.providers.stub:StubProvider",
    "openai": "perspektive.providers.openai_provider:OpenAIProvider",
    "google": "perspektive.providers.google_provider:GoogleProvider",
    "runway": "perspektive.providers.runway_provider:RunwayProvider",
}


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider(name: str) -> ContentProvider:
    try:
        target = _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(available_providers())}"
        ) from exc
    module_path, _, class_name = target.partition(":")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()
