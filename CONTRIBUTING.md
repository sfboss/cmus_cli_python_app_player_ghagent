# Contributing to CMUS Rich

Thank you for your interest in contributing to CMUS Rich! This document provides guidelines and information for contributors.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sfboss/cmus_cli_python_app_player_ghagent.git
   cd cmus_cli_python_app_player_ghagent
   ```

2. **Set up development environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   pip install -r requirements-dev.txt
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Before submitting a PR, run:

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type check
mypy src/
```

## Project Structure

```
src/cmus_rich/
├── core/           # Core application components
├── features/       # Feature modules (playback, queue, library, etc.)
├── ui/             # UI components
├── plugins/        # Plugin system
└── utils/          # Utility modules
```

## Adding New Features

1. Create a new module in the appropriate directory
2. Add tests for your feature in `tests/`
3. Update documentation if needed
4. Ensure all tests pass
5. Submit a pull request

## Creating Plugins

Plugins extend CMUS Rich functionality. To create a plugin:

1. Create a new file in `plugins/` directory
2. Inherit from `Plugin` base class
3. Implement event handlers as needed

Example:

```python
from cmus_rich.plugins.api import Plugin
from cmus_rich.core.cmus_interface import TrackInfo

class MyPlugin(Plugin):
    def __init__(self, app):
        super().__init__(app)
        self.name = "my_plugin"
        self.version = "1.0.0"
    
    async def on_track_change(self, track: TrackInfo):
        # Handle track change
        pass
```

## Testing

- Write tests for all new features
- Maintain or improve test coverage
- Run the full test suite before submitting PRs

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cmus_rich --cov-report=html

# Run specific test
pytest tests/test_core.py::TestCMUSInterface
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Update documentation
7. Commit your changes with clear messages
8. Push to your fork
9. Submit a pull request

## Commit Messages

Use clear, descriptive commit messages:

- Use present tense ("Add feature" not "Added feature")
- Be concise but descriptive
- Reference issues when applicable

Examples:
- `Add search functionality for library`
- `Fix volume control bug (#123)`
- `Improve dashboard rendering performance`

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Questions?

Feel free to open an issue for questions or discussions!
