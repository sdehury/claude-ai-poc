import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import Optional
import json
import os

from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(
    name="finsight",
    help="FinSight — Long-Term Investment Analysis Platform",
    add_completion=False,
)
console = Console()


def _score_color(score: float) -> str:
    if score >= 65:
        return "green"
    elif score >= 45:
        return "yellow"
    return "red"


def _score_emoji(score: float) -> str:
    if score >= 80:
        return "STRONG"
    elif score >= 65:
        return "GOOD"
    elif score >= 45:
        return "AVERAGE"
    elif score >= 30:
        return "WEAK"
    return "AVOID"


def _display_equity_report(report, quote_info=None):
    """Display equity analysis report in Rich formatted console output."""
    score = report.overall_score
    color = _score_color(score)
    fs = report.fundamental_score
    ts = report.technical_signals

    # Header
    header_lines = []
    header_lines.append(f"  [bold]{report.ticker}[/bold]")
    if report.executive_summary:
        header_lines.append(f"  {report.executive_summary}")
    console.print(Panel(
        "\n".join(header_lines),
        title="EQUITY ANALYSIS",
        border_style=color,
        box=box.DOUBLE,
    ))

    # Score breakdown table
    if fs:
        score_table = Table(
            title="Fundamental Score Breakdown",
            box=box.ROUNDED,
            show_header=True,
        )
        score_table.add_column("Category", style="bold")
        score_table.add_column("Score", justify="right")
        score_table.add_column("Weight", justify="right")

        categories = [
            ("Earnings Quality", fs.earnings_quality_score, "25%"),
            ("Balance Sheet", fs.balance_sheet_score, "20%"),
            ("Valuation", fs.valuation_score, "20%"),
            ("Competitive Moat", fs.moat_score, "20%"),
            ("Management", fs.management_score, "15%"),
        ]
        for name, cat_score, weight in categories:
            cat_color = _score_color(cat_score)
            score_table.add_row(
                name,
                f"[{cat_color}]{cat_score:.1f}/100[/{cat_color}]",
                weight,
            )
        score_table.add_row(
            "[bold]OVERALL[/bold]",
            f"[bold {color}]{score:.1f}/100 ({fs.rating})[/bold {color}]",
            "100%",
        )
        score_table.add_row(
            "Data Coverage",
            f"{fs.data_coverage_pct:.1f}%",
            "",
        )
        console.print(score_table)

    # Technical signals
    if ts:
        tech_table = Table(
            title="Technical Analysis",
            box=box.ROUNDED,
        )
        tech_table.add_column("Indicator", style="bold")
        tech_table.add_column("Value", justify="right")

        tech_table.add_row("CMP", f"Rs.{ts.cmp:,.2f}")
        tech_table.add_row("Trend", ts.trend)
        tech_table.add_row("Momentum", ts.momentum)
        if ts.rsi_14:
            tech_table.add_row("RSI (14)", f"{ts.rsi_14:.1f}")
        if ts.sma_50:
            tech_table.add_row("SMA 50", f"Rs.{ts.sma_50:,.2f}")
        if ts.sma_200:
            tech_table.add_row("SMA 200", f"Rs.{ts.sma_200:,.2f}")
        if ts.price_vs_200dma_pct is not None:
            tech_table.add_row("vs 200-DMA", f"{ts.price_vs_200dma_pct:+.1f}%")
        if ts.adx:
            tech_table.add_row("ADX", f"{ts.adx:.1f}")
        if ts.golden_cross:
            tech_table.add_row("Signal", "[bold green]GOLDEN CROSS[/bold green]")
        if ts.death_cross:
            tech_table.add_row("Signal", "[bold red]DEATH CROSS[/bold red]")
        console.print(tech_table)

        if ts.signals:
            console.print(Panel(
                "\n".join(f"  - {s}" for s in ts.signals),
                title="Technical Signals",
                border_style="cyan",
            ))

    # Recommendation
    console.print(Panel(
        f"  [bold]Recommendation:[/bold] {report.recommendation}\n"
        + (f"  [bold]Allocation:[/bold] {report.suggested_allocation_pct}\n" if report.suggested_allocation_pct else "")
        + (f"  [bold]5Y Target:[/bold] {report.target_5y}\n" if report.target_5y else "")
        + (f"  [bold]Entry Zones:[/bold] {', '.join(report.entry_zones)}\n" if report.entry_zones else ""),
        title="RECOMMENDATION",
        border_style="bold " + color,
    ))

    # Bull case
    if report.bull_case:
        console.print(Panel(
            "\n".join(f"  [green]+[/green] {p}" for p in report.bull_case),
            title="BULL CASE",
            border_style="green",
        ))

    # Bear case
    if report.bear_case:
        console.print(Panel(
            "\n".join(f"  [red]-[/red] {p}" for p in report.bear_case),
            title="BEAR CASE",
            border_style="red",
        ))

    # Red flags
    if report.red_flags:
        console.print(Panel(
            "\n".join(f"  [bold red]![/bold red] {f}" for f in report.red_flags),
            title="RED FLAGS",
            border_style="red",
        ))

    # Macro
    if report.macro_tailwinds or report.macro_headwinds:
        macro_lines = []
        for tw in report.macro_tailwinds:
            macro_lines.append(f"  [green]+[/green] {tw}")
        for hw in report.macro_headwinds:
            macro_lines.append(f"  [red]-[/red] {hw}")
        console.print(Panel(
            "\n".join(macro_lines),
            title="MACRO ENVIRONMENT",
            border_style="blue",
        ))

    # Disclaimer
    console.print(f"\n[dim]{report.disclaimer}[/dim]\n")


