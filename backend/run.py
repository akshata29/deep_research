#!/usr/bin/env python3
"""
Development server runner for Deep Research backend.
This script provides convenient development utilities and server management.
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import click
import uvicorn


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
APP_MODULE = "app.main:app"


def check_python_version():
    """Check if Python version meets requirements."""
    if sys.version_info < (3, 11):
        click.echo(click.style(
            "Error: Python 3.11 or higher is required", 
            fg="red"
        ))
        sys.exit(1)


def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        click.echo(click.style(
            f"Warning: Missing environment variables: {', '.join(missing_vars)}", 
            fg="yellow"
        ))
        click.echo("Please check your .env file or environment configuration.")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    click.echo("Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, cwd=PROJECT_ROOT)
        click.echo(click.style("Dependencies installed successfully", fg="green"))
        return True
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Failed to install dependencies: {e}", fg="red"))
        return False


def run_tests():
    """Run the test suite."""
    click.echo("Running tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "-v", "--tb=short"
        ], cwd=PROJECT_ROOT)
        return result.returncode == 0
    except FileNotFoundError:
        click.echo(click.style("pytest not found. Installing test dependencies...", fg="yellow"))
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "httpx"
        ], cwd=PROJECT_ROOT)
        return run_tests()


def check_azure_cli():
    """Check if Azure CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["az", "account", "show"], 
            capture_output=True, 
            text=True,
            check=True
        )
        click.echo(click.style("Azure CLI authentication verified", fg="green"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo(click.style(
            "Azure CLI not found or not authenticated. Please run 'az login'", 
            fg="yellow"
        ))
        return False


@click.group()
def cli():
    """Deep Research Backend Development Tools."""
    check_python_version()


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8010, help="Port to bind to")
@click.option("--reload", is_flag=True, default=True, help="Enable auto-reload")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--check-env/--no-check-env", default=True, help="Check environment variables")
def serve(host: str, port: int, reload: bool, debug: bool, workers: int, check_env: bool):
    """Start the development server."""
    if check_env:
        env_ok = check_environment()
        if not env_ok:
            click.echo("Consider using --no-check-env to skip environment checks.")
    
    # Set debug environment variable
    if debug:
        os.environ["DEBUG"] = "true"
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    click.echo(f"Starting server at http://{host}:{port}")
    click.echo(f"API Documentation: http://{host}:{port}/docs")
    click.echo(f"Health Check: http://{host}:{port}/api/v1/health/")
    
    uvicorn.run(
        APP_MODULE,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        access_log=debug,
        log_level="debug" if debug else "info"
    )


@cli.command()
def setup():
    """Set up the development environment."""
    click.echo("Setting up Deep Research backend development environment...")
    
    # Check environment file
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        example_file = PROJECT_ROOT / ".env.example"
        if example_file.exists():
            click.echo("Copying .env.example to .env...")
            with open(example_file) as src, open(env_file, "w") as dst:
                dst.write(src.read())
            click.echo(click.style(
                "Please update .env with your Azure configuration", 
                fg="yellow"
            ))
        else:
            click.echo(click.style("No .env.example found", fg="red"))
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check Azure CLI
    check_azure_cli()
    
    click.echo(click.style("Setup completed!", fg="green"))
    click.echo("Run 'python run.py serve' to start the development server")


@cli.command()
@click.option("--coverage", is_flag=True, help="Run with coverage report")
@click.option("--watch", is_flag=True, help="Watch for file changes")
def test(coverage: bool, watch: bool):
    """Run the test suite."""
    cmd = [sys.executable, "-m", "pytest", "-v"]
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    if watch:
        cmd.append("--looponfail")
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)


