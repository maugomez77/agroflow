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

CROP_EMOJI = {
    "avocado": "[green]Avocado[/]",
    "berry": "[magenta]Berry[/]",
    "lemon": "[yellow]Lemon[/]",
    "mango": "[yellow]Mango[/]",
    "rose": "[red]Rose[/]",
    "chrysanthemum": "[bright_yellow]Crisantemo[/]",
    "gerbera": "[bright_magenta]Gerbera[/]",
    "lily": "[white]Lily[/]",
}
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
    console.print("[bold green]Demo data loaded with real-time research![/bold green]")
    console.print("  16 farms (12 Michoacan + 4 EdoMex floriculture), 34 harvests, 8 shipments, 6 buyers")
    console.print("  3 cooperatives, 4 phyto certificates, NDVI seed data, Enterprise tier")
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

    # Cooperative summary
    coops = store.list_cooperatives()
    if coops:
        console.print(Panel(
            f"  {len(coops)} cooperatives | "
            + " | ".join(f"[bold]{c.name}[/bold] ({len(c.member_farm_ids)} members)" for c in coops),
            title="[bold]Cooperatives[/bold]", border_style="cyan",
        ))

    # Phyto certificates summary
    phyto_certs = store.list_phyto_certificates()
    if phyto_certs:
        approved = len([c for c in phyto_certs if c.status.value == "approved"])
        pending = len([c for c in phyto_certs if c.status.value in ("draft", "submitted")])
        console.print(Panel(
            f"  [green]{approved}[/green] approved | [yellow]{pending}[/yellow] pending",
            title="[bold]Phytosanitary Certificates[/bold]", border_style="cyan",
        ))

    # Tier info
    sub = store.get_subscription()
    tier_color = {"starter": "white", "pro": "cyan", "enterprise": "green"}
    tc = tier_color.get(sub.tier.value, "white")
    console.print(f"\n[dim]Subscription:[/dim] [{tc}][bold]{sub.tier.value.upper()}[/bold][/{tc}] | {len(store.TIER_FEATURES.get(sub.tier.value, []))} features")

    console.print("\n[dim]Commands: farms | harvests | shipments | buyers | weather | prices | quality | documents | insights | analyze | predict | optimize | report[/dim]")
    console.print("[dim]Premium: cooperatives | aggregate <id> | satellite | phyto | tier[/dim]")
    console.print("[dim]Live feeds: live-weather | trade | soil[/dim]")


