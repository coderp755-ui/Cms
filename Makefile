lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .

fix:
	ruff check --fix .
	ruff format .