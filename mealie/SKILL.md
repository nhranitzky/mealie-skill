---
name: mealie
description: >
  Use this skill to interact with the self-hosted Mealie recipe server.
  Trigger when the user wants to search, list, or browse recipes, get details
  of a specific recipe, import a recipe from a URL or JSON file, get a random
  recipe suggestion, view recipe statistics, or browse categories, tags, and
  cookbooks.  
author: N.Hranitzky
license: MIT
required_environment_variables:
  - name: MEALIE_URL
    prompt: "Base URL of your Mealie instance"
    help: "Example: https://mealie.example.com"
    required_for: "All commands"
  - name: MEALIE_API_TOKEN
    prompt: "Mealie API token"
    help: "Create one in Mealie under Settings → API Tokens"
    required_for: "All commands"
metadata:
  hermes:
    tags: [mealie, recipes]
---

# mealie Skill

CLI interface to the self-hosted [Mealie](https://mealie.io) recipe server.

**Always pass `--output json`** so the output is machine-readable.

---

## List Recipes

Browse all recipes, optionally filtered by category or tag.

### Examples

```bash
# All recipes (default page size 25)
${HERMES_SKILL_DIR}/bin/mealie-cli list --output json

# Fetch every recipe at once
${HERMES_SKILL_DIR}/bin/mealie-cli list --all --output json

# Filter by category
${HERMES_SKILL_DIR}/bin/mealie-cli list --category "Italian" --output json

# Filter by tag, sorted descending by name
${HERMES_SKILL_DIR}/bin/mealie-cli list --tag "vegan" --desc --output json

# Paginate manually
${HERMES_SKILL_DIR}/bin/mealie-cli list --page 2 --limit 10 --output json
```

---

## Search Recipes

Full-text search across all recipes.

### Examples

```bash
# Simple search
${HERMES_SKILL_DIR}/bin/mealie-cli search "pasta" --output json

# Search within a category
${HERMES_SKILL_DIR}/bin/mealie-cli search "soup" --category "Asian" --output json

# Search with tag filter, limit results
${HERMES_SKILL_DIR}/bin/mealie-cli search "cake" --tag "dessert" --limit 5 --output json
```

---

## Recipe Detail

Show full details of a recipe (ingredients, steps, metadata). Accepts a slug or a partial name — if multiple matches are found, the CLI lists them.

### Examples

```bash
# By slug
${HERMES_SKILL_DIR}/bin/mealie-cli detail spaghetti-carbonara --output json

# By partial name (auto-resolves if unique)
${HERMES_SKILL_DIR}/bin/mealie-cli detail "carbonara" --output json
```

---

## Import Recipe from URL

Scrape and import a recipe directly from a website URL.

### Examples

```bash
${HERMES_SKILL_DIR}/bin/mealie-cli import https://www.example.com/recipes/lasagne --output json

# Import and assign tags
${HERMES_SKILL_DIR}/bin/mealie-cli import https://www.example.com/recipes/lasagne --tag italian --tag pasta --output json
```

---

## Import Recipe from File

Import a recipe from a local `schema.org/Recipe` JSON file or an HTML file containing a `<script type="application/ld+json">` block.

### Examples

```bash
# From a JSON file
${HERMES_SKILL_DIR}/bin/mealie-cli import-json /tmp/recipe.json --output json

# From an HTML file saved locally
${HERMES_SKILL_DIR}/bin/mealie-cli import-json /tmp/recipe.html --tag homemade --output json
```

---

## Random Recipe

Pick one or more random recipes from the collection, optionally filtered.

### Examples

```bash
# One random recipe
${HERMES_SKILL_DIR}/bin/mealie-cli random --output json

# Three random recipes from a specific tag
${HERMES_SKILL_DIR}/bin/mealie-cli random --tag "quick" --count 3 --output json

# Random from a category
${HERMES_SKILL_DIR}/bin/mealie-cli random --category "Soup" --output json
```

---

## Statistics

Show an overview of the recipe collection: total counts, top categories, top tags, server version.

### Examples

```bash
${HERMES_SKILL_DIR}/bin/mealie-cli stats --output json

# Limit top-N lists
${HERMES_SKILL_DIR}/bin/mealie-cli stats --top 5 --output json
```

---

## Organizers

Browse categories, tags, and cookbooks.

### Examples

```bash
# List all categories
${HERMES_SKILL_DIR}/bin/mealie-cli organizers categories --output json

# List all tags
${HERMES_SKILL_DIR}/bin/mealie-cli organizers tags --output json

# List all cookbooks
${HERMES_SKILL_DIR}/bin/mealie-cli organizers cookbooks --output json

# Show recipes in a specific cookbook
${HERMES_SKILL_DIR}/bin/mealie-cli organizers cookbook my-favorites --output json
```

---

## Pitfalls

- **Missing env vars** — If `MEALIE_URL` or `MEALIE_API_TOKEN` is not set, the CLI exits immediately with an error. Never continue without both variables present.
- **Token format** — `MEALIE_API_TOKEN` must be a Bearer token created in Mealie under *Settings → API Tokens*. Do not use the login password.
- **Slug vs. name** — `detail` accepts a slug (e.g. `spaghetti-carbonara`) or a partial name. If the partial name matches multiple recipes, the CLI prompts interactively — in automated use always prefer the exact slug.
- **`--all` is slow** — `list --all` fetches every recipe page-by-page. On large collections this can take several seconds. Use `--search` or filters to narrow down first.
- **URL import may fail** — Not every website supports schema.org scraping. If `import` returns an error, save the page as HTML and use `import-json` instead.
- **JSON output only** — Always pass `--output json`. Without it, the CLI outputs rich-text tables that are not parseable.
