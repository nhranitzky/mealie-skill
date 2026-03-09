# Mealie CLI

Manage your self-hosted [Mealie](https://mealie.io) recipe server from the terminal.

List, search, and display recipes; import recipes from any website URL;
manage your meal plan and shopping lists; browse categories and cookbooks –
all without opening a browser.

---

## Requirements

| Tool | Version | Install |
|------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | ≥ 0.4 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python | ≥ 3.11 | managed automatically by `uv` |
| Mealie server | ≥ v1.0 | [docs.mealie.io](https://docs.mealie.io) |

---

## Getting a Mealie API Token

1. Log in to your Mealie instance.
2. Go to **Settings → API Tokens** (or your profile → API Tokens).
3. Click **"Generate API Token"**, give it a name, and copy the token.

---

## Installation for standalone usage

### 1 – Get the project

```bash
git clone https://github.com/your-org/mealie-skill.git
cd mealie-skill/mealie
```

### 2 – Configure credentials

```
MEALIE_URL=http://192.168.1.100:9000
MEALIE_API_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6...
```

## Usage

### List recipes

```bash
# All recipes, sorted by name
mealie list

# Filter and sort
mealie list --category "Suppen" --sort rating --desc
mealie list --tag schnell --limit 10
mealie list --all --json

# Search while listing
mealie list --search "Hähnchen"
```

### View a recipe

```bash
mealie detail pasta-carbonara
mealie detail "Chicken Soup"      # partial name search
mealie detail carbonara --json
```

### Search recipes

```bash
mealie search pasta
mealie search "Tomatensuppe" --category Suppen
mealie search risotto --tag veggie --open   # open detail if 1 result
```

### Import from a website

```bash
# Single URL
mealie import https://www.chefkoch.de/rezepte/12345/Spaghetti.html
mealie import https://example.com/recipe --tag Italian --tag Pasta
mealie import https://example.com/recipe --open   # show detail after import
```

### Import from a schema.org/Recipe JSON file

Accepts `.json`, `.jsonld`, and `.html` files.
Supported input shapes:

| Shape | Example |
|-------|---------|
| Single recipe | `{ "@type": "Recipe", "name": "...", ... }` |
| Array of recipes | `[ { "@type": "Recipe", ... }, ... ]` |
| JSON-LD `@graph` | `{ "@graph": [ { "@type": "Recipe", ... } ] }` |
| HTML with ld+json | any `.html` file – all `<script type="application/ld+json">` blocks are scanned |

Fields mapped from schema.org → Mealie:

| schema.org | Mealie field |
|-----------|--------------|
| `name` | name |
| `description` | description |
| `recipeYield` | recipeYield |
| `prepTime` / `cookTime` / `totalTime` | prepTime / cookTime / totalTime (ISO 8601) |
| `recipeIngredient` | recipeIngredient (as free-text notes) |
| `recipeInstructions` (strings, HowToStep, HowToSection) | recipeInstructions |
| `recipeCategory` | recipeCategory |
| `keywords` | tags |
| `nutrition` | nutrition |
| `author` | notes (Author) |
| `url` / `mainEntityOfPage` | orgURL |
| `image` | image |

```bash
# Import a single recipe
mealie import-json recipe.json

# Import multiple recipes, add a tag
mealie import-json recipes.jsonld --tag Imported

# Preview what would be imported (nothing sent to Mealie)
mealie import-json export.json --dry-run

# Import from a saved HTML page
mealie import-json page.html --tag WebImport

# Show full detail after import + JSON output
mealie import-json recipe.json --open --json
```

### Random recipe

```bash
mealie random
mealie random --category Italian --count 3
mealie random --tag quick --open
```

### Meal plan

```bash
# View current week
mealie mealplan show

# Custom date range
mealie mealplan show --start 2024-06-01 --end 2024-06-14

# Add a recipe
mealie mealplan add 2024-06-10 pasta-carbonara
mealie mealplan add 2024-06-11 chicken-soup --type lunch

# Add a random recipe
mealie mealplan random 2024-06-12 --type dinner

# Remove an entry (get ID from `mealie mealplan show`)
mealie mealplan remove 42
```

### Shopping lists

```bash
# List all shopping lists
mealie shopping lists

# View items
mealie shopping show <list-id>
mealie shopping show <list-id> --checked   # include completed items

# Add a free-text item
mealie shopping add <list-id> "Olive oil"
mealie shopping add <list-id> Milk --qty 2 --unit litre

# Add all ingredients of a recipe
mealie shopping recipe <list-id> spaghetti-bolognese
mealie shopping recipe <list-id> pasta-carbonara --servings 6

# Clean up
mealie shopping clear <list-id>          # remove checked items
mealie shopping clear <list-id> --all    # remove everything
```

### Browse organizers

```bash
mealie organizers categories
mealie organizers tags
mealie organizers cookbooks
mealie organizers cookbook italian-favourites
```

### Statistics

```bash
mealie stats
mealie stats --json
```

---

## JSON Output

Every command supports `--json` for machine-readable output (useful for
scripting or piping to `jq`):

```bash
mealie search pasta --json | jq '.[0] | {name, slug, tags: [.tags[].name]}'
mealie mealplan show --json | jq '.[] | {date, type: .entryType, recipe: .recipe.name}'
```

---

## Meal Types

| Code | Description |
|------|-------------|
| `breakfast` | Breakfast |
| `lunch` | Lunch |
| `dinner` | Dinner (default) |
| `snack` | Snack |

---
## Installation in Openclaw as Skill

* Create a zip and unzip in the skill folder (managed or workspace) as `mealie`.

### 1– Install dependencies

```bash
cd mealie
bash install-skill.sh
```

The script installs Python dependencies via `uv sync` and verifies that `MEALIE_URL` and `MEALIE_API_TOKEN` are present in `$HOME/.openclaw/.env`.
  


### 2 – Configure credentials

Set the required variables in `$HOME/.openclaw/.env`:

```
MEALIE_URL=http://192.168.1.100:9000
MEALIE_API_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6...
```

## Project Structure

```
mealie-skill/
├── Makefile              ← build/deploy automation
├── README.md             ← this file
└── mealie/               ← skill package
    ├── SKILL.md          ← Openclaw skill metadata
    ├── pyproject.toml    ← uv/Python project config
    ├── install-skill.sh  ← dependency installer + env checker
    ├── bin/
    │   └── mealie        ← shell launcher
    └── scripts/
        ├── main.py           ← CLI entry point
        ├── utils.py          ← MealieClient + shared helpers
        ├── cmd_list.py       ← `mealie list`
        ├── cmd_detail.py     ← `mealie detail`
        ├── cmd_search.py     ← `mealie search`
        ├── cmd_import.py     ← `mealie import` / `import-json`
        ├── cmd_random.py     ← `mealie random`
        ├── cmd_mealplan.py   ← `mealie mealplan`
        ├── cmd_shopping.py   ← `mealie shopping`
        ├── cmd_organizers.py ← `mealie organizers`
        └── cmd_stats.py      ← `mealie stats`
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Missing configuration` | Set `MEALIE_URL` and `MEALIE_API_TOKEN` in `$HOME/.openclaw/.env` |
| `HTTP 401` | Token is invalid or expired – generate a new one in Mealie |
| `HTTP 404` | Wrong slug; use `mealie search <name>` to find the correct slug |
| `Network error` | Check that your Mealie server is running and reachable |
| `command not found: mealie` | Check PATH or run `./bin/mealie` from the project root |
| Import fails | The website may not be supported by Mealie's scraper |

---

## Supported Recipe Import Sites

Mealie uses the [recipe-scrapers](https://github.com/hhursev/recipe-scrapers)
library. Hundreds of sites are supported including: Chefkoch, Allrecipes,
BBC Good Food, Serious Eats, NYT Cooking, Taste of Home, and many more.
See the full list at: https://github.com/hhursev/recipe-scrapers#scrapers-available-for

---

## Development Notes
Parts of this codebase were generated or assisted by Claude Code  Sonnet 4.6  
All generated code has been reviewed and tested by human developers.

## License

MIT