def _display_mf_report(result):
    """Display mutual fund analysis report."""
    color = _score_color(result.overall_score)
    returns = result.returns

    # Header
    console.print(Panel(
        f"  [bold]{result.scheme_name}[/bold]\n"
        f"  Scheme Code: {result.scheme_code}\n"
        f"  NAV: Rs.{result.latest_nav} (as of {result.nav_date})",
        title="MUTUAL FUND ANALYSIS",
        border_style=color,
        box=box.DOUBLE,
    ))

    # Returns table
    returns_table = Table(title="Returns", box=box.ROUNDED)
    returns_table.add_column("Period", style="bold")
    returns_table.add_column("Return", justify="right")

    if returns.return_1y is not None:
        returns_table.add_row("1 Year", f"{returns.return_1y:.2f}%")
    if returns.return_3y_cagr is not None:
        returns_table.add_row("3 Year CAGR", f"{returns.return_3y_cagr:.2f}%")
    if returns.return_5y_cagr is not None:
        returns_table.add_row("5 Year CAGR", f"{returns.return_5y_cagr:.2f}%")
    if returns.return_10y_cagr is not None:
        returns_table.add_row("10 Year CAGR", f"{returns.return_10y_cagr:.2f}%")
    console.print(returns_table)

    # Risk metrics table
    risk_table = Table(title="Risk Metrics", box=box.ROUNDED)
    risk_table.add_column("Metric", style="bold")
    risk_table.add_column("Value", justify="right")

    if result.sharpe_ratio is not None:
        risk_table.add_row("Sharpe Ratio", f"{result.sharpe_ratio:.3f}")
    if result.sortino_ratio is not None:
        risk_table.add_row("Sortino Ratio", f"{result.sortino_ratio:.3f}")
    if result.alpha is not None:
        risk_table.add_row("Alpha", f"{result.alpha:.2f}%")
    if result.beta is not None:
        risk_table.add_row("Beta", f"{result.beta:.3f}")
    if result.std_deviation is not None:
        risk_table.add_row("Std Deviation", f"{result.std_deviation:.2f}%")
    if result.max_drawdown is not None:
        risk_table.add_row("Max Drawdown", f"{result.max_drawdown:.2f}%")
    if result.max_drawdown_duration_days is not None:
        risk_table.add_row("Drawdown Duration", f"{result.max_drawdown_duration_days} days")

    console.print(risk_table)

    # Overall score
    console.print(Panel(
        f"  [bold]Score:[/bold] [{color}]{result.overall_score:.1f}/100 ({result.rating})[/{color}]",
        title="OVERALL ASSESSMENT",
        border_style=color,
    ))

    console.print(
        "\n[dim]This analysis is for educational and research purposes only. "
        "It does not constitute financial advice.[/dim]\n"
    )


