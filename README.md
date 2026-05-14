# Mealie Skill for Hermes

Use this skill to interact with the self-hosted  [Mealie](https://mealie.io)  recipe server. Trigger when the user wants to search, list, or browse recipes, get details of a specific recipe, import a recipe from a URL or JSON file, get a random recipe suggestion, view recipe statistics, or browse categories, tags, and cookbooks.  

## Installation

### Managed skill directory (via Hermes CLI)

```bash
hermes skills install nhranitzky/mealie-skill/mealie
```

> **Note:** The installation will be blocked by default:
> ```
> Installation blocked: Blocked (community source + caution verdict, 2 findings).
> Use --force to override.
> ```
> This is expected — the skill requires environment variables with sensitive values (`MEALIE_URL`, `MEALIE_API_TOKEN`).
> Review the source code, then install with:

```bash
hermes skills install nhranitzky/mealie-skill/mealie --force
```

### Custom directory (skills.external_dirs)

```bash
git clone https://github.com/nhranitzky/mealie-skill.git
cd mealie-skill
./install.sh /path/to/target   # installs into /path/to/target/mealie/
```

The install script will warn and ask for confirmation if the target already contains files.

## Configuration

Add the following variables to your Hermes `.env` file:

```dotenv
MEALIE_URL=https://mealie.example.com   # base URL of your Mealie instance (no trailing slash)
MEALIE_API_TOKEN=<your-api-token>        # create one in Mealie: Settings → API Tokens
```

## License

MIT
