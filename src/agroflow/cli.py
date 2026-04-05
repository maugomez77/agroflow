"""CLI for AgroFlow Intelligence — AI-powered agricultural supply chain."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import store
from .demo import generate_demo_data, async_generate_demo_data

app = typer.Typer(
    name="agroflow",
    help="AgroFlow Intelligence -- AI-powered agricultural supply chain for Michoacan, Mexico",
    no_args_is_help=True,
)
console = Console()

# ── Helpers ────────────────────────────────────────────────────

CROP_EMOJI = {"avocado": "[green]Avocado[/]", "berry": "[magenta]Berry[/]", "lemon": "[yellow]Lemon[/]", "mango": "[yellow]Mango[/]"}
STATUS_COLOR = {"preparing": "[cyan]preparing[/]", "in_transit": "[yellow]in_transit[/]", "customs": "[red]customs[/]", "delivered": "[green]delivered[/]"}
SEVERITY_COLOR = {"low": "[green]low[/]", "medium": "[yellow]medium[/]", "high": "[red]high[/]", "critical": "[bold red]CRITICAL[/]"}
TREND_ICON = {"up": "[green]+[/]", "down": "[red]-[/]", "stable": "[dim]=[/]"}
PRIORITY_COLOR = {"low": "[green]low[/]", "medium": "[yellow]medium[/]", "high": "[red]high[/]", "critical": "[bold red]CRITICAL[/]"}


def _no_data():
    console.print("[dim]No data. Run [bold]agroflow demo[/bold] first.[/dim]")
    raise typer.Exit()


# ── Commands ───────────────────────────────────────────────────

@app.command()
def farms():
    """List all registered farms."""
    items = store.list_farms()
    if not items:
        _no_data()
    table = Table(title="Michoacan Farms", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Crop")
    table.add_column("Hectares", justify="right")
    table.add_column("Owner")
    table.add_column("Location")
    for f in items:
        table.add_row(
            f.id, f.name, CROP_EMOJI.get(f.crop_type, f.crop_type),
            f"{f.hectares:.0f}", f.owner,
            f"{f.location_lat:.4f}, {f.location_lng:.4f}",
        )
    console.print(table)


@app.command()
def harvests(farm: Optional[str] = typer.Option(None, "--farm", help="Filter by farm name")):
    """List harvests, optionally filtered by farm name."""
    farm_id = None
    if farm:
        for f in store.list_farms():
            if farm.lower() in f.name.lower():
                farm_id = f.id
                break
        if not farm_id:
            console.print(f"[red]Farm matching '{farm}' not found.[/red]")
            raise typer.Exit(1)
    items = store.list_harvests(farm_id)
    if not items:
        _no_data()
    table = Table(title="Harvests", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Farm", style="dim")
    table.add_column("Crop")
    table.add_column("Quantity (kg)", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Date")
    table.add_column("Value (USD)", justify="right", style="green")
    for h in items:
        grade_color = {"A": "green", "B": "yellow", "C": "red"}.get(h.quality_grade, "white")
        table.add_row(
            h.id, h.farm_id, CROP_EMOJI.get(h.crop_type, h.crop_type),
            f"{h.quantity_kg:,.0f}", f"[{grade_color}]{h.quality_grade}[/]",
            h.harvest_date, f"${h.estimated_value_usd:,.0f}",
        )
    console.print(table)


@app.command()
def shipments(status: Optional[str] = typer.Option(None, "--status", help="Filter by status")):
    """Track active shipments with status and ETA."""
    items = store.list_shipments(status)
    if not items:
        _no_data()
    table = Table(title="Active Shipments", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Destination")
    table.add_column("Status")
    table.add_column("Carrier")
    table.add_column("Container")
    table.add_column("Departure")
    table.add_column("ETA")
    table.add_column("Temp (C)", justify="right")
    for s in items:
        last_temp = ""
        if s.temperature_logs:
            last = s.temperature_logs[-1]
            last_temp = f"{last.temperature_c:.1f}"
        table.add_row(
            s.id, s.destination,
            STATUS_COLOR.get(s.status, s.status),
            s.carrier, s.container_id,
            s.departure_date, s.eta, last_temp,
        )
    console.print(table)


@app.command()
def buyers():
    """Show buyer matches with volume and price."""
    items = store.list_buyer_matches()
    if not items:
        _no_data()
    table = Table(title="Buyer Matches", show_lines=True)
    table.add_column("Buyer", style="bold")
    table.add_column("Country")
    table.add_column("Crop")
    table.add_column("Volume (kg)", justify="right")
    table.add_column("Price/kg", justify="right", style="green")
    table.add_column("Certifications")
    table.add_column("Matched Farms")
    for b in items:
        certs = ", ".join(c for c in b.certification_required) if b.certification_required else "[dim]none[/dim]"
        table.add_row(
            b.buyer_name, b.country,
            CROP_EMOJI.get(b.crop_interest, b.crop_interest),
            f"{b.volume_needed_kg:,.0f}", f"${b.price_per_kg_usd:.2f}",
            certs, ", ".join(b.matched_farms),
        )
    console.print(table)


@app.command()
def weather():
    """Current weather alerts for farming regions."""
    items = store.get_weather_alerts()
    if not items:
        _no_data()
    for w in items:
        sev = SEVERITY_COLOR.get(w.severity, w.severity)
        console.print(Panel(
            f"[bold]{w.alert_type.upper()}[/bold] | Severity: {sev} | Date: {w.forecast_date}\n\n"
            f"{w.description}\n\n"
            f"[dim]Affected farms: {', '.join(w.affected_farms)}[/dim]",
            title=f"[bold yellow]{w.region}[/bold yellow] -- {w.id}",
            border_style="yellow",
        ))


@app.command()
def prices():
    """Market prices with trend indicators."""
    items = store.get_market_prices()
    if not items:
        _no_data()
    table = Table(title="Market Prices", show_lines=True)
    table.add_column("Crop")
    table.add_column("Market")
    table.add_column("Price/kg (USD)", justify="right", style="green")
    table.add_column("Trend", justify="center")
    table.add_column("Date")
    table.add_column("Source", style="dim")
    for p in items:
        table.add_row(
            CROP_EMOJI.get(p.crop_type, p.crop_type), p.market,
            f"${p.price_per_kg_usd:.2f}",
            TREND_ICON.get(p.trend, p.trend),
            p.date, p.source,
        )
    console.print(table)


@app.command()
def quality(harvest: Optional[str] = typer.Option(None, "--harvest", help="Filter by harvest ID")):
    """Quality inspection results."""
    items = store.get_quality_inspections(harvest)
    if not items:
        _no_data()
    table = Table(title="Quality Inspections", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Harvest")
    table.add_column("Inspector")
    table.add_column("pH", justify="right")
    table.add_column("Brix", justify="right")
    table.add_column("Defect %", justify="right")
    table.add_column("Pesticide")
    table.add_column("Certification")
    for q in items:
        pest = "[red]DETECTED[/red]" if q.pesticide_residue else "[green]Clear[/green]"
        defect_color = "green" if q.defect_pct < 3 else ("yellow" if q.defect_pct < 6 else "red")
        table.add_row(
            q.id, q.harvest_id, q.inspector,
            f"{q.ph_level:.1f}", f"{q.brix_level:.1f}",
            f"[{defect_color}]{q.defect_pct:.1f}%[/]",
            pest, q.certification_status,
        )
    console.print(table)


@app.command()
def documents(shipment: Optional[str] = typer.Option(None, "--shipment", help="Filter by shipment ID")):
    """Export document status."""
    items = store.get_export_documents(shipment)
    if not items:
        _no_data()
    table = Table(title="Export Documents", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Shipment")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Issued")
    table.add_column("Expires")
    doc_status_color = {"approved": "green", "pending": "yellow", "rejected": "red"}
    for d in items:
        sc = doc_status_color.get(d.status, "white")
        table.add_row(
            d.id, d.shipment_id, d.doc_type,
            f"[{sc}]{d.status}[/]",
            d.issued_date, d.expiry_date,
        )
    console.print(table)


@app.command()
def insights():
    """AI-generated supply chain insights."""
    items = store.get_insights()
    if not items:
        _no_data()
    type_icon = {"optimization": "[cyan]OPT[/cyan]", "risk": "[red]RISK[/red]", "opportunity": "[green]OPP[/green]"}
    for i in items:
        console.print(Panel(
            f"{type_icon.get(i.insight_type, i.insight_type)} | Priority: {PRIORITY_COLOR.get(i.priority, i.priority)}\n\n"
            f"{i.description}\n\n"
            f"[dim]Affected: {', '.join(i.affected_entities)}[/dim]",
            title=f"[bold]{i.title}[/bold]",
            subtitle=i.created_at[:10],
            border_style="blue",
        ))


@app.command()
def analyze():
    """Run full AI supply chain analysis (calls Claude)."""
    from . import ai
    farm_data = [f.model_dump() for f in store.list_farms()]
    harvest_data = [h.model_dump() for h in store.list_harvests()]
    shipment_data = [s.model_dump() for s in store.list_shipments()]
    if not farm_data:
        _no_data()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Analyzing supply chain with AI...", total=None)
        result = ai.analyze_supply_chain(farm_data, harvest_data, shipment_data)
    console.print(Panel(json.dumps(result, indent=2, ensure_ascii=False), title="[bold green]AI Supply Chain Analysis[/bold green]", border_style="green"))


@app.command()
def predict(farm: Optional[str] = typer.Option(None, "--farm", help="Farm name to predict")):
    """AI yield prediction for a farm."""
    from . import ai
    target = None
    for f in store.list_farms():
        if farm and farm.lower() in f.name.lower():
            target = f
            break
    if not target:
        target = store.list_farms()[0] if store.list_farms() else None
    if not target:
        _no_data()
    weather_data = [w.model_dump() for w in store.get_weather_alerts()]
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task(f"Predicting yield for {target.name}...", total=None)
        result = ai.predict_yield(target.model_dump(), weather_data)
    console.print(Panel(json.dumps(result, indent=2, ensure_ascii=False), title=f"[bold green]Yield Prediction: {target.name}[/bold green]", border_style="green"))


@app.command()
def optimize():
    """AI logistics optimization suggestions."""
    from . import ai
    shipment_data = [s.model_dump() for s in store.list_shipments()]
    if not shipment_data:
        _no_data()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Optimizing logistics with AI...", total=None)
        result = ai.optimize_logistics(shipment_data)
    console.print(Panel(json.dumps(result, indent=2, ensure_ascii=False), title="[bold green]AI Logistics Optimization[/bold green]", border_style="green"))


@app.command()
def report():
    """Generate AI market report."""
    from . import ai
    price_data = [p.model_dump() for p in store.get_market_prices()]
    if not price_data:
        _no_data()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Generating market report with AI...", total=None)
        result = ai.generate_market_report(price_data)
    console.print(Panel(json.dumps(result, indent=2, ensure_ascii=False), title="[bold green]AI Market Report[/bold green]", border_style="green"))


@app.command()
def demo():
    """Load demo data with real-time market research."""
    import asyncio
    console.print("[bold cyan]Researching real market data...[/bold cyan]")
    console.print("[dim]Searching DuckDuckGo for prices, weather, export news, and buyer activity...[/dim]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Gathering real-time data and generating demo...", total=None)
        asyncio.run(async_generate_demo_data())
    console.print("[bold green]Demo data loaded with real-time research![/bold green] 12 farms, 30 harvests, 8 shipments, 6 buyers, and more.")
    console.print("[dim]Run [bold]agroflow status[/bold] to see the dashboard.[/dim]")


@app.command()
def status():
    """Dashboard summary with key metrics."""
    stats = store.get_stats()
    if not stats:
        _no_data()

    # Header
    console.print(Panel(
        "[bold green]AgroFlow Intelligence[/bold green] -- Michoacan Agricultural Supply Chain",
        border_style="green",
    ))

    # KPIs
    kpi_table = Table(show_header=False, box=None, padding=(0, 3))
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    kpi_table.add_row(
        f"[bold]{stats.total_farms}[/bold]\n[dim]Farms[/dim]",
        f"[bold]{stats.total_hectares:.0f}[/bold]\n[dim]Hectares[/dim]",
        f"[bold]{stats.active_shipments}[/bold]\n[dim]Active Shipments[/dim]",
        f"[bold]{stats.monthly_export_tons:,.0f}[/bold]\n[dim]Tons/Month[/dim]",
        f"[bold green]${stats.revenue_ytd_usd:,.0f}[/bold green]\n[dim]Revenue YTD[/dim]",
    )
    console.print(Panel(kpi_table, title="[bold]Key Metrics[/bold]", border_style="cyan"))

    # Top Buyers
    buyer_str = " | ".join(f"[bold]{b}[/bold]" for b in stats.top_buyers)
    console.print(Panel(buyer_str, title="[bold]Top Buyers[/bold]", border_style="blue"))

    # Weather alerts summary
    alerts = store.get_weather_alerts()
    critical = [a for a in alerts if a.severity in ("high", "critical")]
    if critical:
        alert_lines = []
        for a in critical:
            sev = SEVERITY_COLOR.get(a.severity, a.severity)
            alert_lines.append(f"  {sev} {a.region}: {a.alert_type.upper()} -- {a.description[:80]}...")
        console.print(Panel("\n".join(alert_lines), title="[bold red]Active Alerts[/bold red]", border_style="red"))

    # Shipment summary
    all_shipments = store.list_shipments()
    in_transit = len([s for s in all_shipments if s.status == "in_transit"])
    in_customs = len([s for s in all_shipments if s.status == "customs"])
    preparing = len([s for s in all_shipments if s.status == "preparing"])
    console.print(Panel(
        f"  [yellow]{in_transit}[/yellow] in transit | [red]{in_customs}[/red] in customs | [cyan]{preparing}[/cyan] preparing",
        title="[bold]Shipment Status[/bold]", border_style="yellow",
    ))

    console.print("\n[dim]Commands: farms | harvests | shipments | buyers | weather | prices | quality | documents | insights | analyze | predict | optimize | report[/dim]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
):
    """Start FastAPI server."""
    import uvicorn
    console.print(f"[bold green]Starting AgroFlow API[/bold green] at http://{host}:{port}")
    console.print("[dim]API docs at /docs | Health at /health[/dim]")
    uvicorn.run("agroflow.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