@app.command()
def analyze_stock(
    symbols: list[str] = typer.Argument(help="Stock symbols (e.g., RELIANCE INFY TCS)"),
    skip_technical: bool = typer.Option(False, "--skip-technical", help="Skip technical analysis"),
    skip_advisory: bool = typer.Option(True, "--skip-advisory/--with-advisory", help="Skip LLM advisory (default: skip)"),
    output: str = typer.Option("console", "--output", "-o", help="Output format: console, json"),
):
    """Analyze Indian equity stocks with fundamental, technical, and sentiment scoring."""
    from finsight.orchestrator import Orchestrator

    orchestrator = Orchestrator(
        skip_advisory=skip_advisory,
        skip_technical=skip_technical,
    )

    reports = []
    for symbol in symbols:
        try:
            console.print(f"\n[bold cyan]Analyzing {symbol.upper()}...[/bold cyan]\n")
            report = orchestrator.analyze_equity(symbol)
            reports.append(report)

            if output == "json":
                console.print(report.model_dump_json(indent=2))
            else:
                _display_equity_report(report)

        except Exception as e:
            console.print(f"[bold red]Error analyzing {symbol}: {e}[/bold red]")

    # Portfolio summary if multiple stocks
    if len(reports) > 1:
        from finsight.advisory.portfolio_advisor import PortfolioAdvisor
        portfolio = PortfolioAdvisor.analyze_portfolio(reports)

        console.print(Panel(
            f"  Positions: {portfolio['num_positions']}\n"
            f"  Portfolio Score: {portfolio['portfolio_score']}/100\n"
            f"  Strong: {portfolio['score_distribution']['strong']} | "
            f"Average: {portfolio['score_distribution']['average']} | "
            f"Weak: {portfolio['score_distribution']['weak']}",
            title="PORTFOLIO SUMMARY",
            border_style="bold blue",
            box=box.DOUBLE,
        ))

        if portfolio.get("recommendations"):
            for rec in portfolio["recommendations"]:
                console.print(f"  [cyan]>[/cyan] {rec}")

    orchestrator.close()


@app.command()
def analyze_mf(
    scheme_codes: list[str] = typer.Argument(help="AMFI scheme codes (e.g., 122639 119598)"),
    benchmark: str = typer.Option("^NSEI", "--benchmark", "-b", help="Benchmark ticker"),
    output: str = typer.Option("console", "--output", "-o", help="Output format: console, json"),
):
    """Analyze mutual funds with risk-return metrics and scoring."""
    from finsight.orchestrator import Orchestrator

    orchestrator = Orchestrator(skip_advisory=True)

    for code in scheme_codes:
        try:
            console.print(f"\n[bold cyan]Analyzing scheme {code}...[/bold cyan]\n")
            result = orchestrator.analyze_mf(code, benchmark)

            if output == "json":
                console.print(result.model_dump_json(indent=2))
            else:
                _display_mf_report(result)

        except Exception as e:
            console.print(f"[bold red]Error analyzing scheme {code}: {e}[/bold red]")

    orchestrator.close()


@app.command()
def search_mf(
    query: str = typer.Argument(help="Search query (e.g., 'parag parikh')"),
):
    """Search for mutual fund schemes by name."""
    from finsight.orchestrator import Orchestrator

    orchestrator = Orchestrator(skip_advisory=True)

    try:
        results = orchestrator.search_mf(query)

        if not results:
            console.print("[yellow]No schemes found.[/yellow]")
            return

        table = Table(title=f"MF Schemes matching '{query}'", box=box.ROUNDED)
        table.add_column("Scheme Code", style="bold cyan")
        table.add_column("Scheme Name")

        for scheme in results[:30]:
            table.add_row(scheme["code"], scheme["name"])

        console.print(table)
        console.print(f"\n[dim]Found {len(results)} schemes. Showing top 30.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error searching: {e}[/bold red]")

    orchestrator.close()


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of records"),
):
    """Show past analysis history."""
    from finsight.storage.db import Database
    db = Database()

    records = db.list_analyses(limit)

    if not records:
        console.print("[yellow]No analysis history found.[/yellow]")
        return

    table = Table(title="Analysis History", box=box.ROUNDED)
    table.add_column("Symbol", style="bold")
    table.add_column("Type")
    table.add_column("Date")
    table.add_column("Score", justify="right")
    table.add_column("Recommendation")

    for r in records:
        color = _score_color(r["score"]) if r["score"] else "white"
        table.add_row(
            r["symbol"],
            r["asset_type"],
            r["date"][:10] if r["date"] else "N/A",
            f"[{color}]{r['score']:.1f}[/{color}]" if r["score"] else "N/A",
            r["recommendation"] or "N/A",
        )

    console.print(table)


if __name__ == "__main__":
    app()