@cli.command()
def lint():
    """Run code linting."""
    click.echo("Running code linting...")
    
    # Try to run black (formatter)
    try:
        subprocess.run([
            sys.executable, "-m", "black", "--check", "app/", "tests/"
        ], cwd=PROJECT_ROOT, check=True)
        click.echo(click.style("Code formatting: PASSED", fg="green"))
    except subprocess.CalledProcessError:
        click.echo(click.style("Code formatting: FAILED", fg="red"))
        click.echo("Run 'python -m black app/ tests/' to fix formatting")
    except FileNotFoundError:
        click.echo(click.style("black not found, skipping formatting check", fg="yellow"))
    
    # Try to run flake8 (linter)
    try:
        subprocess.run([
            sys.executable, "-m", "flake8", "app/", "tests/"
        ], cwd=PROJECT_ROOT, check=True)
        click.echo(click.style("Code linting: PASSED", fg="green"))
    except subprocess.CalledProcessError:
        click.echo(click.style("Code linting: FAILED", fg="red"))
    except FileNotFoundError:
        click.echo(click.style("flake8 not found, skipping linting", fg="yellow"))


@cli.command()
def health():
    """Check application health and dependencies."""
    click.echo("Checking application health...")
    
    # Check Python version
    click.echo(f"Python version: {sys.version}")
    
    # Check environment
    env_status = check_environment()
    
    # Check Azure CLI
    azure_status = check_azure_cli()
    
    # Try to import main modules
    try:
        from app.main import app
        click.echo(click.style("Application imports: OK", fg="green"))
    except ImportError as e:
        click.echo(click.style(f"Application imports: FAILED - {e}", fg="red"))
    
    # Check if server is running
    try:
        import httpx
        response = httpx.get("http://localhost:8010/api/v1/health/", timeout=5)
        if response.status_code == 200:
            click.echo(click.style("Server health: RUNNING", fg="green"))
        else:
            click.echo(click.style(f"Server health: ERROR ({response.status_code})", fg="red"))
    except ImportError:
        click.echo(click.style("httpx not available for health check", fg="yellow"))
    except Exception:
        click.echo(click.style("Server health: NOT RUNNING", fg="yellow"))
    
    # Summary
    if env_status and azure_status:
        click.echo(click.style("Overall status: READY", fg="green"))
    else:
        click.echo(click.style("Overall status: NEEDS ATTENTION", fg="yellow"))


@cli.command()
@click.argument("command", required=False)
def docker(command: Optional[str]):
    """Docker operations."""
    if not command:
        click.echo("Available docker commands:")
        click.echo("  build    - Build Docker image")
        click.echo("  run      - Run Docker container")
        click.echo("  stop     - Stop running container")
        click.echo("  logs     - Show container logs")
        return
    
    image_name = "deep-research-backend"
    container_name = "deep-research-backend-dev"
    
    if command == "build":
        click.echo("Building Docker image...")
        subprocess.run([
            "docker", "build", "-t", image_name, "."
        ], cwd=PROJECT_ROOT)
    
    elif command == "run":
        click.echo("Running Docker container...")
        env_args = []
        if os.path.exists(".env"):
            env_args = ["--env-file", ".env"]
        
        subprocess.run([
            "docker", "run", "--name", container_name, "-p", "8010:8010",
            "--rm", "-d"
        ] + env_args + [image_name])
        click.echo(f"Container running at http://localhost:8010")
    
    elif command == "stop":
        click.echo("Stopping Docker container...")
        subprocess.run(["docker", "stop", container_name])
    
    elif command == "logs":
        subprocess.run(["docker", "logs", "-f", container_name])
    
    else:
        click.echo(f"Unknown docker command: {command}")


@cli.command()
def clean():
    """Clean up temporary files and caches."""
    click.echo("Cleaning up...")
    
    # Python cache files
    for pattern in ["**/__pycache__", "**/*.pyc", "**/*.pyo"]:
        for path in PROJECT_ROOT.glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
    
    # Coverage files
    for pattern in [".coverage", "htmlcov", ".pytest_cache"]:
        path = PROJECT_ROOT / pattern
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                import shutil
                shutil.rmtree(path)
    
    click.echo(click.style("Cleanup completed", fg="green"))


if __name__ == "__main__":
    cli()
