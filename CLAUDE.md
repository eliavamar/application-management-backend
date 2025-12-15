# application-management-backend_b534fb9f

## Project Overview

* [Docker](https://www.docker.com/). * [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Tech Stack

- **Python**: 100%

### Frameworks
- Python (pyproject.toml)

## Project Structure

```
📄 Dockerfile
📄 README.md
📄 alembic.ini
📁 app
  📄 __init__.py
  📁 alembic
  📁 api
  📄 backend_pre_start.py
  📁 core
📄 pyproject.toml
📁 scripts
  📄 format.sh
  📄 lint.sh
  📄 prestart.sh
  📄 test.sh
  📄 tests-start.sh
📁 tests
  📄 __init__.py
  📁 api
  📄 conftest.py
  📁 crud
  📁 scripts
📄 uv.lock
```

## Development Commands

```bash
# Install dependencies
poetry install  # or: pip install -r requirements.txt

# Run tests
pytest

# Format code
black . && ruff check --fix .
```

## Key Patterns & Conventions

- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Prefer dataclasses for data structures

## Important Context for AI Agents

When working with this codebase:

- Total files: 62
- Total lines: 2704
- Primary language: Python

### Do's
- Read relevant source files before making changes
- Follow existing code patterns and conventions
- Write tests for new functionality
- Keep commits atomic and well-described

### Don'ts
- Don't introduce new dependencies without discussion
- Don't change formatting/style unless specifically requested
- Don't remove existing functionality without confirmation
