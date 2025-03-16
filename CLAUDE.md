# Project Guidelines for contextr

## Build & Test Commands
- Install: `pip install -e .`
- Run: `contextr` or `ctxr` (short alias)
- Python version: Requires Python >= 3.12

## Code Style Guidelines
- **Formatting**: Follow PEP 8 guidelines with ~80-90 character line length
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Group by standard library, third-party, then local imports with blank line separators
- **Types**: Use type hints with explicit return types on functions
- **Documentation**: Google-style docstrings with Args/Returns sections
- **Error Handling**: Use try/except with specific error types

## Project Structure
- CLI commands defined in `cli.py`
- Core functionality in `manager.py`
- Output formatting in `formatters.py`
- Helper utilities in `utils/` directory