@app.command(name="live-weather")
def live_weather():
    """Show real-time weather for all farm locations from Open-Meteo."""
    import asyncio
    from .feeds import fetch_all_farm_weather

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Fetching live weather from Open-Meteo...", total=None)
        result = asyncio.run(fetch_all_farm_weather())

    locations = result.get("locations", [])
    alerts = result.get("alerts", [])
    fetched = result.get("fetched_at", "")

    if not locations:
        console.print("[red]Unable to fetch weather data. Check your internet connection.[/red]")
        raise typer.Exit(1)

    # Current conditions table
    table = Table(title="Live Weather -- Michoacan Farms", show_lines=True, caption=f"[dim]Source: Open-Meteo | {fetched[:19]}[/dim]")
    table.add_column("Region", style="bold")
    table.add_column("Farms", style="dim")
    table.add_column("Temp (C)", justify="right")
    table.add_column("Humidity", justify="right")
    table.add_column("Wind (km/h)", justify="right")
    table.add_column("Precip (mm)", justify="right")
    table.add_column("Conditions")

    for loc in locations:
        cur = loc.get("current", {})
        temp = cur.get("temp_c")
        humidity = cur.get("humidity")
        wind = cur.get("wind_kmh")
        precip = cur.get("precipitation_mm")
        desc = cur.get("description", "")

        # Color code temperature
        temp_str = ""
        if temp is not None:
            if temp < 4:
                temp_str = f"[bold red]{temp:.1f}[/bold red]"
            elif temp > 35:
                temp_str = f"[bold red]{temp:.1f}[/bold red]"
            elif temp > 28:
                temp_str = f"[yellow]{temp:.1f}[/yellow]"
            else:
                temp_str = f"[green]{temp:.1f}[/green]"

        farm_ids = ", ".join(loc.get("farm_ids", []))

        table.add_row(
            loc["region"], farm_ids, temp_str,
            f"{humidity}%" if humidity is not None else "-",
            f"{wind:.1f}" if wind is not None else "-",
            f"{precip:.1f}" if precip is not None else "-",
            desc,
        )

    console.print(table)

    # 7-day forecast per region
    for loc in locations:
        daily = loc.get("daily", [])
        if not daily:
            continue
        ftable = Table(title=f"7-Day Forecast: {loc['region']}", show_lines=False, box=None)
        ftable.add_column("Date", style="dim")
        ftable.add_column("High (C)", justify="right")
        ftable.add_column("Low (C)", justify="right")
        ftable.add_column("Rain (mm)", justify="right")
        ftable.add_column("Rain %", justify="right")

        for day in daily:
            t_max = day.get("temp_max")
            t_min = day.get("temp_min")
            rain = day.get("precip_mm")
            prob = day.get("precip_prob")

            max_str = f"{t_max:.0f}" if t_max is not None else "-"
            min_str = f"{t_min:.0f}" if t_min is not None else "-"
            if t_min is not None and t_min < 4:
                min_str = f"[bold red]{t_min:.0f}[/bold red]"
            if t_max is not None and t_max > 35:
                max_str = f"[bold red]{t_max:.0f}[/bold red]"

            rain_str = f"{rain:.1f}" if rain is not None else "-"
            if rain is not None and rain > 30:
                rain_str = f"[bold red]{rain:.1f}[/bold red]"

            prob_str = f"{prob}%" if prob is not None else "-"
            if prob is not None and prob > 80:
                prob_str = f"[bold yellow]{prob}%[/bold yellow]"

            ftable.add_row(day.get("date", ""), max_str, min_str, rain_str, prob_str)

        console.print(ftable)

    # Alerts
    if alerts:
        console.print()
        for a in alerts:
            sev = SEVERITY_COLOR.get(a["severity"], a["severity"])
            console.print(Panel(
                f"[bold]{a['alert_type'].upper()}[/bold] | Severity: {sev} | Date: {a['forecast_date']}\n\n"
                f"{a['description']}\n\n"
                f"[dim]Affected farms: {', '.join(a.get('affected_farms', []))}[/dim]",
                title=f"[bold yellow]{a['region']}[/bold yellow]",
                border_style="yellow",
            ))
    else:
        console.print("\n[green]No weather alerts -- conditions are normal across all regions.[/green]")


@app.command()
def trade():
    """Show real Mexico avocado export data from UN Comtrade."""
    import asyncio
    from .feeds import fetch_comtrade_exports

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Fetching trade data...", total=None)
        result = asyncio.run(fetch_comtrade_exports())

    live = result.get("live", False)
    source = result.get("source", "Unknown")

    console.print(Panel(
        f"[bold]{result.get('commodity', 'Avocados')}[/bold] (HS {result.get('hs_code', '080440')})\n"
        f"Reporter: {result.get('reporter', 'Mexico')}\n"
        f"Source: {'[green]LIVE[/green]' if live else '[yellow]CACHED[/yellow]'} -- {source}",
        title="[bold green]Mexico Avocado Exports[/bold green]",
        border_style="green",
    ))

    years = result.get("years", {})
    for year in sorted(years.keys()):
        ydata = years[year]
        total_val = ydata.get("total_export_value_usd", 0)
        total_vol = ydata.get("total_volume_kg", 0)

        console.print(f"\n[bold cyan]{year}[/bold cyan]")
        console.print(f"  Total Export Value: [bold green]${total_val:,.0f}[/bold green]")
        console.print(f"  Total Volume: [bold]{total_vol / 1_000_000:,.0f}[/bold] thousand metric tons")

        partners = ydata.get("top_partners", [])
        if partners:
            ptable = Table(show_lines=False, box=None, padding=(0, 2))
            ptable.add_column("Partner", style="bold")
            ptable.add_column("Value (USD)", justify="right", style="green")
            ptable.add_column("Volume (tons)", justify="right")
            ptable.add_column("Share", justify="right")
            for p in partners:
                pval = p.get("value_usd", 0)
                pvol = p.get("volume_kg", 0)
                share = (pval / total_val * 100) if total_val > 0 else 0
                ptable.add_row(
                    p["country"],
                    f"${pval:,.0f}",
                    f"{pvol / 1_000:,.0f}",
                    f"{share:.1f}%",
                )
            console.print(ptable)


