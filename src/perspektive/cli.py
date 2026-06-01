"""`perspektive` command-line interface."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from . import config as cfg
from .pipeline import run_brief
from .providers.registry import available_providers

app = typer.Typer(add_completion=False, help="Perspektive content generation pipeline.")
console = Console()


@app.command("companies")
def companies_cmd() -> None:
    """List configured companies."""
    config = cfg.load_pipeline_config()
    names = cfg.list_companies(config)
    if not names:
        console.print("[yellow]No companies found under the companies/ directory.[/]")
        raise typer.Exit()
    table = Table(title="Companies")
    table.add_column("slug")
    table.add_column("name")
    table.add_column("briefs", justify="right")
    for slug in names:
        brand = cfg.load_brand(slug, config)
        table.add_row(slug, brand.name, str(len(cfg.list_briefs(slug, config))))
    console.print(table)


@app.command("briefs")
def briefs_cmd(company: str) -> None:
    """List briefs for a company."""
    config = cfg.load_pipeline_config()
    briefs = cfg.list_briefs(company, config)
    if not briefs:
        console.print(f"[yellow]No briefs found for '{company}'.[/]")
        raise typer.Exit()
    for name in briefs:
        console.print(f"- {name}")


@app.command("providers")
def providers_cmd() -> None:
    """List available generation providers."""
    for name in available_providers():
        console.print(f"- {name}")


@app.command("validate")
def validate_cmd(
    company: str | None = typer.Argument(None, help="Validate one company (default: all)."),
) -> None:
    """Validate brand + brief config files."""
    config = cfg.load_pipeline_config()
    slugs = [company] if company else cfg.list_companies(config)
    ok = True
    for slug in slugs:
        try:
            cfg.load_brand(slug, config)
            for brief in cfg.list_briefs(slug, config):
                cfg.load_brief(slug, brief, config)
            console.print(f"[green]✓[/] {slug}")
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            ok = False
            console.print(f"[red]✗ {slug}: {exc}[/]")
    raise typer.Exit(code=0 if ok else 1)


@app.command("generate")
def generate_cmd(
    company: str,
    brief: str,
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Use the stub provider: write placeholders, call no APIs."
    ),
    deliverable: list[str] | None = typer.Option(
        None, "--deliverable", "-d", help="Only run these deliverable id(s)."
    ),
) -> None:
    """Generate the assets for a company's brief."""
    config = cfg.load_pipeline_config()
    assets = run_brief(
        company,
        brief,
        config,
        dry_run=dry_run,
        only=set(deliverable) if deliverable else None,
    )
    console.print(f"[green]Generated {len(assets)} asset(s).[/]")
    for asset in assets:
        console.print(f"  - {asset.media_type.value}: {asset.path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
