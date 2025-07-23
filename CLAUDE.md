# Project Guidelines for contextr

## Build & Test Commands
- Install: `uv sync --extra dev` (uses uv package manager)
- Run: `contextr` or `ctxr` (short alias)
- Python version: Requires Python >= 3.12
- Format code: `uv run ruff format .`
- Lint code: `uv run ruff check .`
- Auto-fix linting issues: `uv run ruff check . --fix`
- Type check: `uv run pyright` (runs strict type checking)
- Run tests: `uv run pytest` (runs all tests with coverage)
- Run specific test: `uv run pytest tests/unit/test_file.py`
- Run tests with verbose output: `uv run pytest -v`

## Code Style Guidelines
- **Formatting**: Enforced by Ruff with 88 character line length (matching Black)
- **Linting**: Ruff checks for F (Pyflakes), E/W (pycodestyle), and I (isort) rules
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Automatically sorted by Ruff following isort conventions
- **Types**: Use type hints with explicit return types on functions, enforced by Pyright strict mode
- **Documentation**: Google-style docstrings with Args/Returns sections
- **Error Handling**: Use try/except with specific error types
- **Type Checking**: Pyright configured in strict mode - all functions must have type annotations

## Project Structure
- CLI commands defined in `cli.py`
- Core functionality in `manager.py`
- Output formatting in `formatters.py`
- Helper utilities in `utils/` directory
- Tests in `tests/` directory (unit, integration, fixtures)

## Testing Guidelines
- **Framework**: pytest with coverage reporting
- **Structure**: Tests organized in unit/, integration/, and fixtures/ directories
- **Coverage Goal**: Aim for 80% code coverage
- **Test Naming**: Use descriptive test names that explain what is being tested
- **Test Organization**: Group related tests in classes
- **Fixtures**: Shared fixtures in conftest.py
- **Mocking**: Use pytest-mock for mocking external dependencies
- **Parametrization**: Use @pytest.mark.parametrize for multiple test cases