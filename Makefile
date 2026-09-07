.PHONY: install lint test all

install:
	uv sync

lint:
	uv run ruff check .
	uv run mypy --strict src/

test:
	@uv run pytest; code=$$?; \
	if [ "$$code" -eq 5 ]; then \
	  echo "Empty suite: no tests collected (pytest exit 5); no tests passed."; \
	elif [ "$$code" -ne 0 ]; then \
	  exit "$$code"; \
	fi

all:
	$(MAKE) lint
	$(MAKE) test