@app.command()
def soil():
    """Show real-time soil health for all farm locations."""
    import asyncio
    from .feeds import fetch_all_soil_health

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Fetching soil data from Open-Meteo...", total=None)
        result = asyncio.run(fetch_all_soil_health())

    if not result:
        console.print("[red]Unable to fetch soil data.[/red]")
        raise typer.Exit(1)

    table = Table(title="Soil Health -- Michoacan Farms", show_lines=True, caption="[dim]Source: Open-Meteo Soil API[/dim]")
    table.add_column("Region", style="bold")
    table.add_column("Farms", style="dim")
    table.add_column("Soil Temp (C)", justify="right")
    table.add_column("Moisture (m3/m3)", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    health_color = {"good": "green", "stressed": "yellow", "critical": "red", "unknown": "dim"}

    for s in result:
        status = s.get("health_status", "unknown")
        color = health_color.get(status, "white")
        temp = s.get("soil_temp_c")
        moisture = s.get("soil_moisture")

        table.add_row(
            s["region"],
            ", ".join(s.get("farm_ids", [])),
            f"{temp:.1f}" if temp is not None else "-",
            f"{moisture:.3f}" if moisture is not None else "-",
            f"[{color}]{status.upper()}[/{color}]",
            s.get("details", "")[:80],
        )

    console.print(table)


@app.command()
def cooperatives():
    """List cooperatives and their member farms."""
    items = store.list_cooperatives()
    if not items:
        _no_data()
    for c in items:
        certs = ", ".join(ct for ct in c.certifications) if c.certifications else "[dim]none[/dim]"
        body = (
            f"[bold]Region:[/bold] {c.region}\n"
            f"[bold]Founded:[/bold] {c.founded_year}  |  [bold]Members:[/bold] {len(c.member_farm_ids)}  |  "
            f"[bold]Crop:[/bold] {CROP_EMOJI.get(c.primary_crop, c.primary_crop)}\n"
            f"[bold]Revenue split:[/bold] {c.revenue_split_pct:.0f}% members / {c.coop_fee_pct:.0f}% coop fee\n"
            f"[bold]Certifications:[/bold] {certs}\n\n"
            f"{c.description}\n\n"
            f"[dim]Member farms: {', '.join(c.member_farm_ids)}[/dim]"
        )
        console.print(Panel(body, title=f"[bold green]{c.name}[/bold green] -- {c.id}", border_style="green"))


@app.command()
def aggregate(coop_id: str = typer.Argument(..., help="Cooperative ID, e.g. coop-001")):
    """Show aggregated harvest + revenue metrics for a cooperative."""
    agg = store.aggregate_cooperative(coop_id)
    if not agg:
        console.print(f"[red]Cooperative '{coop_id}' not found.[/red]")
        raise typer.Exit(1)
    coop = agg["cooperative"]
    table = Table(show_header=False, box=None, padding=(0, 3))
    table.add_column(justify="center")
    table.add_column(justify="center")
    table.add_column(justify="center")
    table.add_column(justify="center")
    table.add_row(
        f"[bold]{agg['member_count']}[/bold]\n[dim]Members[/dim]",
        f"[bold]{agg['total_hectares']:.0f}[/bold]\n[dim]Hectares[/dim]",
        f"[bold]{agg['total_harvest_kg']:,.0f}[/bold]\n[dim]Total kg[/dim]",
        f"[bold]{agg['grade_a_pct']:.1f}%[/bold]\n[dim]Grade A[/dim]",
    )
    console.print(Panel(table, title=f"[bold]{coop['name']}[/bold]", border_style="cyan"))

    rev_table = Table(show_header=False, box=None, padding=(0, 3))
    rev_table.add_column(justify="center")
    rev_table.add_column(justify="center")
    rev_table.add_column(justify="center")
    rev_table.add_row(
        f"[bold green]${agg['total_value_usd']:,.0f}[/bold green]\n[dim]Total Value[/dim]",
        f"[bold green]${agg['member_distribution_usd']:,.0f}[/bold green]\n[dim]To Members ({coop['revenue_split_pct']:.0f}%)[/dim]",
        f"[bold yellow]${agg['coop_fee_usd']:,.0f}[/bold yellow]\n[dim]Coop Fee ({coop['coop_fee_pct']:.0f}%)[/dim]",
    )
    console.print(Panel(rev_table, title="[bold]Revenue Distribution[/bold]", border_style="green"))


@app.command()
def satellite(farm: Optional[str] = typer.Option(None, "--farm", help="Farm ID for single fetch")):
    """Live NASA POWER NDVI proxy + vegetation status."""
    import asyncio
    from .feeds import fetch_satellite_for_farm, fetch_all_satellite

    sub = store.get_subscription()
    if not store.tier_allows(sub.tier.value, "satellite"):
        console.print(f"[red]Satellite monitoring requires Pro or Enterprise tier (current: {sub.tier.value}).[/red]")
        console.print("[dim]Run [bold]agroflow tier --set pro[/bold] to upgrade.[/dim]")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as prog:
        prog.add_task("Fetching NASA POWER vegetation data...", total=None)
        if farm:
            result = asyncio.run(fetch_satellite_for_farm(farm))
            if not result:
                console.print(f"[red]No data for farm '{farm}'.[/red]")
                raise typer.Exit(1)
            results = [result]
        else:
            results = asyncio.run(fetch_all_satellite())

    table = Table(title="Satellite Vegetation Monitoring (NASA POWER NDVI proxy)", show_lines=True)
    table.add_column("Farm", style="dim")
    table.add_column("Region")
    table.add_column("NDVI", justify="right")
    table.add_column("EVI", justify="right")
    table.add_column("Solar (MJ)", justify="right")
    table.add_column("Cloud %", justify="right")
    table.add_column("Status", justify="center")
    veg_color = {"excellent": "bold green", "good": "green", "fair": "yellow", "stressed": "yellow", "critical": "red"}
    for r in results:
        status = r.get("status", "unknown")
        color = veg_color.get(status, "white")
        ndvi = r.get("ndvi")
        evi = r.get("evi")
        rad = r.get("solar_radiation")
        cloud = r.get("cloud_cover_pct")
        table.add_row(
            r.get("farm_id", ""),
            r.get("region", ""),
            f"{ndvi:.2f}" if ndvi is not None else "-",
            f"{evi:.2f}" if evi is not None else "-",
            f"{rad:.1f}" if rad is not None else "-",
            f"{cloud:.0f}%" if cloud is not None else "-",
            f"[{color}]{status.upper()}[/{color}]",
        )
    console.print(table)


@app.command()
def phyto(
    cert_id: Optional[str] = typer.Option(None, "--cert", help="Certificate ID to inspect"),
    risk: bool = typer.Option(False, "--risk", help="Run rejection risk assessment"),
):
    """SENASICA → USDA APHIS phytosanitary compliance workflow."""
    from . import phyto as phyto_module

    sub = store.get_subscription()
    if not store.tier_allows(sub.tier.value, "phyto_compliance"):
        console.print(f"[red]Phytosanitary compliance requires Pro tier (current: {sub.tier.value}).[/red]")
        raise typer.Exit(1)

    if cert_id:
        cert = store.get_phyto_certificate(cert_id)
        if not cert:
            console.print(f"[red]Certificate '{cert_id}' not found.[/red]")
            raise typer.Exit(1)
        check = phyto_module.check_certificate(cert)
        status_color = {"draft": "dim", "submitted": "cyan", "inspection_scheduled": "cyan",
                        "approved": "green", "rejected": "red", "expired": "red"}
        sc = status_color.get(cert.status.value, "white")
        body = (
            f"[bold]Status:[/bold] [{sc}]{cert.status.value.upper()}[/{sc}]\n"
            f"[bold]Crop:[/bold] {CROP_EMOJI.get(cert.crop_type, cert.crop_type)}  |  "
            f"[bold]Destination:[/bold] {cert.destination}\n"
            f"[bold]SENASICA #:[/bold] {cert.senasica_cert_number or '[dim]not assigned[/dim]'}\n"
            f"[bold]APHIS ID:[/bold] {cert.aphis_inspection_id or '[dim]not assigned[/dim]'}\n"
            f"[bold]Issued:[/bold] {cert.issued_date or '-'}  |  [bold]Expires:[/bold] {cert.expiry_date or '-'}\n\n"
            f"[bold]Compliance:[/bold] {check['met_count']} / {check['total_requirements']} requirements met "
            f"([bold]{check['coverage_pct']:.0f}%[/bold])\n"
            f"[green]Met:[/green] {', '.join(check['met']) or '[dim]none[/dim]'}\n"
            f"[red]Missing:[/red] {', '.join(check['missing']) or '[dim]none[/dim]'}"
        )
        console.print(Panel(body, title=f"[bold]Phytosanitary Certificate {cert.id}[/bold]", border_style="cyan"))

        if risk:
            assessment = phyto_module.assess_rejection_risk(cert)
            level_color = {"very_low": "green", "low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}
            lc = level_color.get(assessment.risk_level.value, "white")
            risk_body = (
                f"[bold]Risk Level:[/bold] [{lc}]{assessment.risk_level.value.upper()}[/{lc}]  "
                f"(score {assessment.risk_score:.2f})\n"
                f"[bold]Estimated loss if rejected:[/bold] [red]${assessment.estimated_loss_usd:,.0f}[/red]\n\n"
                f"[bold]Risk factors:[/bold]\n"
                + "\n".join(f"  • {f}" for f in assessment.factors)
                + "\n\n[bold]Recommendations:[/bold]\n"
                + "\n".join(f"  • {r}" for r in assessment.recommendations[:6])
            )
            console.print(Panel(risk_body, title="[bold red]Rejection Risk Assessment[/bold red]", border_style="red"))
        return

    # No cert_id → list all
    items = store.list_phyto_certificates()
    if not items:
        _no_data()
    table = Table(title="Phytosanitary Certificates", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Farm")
    table.add_column("Crop")
    table.add_column("Destination")
    table.add_column("Status")
    table.add_column("SENASICA #")
    table.add_column("Coverage", justify="right")
    status_color = {"draft": "dim", "submitted": "cyan", "inspection_scheduled": "cyan",
                    "approved": "green", "rejected": "red", "expired": "red"}
    for c in items:
        check = phyto_module.check_certificate(c)
        sc = status_color.get(c.status.value, "white")
        table.add_row(
            c.id, c.farm_id,
            CROP_EMOJI.get(c.crop_type, c.crop_type),
            c.destination,
            f"[{sc}]{c.status.value}[/{sc}]",
            c.senasica_cert_number or "-",
            f"{check['coverage_pct']:.0f}%",
        )
    console.print(table)
    console.print("\n[dim]Run [bold]agroflow phyto --cert phyto-001 --risk[/bold] for risk assessment.[/dim]")


@app.command()
def tier(
    set_tier: Optional[str] = typer.Option(None, "--set", help="Switch tier: starter | pro | enterprise"),
):
    """View or change the AgroFlow Premium subscription tier."""
    from .models import Subscription, SubscriptionTier

    if set_tier:
        if set_tier not in ("starter", "pro", "enterprise"):
            console.print(f"[red]Invalid tier '{set_tier}'. Use starter | pro | enterprise.[/red]")
            raise typer.Exit(1)
        sub = Subscription(
            tier=SubscriptionTier(set_tier),
            organization=store.get_subscription().organization,
            seats=store.get_subscription().seats,
            price_usd_monthly=store.TIER_PRICING.get(set_tier, 0.0),
            features=store.TIER_FEATURES.get(set_tier, []),
        )
        store.set_subscription(sub)
        console.print(f"[green]Subscription updated to [bold]{set_tier}[/bold] (${store.TIER_PRICING[set_tier]}/mo).[/green]")

    sub = store.get_subscription()
    table = Table(title="AgroFlow Premium Tiers", show_lines=True)
    table.add_column("Tier", style="bold")
    table.add_column("Price/mo", justify="right", style="green")
    table.add_column("Features", style="dim")
    table.add_column("Active", justify="center")
    for tier_name in ("starter", "pro", "enterprise"):
        feats = store.TIER_FEATURES.get(tier_name, [])
        active = "[bold green]✓[/bold green]" if tier_name == sub.tier.value else ""
        table.add_row(
            tier_name.capitalize(),
            f"${store.TIER_PRICING.get(tier_name, 0):.0f}",
            f"{len(feats)} features",
            active,
        )
    console.print(table)
    console.print(f"\n[bold]Current tier:[/bold] [bold green]{sub.tier.value}[/bold green]")
    console.print(f"[bold]Organization:[/bold] {sub.organization}")
    console.print(f"[bold]Features unlocked:[/bold] {', '.join(sub.features)}")


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
