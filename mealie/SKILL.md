---
name: mealie
description: Interact with a self-hosted Mealie recipe server via its REST API. Use this skill whenever the user wants to list, search, or browse recipes; view a specific recipe (ingredients, instructions, metadata); import a recipe from a website URL; manage the meal plan (view, add, remove entries); manage shopping lists (view, add items, link recipes); or browse categories, tags, and cookbooks.
licence: MIT
metadata: { "openclaw": {"emoji": "🍽️" } }
---

# Mealie Skill

Manage a self-hosted [Mealie](https://mealie.io) instance from the terminal.

## ⚠️ Credential Security

The URL and Token are provided by the environment as environment variables.
Openclaw must **never** display, log, or relay these values. They flow only:
`env → Python process → Mealie HTTPS request`.

## Available Commands

| Command | User asks |
|---------|-------------|
| `{baseDir}/bin/mealie list` | List recipes with filtering and sorting |
| `{baseDir}/bin/mealie detail <slug>` | Full recipe: ingredients, instructions, metadata |
| `{baseDir}/bin/mealie search <query>` | Full-text search with optional category/tag filters |
| `{baseDir}/bin/mealie import <url>` | Scrape & import a recipe from any supported website |
| `{baseDir}/bin/mealie import-json <file>` | Import one or more recipes from a schema.org/Recipe JSON file |
| `{baseDir}/bin/mealie random` | Random recipe suggestion from the collection |
| `{baseDir}/bin/mealie mealplan show` | Display the current week's meal plan |
| `{baseDir}/bin/mealie mealplan add <date> <slug>` | Add a recipe to the meal plan |
| `{baseDir}/bin/mealie mealplan remove <entry-id>` | Remove a meal plan entry |
| `{baseDir}/bin/mealie mealplan random <date>` | Insert a random recipe into the meal plan |
| `{baseDir}/bin/mealie shopping lists` | Show all shopping lists |
| `{baseDir}/bin/mealie shopping show <list-id>` | Show items in a shopping list |
| `{baseDir}/bin/mealie shopping add <list-id> <item>` | Add a text item |
| `{baseDir}/bin/mealie shopping recipe <list-id> <slug>` | Add all ingredients of a recipe |
| `{baseDir}/bin/mealie shopping check <item-id>` | Toggle an item's checked state |
| `{baseDir}/bin/mealie shopping clear <list-id>` | Remove checked (or all) items |
| `{baseDir}/bin/mealie organizers categories` | List all categories |
| `{baseDir}/bin/mealie organizers tags` | List all tags |
| `{baseDir}/bin/mealie organizers cookbooks` | List all cookbooks |
| `{baseDir}/bin/mealie organizers cookbook <slug>` | Show recipes in a cookbook |
| `{baseDir}/bin/mealie stats` | Collection statistics + server version |

All commands support `--json` for machine-readable output.

## Key Common Options

| Option | Description |
|--------|-------------|
| `--json` | Emit sanitised JSON (no tokens) instead of Rich tables |
| `--category / -c` | Filter by category name |
| `--tag / -t` | Filter by tag name |
| `--limit / -n` | Max rows to return |
| `--open / -o` | Auto-open full detail for a single result |

## Example Invocations

```bash
# Browse & search
{baseDir}/bin/mealie list --category "Suppen" --sort rating --desc
{baseDir}/bin/mealie search "Pasta" --tag schnell --open
{baseDir}/bin/mealie detail carbonara

# Import
{baseDir}/bin/mealie import https://www.chefkoch.de/rezepte/123/Spaghetti.html --tag Italian
{baseDir}/bin/mealie import https://example.com/recipe --open
{baseDir}/bin/mealie import-json recipe.json --tag Imported --open
{baseDir}/bin/mealie import-json export.jsonld --dry-run
{baseDir}/bin/mealie import-json page.html --json

# Meal planning
{baseDir}/bin/mealie mealplan show
{baseDir}/bin/mealie mealplan add 2024-06-10 pasta-carbonara --type dinner
{baseDir}/bin/mealie mealplan random 2024-06-11 --type lunch

# Shopping lists
{baseDir}/bin/mealie shopping lists
{baseDir}/bin/mealie shopping show <list-id>
{baseDir}/bin/mealie shopping recipe <list-id> spaghetti-bolognese
{baseDir}/bin/mealie shopping add <list-id> "Olive oil" --qty 1 --unit bottle

# Discovery
{baseDir}/bin/mealie random --category Italian --count 3
{baseDir}/bin/mealie organizers categories
{baseDir}/bin/mealie stats
```

## How Openclaw Should Use This Skill

1. Identify the intent: list / search / detail / import / meal plan / shopping / organizers.
2. Extract parameters (query, slug, URL, date, list ID) from the user's message.
3. Run the appropriate `{baseDir}/bin/mealie` command.
4. **Never reveal** `MEALIE_URL` or `MEALIE_API_TOKEN` in any response.
5. Summarise the output; for `--json` responses, extract key fields.
