include .env

SKILL_DIR  := mealie	
SKILL_NAME := $(notdir $(abspath $(SKILL_DIR)))
VERSION=1.0
SKILL_ZIP_NAME := $(SKILL_NAME).skill_v$(VERSION).zip
 


.PHONY: install  lint package clean

install:          ## Install all dependencies (dev + skill)
	(cd $(SKILL_DIR) && uv sync)

 
lint:             ## Check code style
	uv run ruff check $(SKILL_DIR)/scripts

package:          ## Build .skill zip
	(cd $(dir $(abspath $(SKILL_DIR))) && \
	 zip -r $(SKILL_ZIP_NAME) $(SKILL_NAME)/ -x *.venv*  -x *.zip  -x "*/__pycache__/*"  -x .pytest_cache -x *.lock -x *.DS_Store) 
	@echo "Created: $(SKILL_ZIP_NAME)"

clean:            ## Remove build artifacts
	rm -f *.skill *.zip
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
 
	rm -rf $(SKILL_DIR)/.venv  
	rm $(SKILL_DIR)/uv.lock	

deploy:
	scp  ${SKILL_ZIP_NAME} ${TARGET}:${REMOTE_DOWNLOADS_DIR}
	  


help:             ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'