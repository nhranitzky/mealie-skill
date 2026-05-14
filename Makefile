-include .env

SKILL_DIR  := mealie
SKILL_NAME := $(notdir $(abspath $(SKILL_DIR)))
VERSION    := 1.0.0
DIST_DIR   := dist
SKILL_ZIP  := $(DIST_DIR)/$(SKILL_NAME).skill_v$(VERSION).zip

HERMES_HOST         ?= pi@openclaw.local
HERMES_SKILL_REPO_DIR ?= /home/pi/downloads/skills

.PHONY: package to-repo clean help

package:          ## Build .skill zip into dist/
	mkdir -p $(DIST_DIR)
	zip -r $(SKILL_ZIP) $(SKILL_DIR)/ \
	  --exclude "*.venv*" \
	  --exclude "*.zip" \
	  --exclude "*/__pycache__/*" \
	  --exclude "*/.pytest_cache/*" \
	  --exclude "*.DS_Store" \
	  --exclude "*/uv.lock"
	@echo "Created: $(SKILL_ZIP)"

to-repo: package  ## Package and copy skill zip to remote HERMES_HOST:HERMES_SKILL_REPO_DIR
	scp $(SKILL_ZIP) $(HERMES_HOST):$(HERMES_SKILL_REPO_DIR)/
	@echo "Deployed to $(HERMES_HOST):$(HERMES_SKILL_REPO_DIR)/"

clean:            ## Remove build artifacts
	rm -rf $(DIST_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .venv -exec rm -rf {} +

help:             ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
