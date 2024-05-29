from pathlib import Path

import yaml
from dotenv import load_dotenv
from sqltest.models import Config
from sqltest.runner import TestRunner
import click

load_dotenv(Path.cwd().absolute() / ".env")


@click.group()
@click.option("-C", "--config", default="sqltest.yml")
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    config_path = Path(config)
    if config_path.exists():
        ctx.obj["CONFIG"] = Config.from_yaml(config)


@cli.command()
@click.pass_context
@click.argument("models", nargs=-1)
def test(ctx, models: str | tuple[str]):
    runner = TestRunner(ctx.obj["CONFIG"])
    if models:
        runner.run(models)
    else:
        runner.run()


@cli.command()
def init():
    """Initialize a sql test project configuration file"""
    config_file = Path("sqltest.yml")
    if config_file.exists():
        print(f"A {config_file.name} config file already exists for this project")
        exit()

    print("Enter a data source name:")
    source_name = input("> ")
    print(
        "Enter a SQLAlchemy connection string or "
        "env variable containing the url for the data source:"
    )
    source_url = input("> ")

    models_dir = "models"

    config = {
        "source": {"name": source_name, "url": source_url},
        "models_dir": models_dir,
    }

    with config_file.open("w") as f:
        yaml.dump(config, f)

    print(f"Created `{config_file.name}`")
    print("Happy testing!")


@cli.command()
@click.pass_context
def debug(ctx):
    config = ctx.obj["CONFIG"]
    runner = TestRunner(config)

    print(f"Testing connection to {config.source.name} ({runner.engine.url})")
    try:
        runner.check_source()
    except Exception as e:
        print(e)
    else:
        print("Connection is working")


if __name__ == "__main__":
    cli()
