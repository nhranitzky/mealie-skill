"""
Mealie CLI – main entry point.

Usage:
    mealie list        [--search …] [--category …] [--tag …] [--sort …]
    mealie detail      <slug-or-name>
    mealie search      <query>   [--category …] [--tag …] [--open]
    mealie import      <url>     [--tag …] [--open]
    mealie import-json <file>    [--tag …] [--open] [--dry-run]
    mealie random      [--category …] [--tag …] [--count N] [--open]
    mealie mealplan    show|add|remove|random
    mealie shopping    lists|show|add|recipe|clear
    mealie organizers  categories|tags|cookbooks|cookbook
    mealie stats

All commands support --json for machine-readable output.
Credentials are loaded from .env and never forwarded to any LLM.
"""

import click

from scripts.cmd_list       import list_recipes
from scripts.cmd_detail     import detail
from scripts.cmd_search     import search
from scripts.cmd_import     import import_url, import_json
from scripts.cmd_random     import random_recipe
from scripts.cmd_mealplan   import mealplan
from scripts.cmd_shopping   import shopping
from scripts.cmd_organizers import organizers
from scripts.cmd_stats      import stats


@click.group()
@click.version_option("1.0.0", prog_name="mealie")
def cli():
    """
    \b
    🍴  Mealie CLI – manage your self-hosted recipe server from the terminal.
    Credentials are read from .env and never shared.
    """


cli.add_command(list_recipes,  name="list")
cli.add_command(detail)
cli.add_command(search)
cli.add_command(import_url,    name="import")
cli.add_command(import_json,   name="import-json")
cli.add_command(random_recipe, name="random")
cli.add_command(mealplan)
cli.add_command(shopping)
cli.add_command(organizers)
cli.add_command(stats)

if __name__ == "__main__":
    cli()
