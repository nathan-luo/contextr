# Project Guidelines for contextr

## Build & Test Commands
- Install: `uv sync --extra dev` (uses uv package manager)
- Run: `contextr` or `ctxr` (short alias)
- Python version: Requires Python >= 3.12
- Format code: `uv run ruff format .`
- Lint code: `uv run ruff check .`
- Auto-fix linting issues: `uv run ruff check . --fix`
- Type check: `uv run pyright` (runs strict type checking)
- Run tests: `uv run pytest` (runs all tests with coverage - currently 89 tests, 62% coverage)
- Run specific test: `uv run pytest tests/unit/test_file.py`
- Run tests with verbose output: `uv run pytest -v`
- Check coverage: `uv run pytest --cov=contextr --cov-report=term-missing`

## Development Workflow
- **CI/CD**: Tests run automatically only on PRs to main branch (not on pushes)
- **Local Validation**: Pre-commit hooks run ruff-format, ruff, and pyright before commits
- **Setup pre-commit**: `uv run pre-commit install` (run once after cloning)
- **Run all checks locally**: `uv run pre-commit run --all-files`
- **Skip pre-commit**: `git commit --no-verify` (use sparingly)

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
- CLI commands defined in `cli.py` (including profile management commands)
- Core functionality in `manager.py` (with storage abstraction)
- Profile management in `profile.py` (ProfileManager and Profile classes)
- Storage abstraction in `storage/` directory (base.py, json_storage.py)
- Output formatting in `formatters.py`
- Helper utilities in `utils/` directory
- Tests in `tests/` directory (unit, integration, fixtures)

## Testing Guidelines
- **Framework**: pytest with coverage reporting
- **Structure**: Tests organized in unit/, integration/, and fixtures/ directories
- **Coverage Goal**: Aim for 80% code coverage (currently at 62%)
- **Test Naming**: Use descriptive test names that explain what is being tested
- **Test Organization**: Group related tests in classes
- **Fixtures**: Shared fixtures in conftest.py
- **Mocking**: Use pytest-mock for mocking external dependencies
- **Parametrization**: Use @pytest.mark.parametrize for multiple test cases