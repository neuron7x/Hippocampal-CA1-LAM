"""Unified service entrypoint for API and Neuro engine."""

import click
import uvicorn
import logging
from typing import Literal

from .utils.config_loader import get_settings, reload_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """MLSDM - Memory Learning System CLI."""
    pass


@cli.command()
@click.option(
    '--mode',
    type=click.Choice(['api', 'neuro'], case_sensitive=False),
    required=True,
    help='Service mode: api or neuro'
)
@click.option('--host', default=None, help='Server host (default: from config)')
@click.option('--port', type=int, default=None, help='Server port (default: from config)')
@click.option('--workers', type=int, default=None, help='Number of workers (default: from config)')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--log-level', default=None, help='Log level (default: from config)')
def serve(
    mode: str,
    host: str,
    port: int,
    workers: int,
    reload: bool,
    log_level: str
):
    """
    Start MLSDM service in specified mode.
    
    Examples:
        mlsdm serve --mode api
        mlsdm serve --mode neuro --port 8001
    """
    settings = get_settings()
    
    # Override settings from CLI if provided
    actual_host = host or settings.server.host
    actual_port = port or settings.server.port
    actual_workers = workers or settings.server.workers
    actual_reload = reload or settings.server.reload
    actual_log_level = log_level or settings.server.log_level
    
    if mode == 'api':
        logger.info(f"Starting MLSDM API service on {actual_host}:{actual_port}")
        app_str = "src.mlsdm.api.app:app"
    elif mode == 'neuro':
        logger.info(f"Starting MLSDM Neuro Engine on {actual_host}:{actual_port}")
        app_str = "src.mlsdm.service.neuro_engine_service:neuro_app"
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    uvicorn.run(
        app_str,
        host=actual_host,
        port=actual_port,
        workers=actual_workers if not actual_reload else 1,
        reload=actual_reload,
        log_level=actual_log_level.lower()
    )


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command('validate')
def config_validate():
    """Validate configuration."""
    try:
        settings = reload_settings()
        click.echo("✓ Configuration is valid")
        click.echo(f"  Environment: {settings.environment}")
        click.echo(f"  Auth mode: {settings.security.auth_mode}")
        click.echo(f"  Storage backend: {settings.storage.backend}")
    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        raise click.Abort()


@config.command('print-effective')
def config_print_effective():
    """Print effective configuration."""
    settings = get_settings()
    
    click.echo("Effective Configuration:")
    click.echo("=" * 50)
    click.echo(f"Environment: {settings.environment}")
    click.echo(f"Debug: {settings.debug}")
    click.echo()
    click.echo("Server:")
    click.echo(f"  Host: {settings.server.host}")
    click.echo(f"  Port: {settings.server.port}")
    click.echo(f"  Workers: {settings.server.workers}")
    click.echo(f"  Log Level: {settings.server.log_level}")
    click.echo()
    click.echo("Security:")
    click.echo(f"  Auth Mode: {settings.security.auth_mode}")
    click.echo(f"  mTLS Enabled: {settings.security.mtls_enabled}")
    click.echo()
    click.echo("Neuro Engine:")
    click.echo(f"  N Neurons: {settings.neuro.n_neurons}")
    click.echo(f"  Seed: {settings.neuro.seed}")
    click.echo(f"  dt: {settings.neuro.dt}")
    click.echo()
    click.echo("Storage:")
    click.echo(f"  Backend: {settings.storage.backend}")
    click.echo(f"  File Path: {settings.storage.file_path}")


@cli.command()
def version():
    """Show version information."""
    click.echo("MLSDM v1.0.0")
    click.echo("Hippocampal CA1 LAM - Memory Learning System")


def main():
    """Main entrypoint."""
    cli()


if __name__ == "__main__":
    main()
