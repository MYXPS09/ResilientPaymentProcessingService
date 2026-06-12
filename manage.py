import logging
import subprocess  # nosec
import sys

import typer
import uvicorn

cmd = typer.Typer(no_args_is_help=True)

# setup loggers
logging.basicConfig(level=logging.INFO, format="%(levelname)-5.5s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

@cmd.command(name="run")
def run():
    """Run application"""
    uvicorn.run(
        app="main:app", reload=True, port=8000, host="0.0.0.0"
    )
    logger.info("App is Starting...")

@cmd.command(name="run_worker")
def run_worker():
    """Run celery worker"""
    logger.info("Starting Celery Worker...")
    process = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "celery_app.celery_app", "worker", "--loglevel=info", "-P", "solo"],
        shell=False,
    )  # nosec
    process.communicate()

@cmd.command(name="migrate-dev")
def migrate_dev():
    """Run migrations for DEVELOPMENT environment"""
    config_file = "alembic.ini"
    logger.info(f"Running DEV migrations using {config_file}")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", config_file, "upgrade", "head"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )  # nosec
    
    stdout, stderr = process.communicate()
    if stdout:
        logger.info(stdout.decode())
    if stderr:
        logger.error(stderr.decode())
    
    if process.returncode != 0:
        raise Exception(f"Migration failed with exit code {process.returncode}")

@cmd.command(name="makemigrations-dev")
def makemigrations_dev(
    msg: str = typer.Option("autogenerate", "--msg", "-m", help="Migration message")
):
    """Create new migration for DEVELOPMENT environment"""
    config_file = "alembic.ini"
    logger.info(f"Creating DEV migration using {config_file}")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", config_file, "revision", "--autogenerate", "-m", msg],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )  # nosec
    
    stdout, stderr = process.communicate()
    if stdout:
        logger.info(stdout.decode())
    if stderr:
        logger.error(stderr.decode())
    
    if process.returncode != 0:
        raise Exception(f"Migration creation failed with exit code {process.returncode}")

@cmd.command(name="downgrade-dev")
def downgrade_dev(
    revision: str = typer.Option("-1", "--revision", "-r", help="Revision to downgrade to")
):
    """Downgrade DEVELOPMENT migrations"""
    config_file = "alembic.ini"
    logger.info(f"Downgrading DEV to revision {revision}")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", config_file, "downgrade", revision],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )  # nosec
    
    stdout, stderr = process.communicate()
    if stdout:
        logger.info(stdout.decode())
    if stderr:
        logger.error(stderr.decode())
    
    if process.returncode != 0:
        raise Exception(f"Downgrade failed with exit code {process.returncode}")

@cmd.command(name="history")
def migration_history():
    """Show migration history"""
    config_file = "alembic.ini"
    logger.info(f"Showing migration history")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", config_file, "history"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )  # nosec
    
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout.decode())
    if stderr:
        logger.error(stderr.decode())

@cmd.command(name="current")
def migration_current():
    """Show current migration revision"""
    config_file = "alembic.ini"
    logger.info(f"Showing current revision")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "alembic", "-c", config_file, "current"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )  # nosec
    
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout.decode())
    if stderr:
        logger.error(stderr.decode())

if __name__ == "__main__":
    cmd()
