.PHONY: help format lint typecheck test build dist clean ci install-dev

help:
	@echo "HTML2exe Development Commands"
	@echo "  format     - Format code with ruff"
	@echo "  lint       - Lint code with ruff"
	@echo "  typecheck  - Type check with mypy"
	@echo "  test       - Run tests with pytest"
	@echo "  build      - Build EXE with PyInstaller"
	@echo "  dist       - Build NSIS installer"
	@echo "  ci         - Run all quality checks"
	@echo "  clean      - Clean build artifacts"

install-dev:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install

format:
	ruff format src tests
	ruff --fix src tests

lint:
	ruff check src tests

typecheck:
	mypy src

test:
	pytest -v

build:
	pyinstaller --clean --onefile --windowed --name HTML2exe --add-data "src/html2exe;html2exe" src/html2exe/__main__.py

dist: build
	makensis installer/installer.nsi

ci: format lint typecheck test
	@echo "All quality checks passed!"

clean:
	rm -rf build/ dist/ *.spec __pycache__ .pytest_cache .mypy_cache .coverage
	find . -name "*.pyc" -delete
