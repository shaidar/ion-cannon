# src/ion_cannon/main.py
import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskID

from ion_cannon.config.settings import settings
from ion_cannon.config.logging_config import setup_logging
from ion_cannon.core.collector import ContentCollector

# Initialize logging first
setup_logging()
logger = logging.getLogger("ion_cannon")

# Create Typer app
app = typer.Typer(
    name="ion_cannon",
    help="Multi-LLM Content Collection and Analysis System",
    add_completion=False,
)
console = Console()


async def run_collection(
    multi_llm: bool,
    output_dir: Optional[Path],
    verbose: bool,
) -> None:
    """Run the content collection and processing pipeline."""
    logger.info("Starting collection pipeline")
    collector = ContentCollector(use_multi_llm=multi_llm, verbose=verbose)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        # Setup progress tracking
        overall_task: TaskID = progress.add_task(
            "Running collection pipeline...", total=3
        )

        # Collection phase
        progress.update(overall_task, description="Collecting content...")
        content = await collector.collect()

        if not content:
            logger.warning("No content collected")
            console.print("[yellow]No content collected.")
            return

        progress.advance(overall_task)
        logger.info(f"Collected {len(content)} items")
        console.print(f"[green]Collected {len(content)} items")

        # Processing phase
        progress.update(overall_task, description="Processing content...")
        results = await collector.process_content(content)

        if not results:
            logger.warning("No relevant content found after processing")
            console.print("[yellow]No relevant content found after processing.")
            return

        progress.advance(overall_task)
        logger.info(f"Found {len(results)} relevant items")
        console.print(f"[green]Found {len(results)} relevant items")

        # Saving phase
        if output_dir:
            settings.OUTPUT_DIR = output_dir

        progress.update(overall_task, description="Saving results...")
        collector.save_results(results)
        progress.advance(overall_task)

    logger.info("Collection pipeline completed")


@app.command()
def collect(
    multi_llm: bool = typer.Option(
        False,
        "--multi-llm",
        "-m",
        help="Use multiple LLMs for content validation",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for collected content",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """Collect and analyze content from configured sources."""
    try:
        logger.info(f"Starting collection (multi_llm={multi_llm}, verbose={verbose})")
        asyncio.run(run_collection(multi_llm, output, verbose))
    except KeyboardInterrupt:
        logger.warning("Collection interrupted by user")
        console.print("\n[yellow]Collection interrupted by user")
        raise typer.Exit(130)
    except Exception as e:
        logger.error(f"Error during collection: {str(e)}", exc_info=True)
        console.print(f"[red]Error during collection: {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def sources(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show full source details",
    )
):
    """List configured content sources."""
    logger.info("Listing configured sources")
    if not settings.RSS_FEEDS and not settings.REDDIT_CHANNELS:
        console.print("[yellow]No sources configured.")
        return

    console.print("[bold]Configured Sources[/bold]")

    if settings.RSS_FEEDS:
        console.print("\n[cyan]RSS Feeds:[/cyan]")
        for feed in settings.RSS_FEEDS:
            if verbose:
                console.print(f"  {feed}")
        if not verbose:
            console.print(f"  {len(settings.RSS_FEEDS)} feeds configured")

    if settings.REDDIT_CHANNELS:
        console.print("\n[cyan]Reddit Channels:[/cyan]")
        for url in settings.REDDIT_CHANNELS:
            if verbose:
                console.print(f"  {url}")
        if not verbose:
            console.print(
                f"  {len(settings.REDDIT_CHANNELS)} reddit channels configured"
            )

    logger.info("Finished listing sources")


@app.command()
def version():
    """Show Ion Cannon version information."""
    from importlib.metadata import version as get_version

    try:
        version = get_version("ion_cannon")
    except:
        version = "dev"

    console.print(f"Ion Cannon v{version}")


if __name__ == "__main__":
    app()
