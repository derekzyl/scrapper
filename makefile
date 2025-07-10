.PHONY: install run clean test lint format help

# Default target
help:
	@echo "🎯 E-commerce Scraper Commands"
	@echo "=============================="
	@echo "install    - Install dependencies using uv"
	@echo "run        - Run the scraper application"
	@echo "clean      - Clean up generated files"
	@echo "test       - Run tests (if available)"
	@echo "lint       - Run code linting"
	@echo "format     - Format code with black"
	@echo "package    - Build package for distribution"
	@echo "help       - Show this help message"

install:
	@echo "📦 Installing dependencies..."
	@python install.py

run:
	@echo "🚀 Starting E-commerce Scraper..."
	@uv run python -m main

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf __pycache__/ */__pycache__/
	@rm -rf .pytest_cache/
	@rm -f *.pyc */*.pyc
	@rm -f *.log
	@echo "✅ Cleanup complete!"

test:
	@echo "🧪 Running tests..."
	@uv run pytest tests/ -v

lint:
	@echo "🔍 Running linter..."
	@uv run flake8 ecommerce_scraper/

format:
	@echo "🎨 Formatting code..."
	@uv run black ecommerce_scraper/

package:
	@echo "📦 Building package..."
	@uv build
