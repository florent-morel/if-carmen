# Contributing to Carmen

Thank you for your interest in contributing to Carmen! This guide will help you get started with contributing to the Carbon Measurement Engine project. 🌱

## Getting Started

### Prerequisites

- **Python 3.11 or higher** - Carmen requires modern Python features
- **pip** - Python package manager
- **npm** - Node package manager for Impact Framework dependencies
- **git** - Version control system

### Fork and Clone

To start contributing, you'll first need to fork the Carmen repository on GitHub.

**Step 1:** Fork the repository on GitHub by clicking the "Fork" button.

**Step 2:** Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/carmen.git
cd carmen
```

**Step 3:** Add the upstream repository as a remote:
```bash
git remote add upstream https://github.com/original/carmen.git
```


## Development Setup

### Setting Up Your Python Environment

The first step in setting up your development environment is creating a Python virtual environment. This isolates your Carmen development dependencies from other Python projects on your system.

**For Linux/macOS:**

**Step 1:** Create a virtual environment:
```bash
python -m venv .venv
```

**Step 2:** Activate the virtual environment:
```bash
source ./.venv/bin/activate
```

**Step 3:** Upgrade pip to the latest version:
```bash
python -m pip install --upgrade pip
```

**Step 4:** Install Carmen in editable mode with development dependencies:
```bash
pip install -e ".[dev]"
```

**For Windows:**

**Step 1:** Create a virtual environment:
```bash
py -m venv .venv
```

**Step 2:** Activate the virtual environment:
```bash
.\.venv\Scripts\activate
```

**Step 3:** Upgrade pip:
```bash
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

**Step 4:** Install Carmen with development dependencies:
```bash
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Installing Impact Framework Dependencies

Carmen relies on the Impact Framework developed by the Green Software Foundation: 

```bash
npm install
```

> **Note:** The `misc-services-model-plugin` build output is committed to the repository, so no local build step is required. If you modify the plugin's TypeScript source, rebuild it with:
> ```bash
> cd misc-services-model-plugin && npm run build
> ```
> and commit the updated `build/` files alongside your source changes.

### Verifying Your Installation

After completing the setup, it's important to verify that everything is working correctly.

**Step 1:** Run the test suite:
```bash
pytest ./backend
```

**Step 2:** Check linting:
```bash
pylint ./backend
```

**Step 3:** Verify formatting:
```bash
black --check .
```

If all these commands complete successfully, your development environment is ready.

## Code Standards

### Python Code Style

Carmen follows PEP 8 standards for Python code, with some project-specific conventions. For automatic code formatting, we use Black, which ensures consistent style across the entire codebase. Pylint serves as our linter for catching code quality issues before they make it into the repository.

All functions should include type hints for parameters and return values. This improves code readability and enables better IDE support for autocomplete and error detection. Additionally, all public functions and classes must have docstrings following the Google style, which we'll discuss in more detail in the documentation section.

### Maintaining Code Quality

Before submitting any code, you must ensure it's properly formatted and passes all quality checks.

**Step 1:** Format your code with Black:
```bash
black .
```

**Step 2:** Check for linting issues:
```bash
pylint backend/
```

You should resolve all Pylint warnings and errors for any files you modify. We aim for a Pylint score of 9.0 or higher. If you absolutely must disable a specific warning, add a comment explaining why:

```python
# pylint: disable=broad-except
# Reason: We need to catch all exceptions here to ensure the daemon doesn't crash during data collection
```

## Testing Guidelines

### Writing Effective Tests

Tests should be placed in the `tests/` directory, mirroring the structure of the source code. All test files must be named with the `test_*.py` pattern so pytest can discover them automatically. We aim for at least 80% code coverage, with particular emphasis on testing critical logic, edge cases, and error handling scenarios.

When writing tests, follow the Arrange-Act-Assert pattern. First, arrange your test data and set up expectations. Then act by executing the function or method being tested. Finally, assert that the results match your expectations. Here's an example:

```python
def test_calculate_carbon_emissions():
    # Arrange: Set up test data and expectations
    vm_usage = VMUsage(cpu=50, memory=8, duration=3600)
    expected_emissions = 0.042
    
    # Act: Execute the function being tested
    result = calculate_emissions(vm_usage)
    
    # Assert: Verify the results
    assert abs(result - expected_emissions) < 0.001
```

### Documenting Your Tests

Each test should include a docstring that explains what functionality is being tested, why it's important to test, and how edge cases are handled if applicable. Here's an example:

```python
def test_handle_missing_prometheus_data():
    """
    Test that the API gracefully handles missing Prometheus data.
    
    This is critical because Prometheus might be temporarily unavailable
    or missing data for certain time ranges. We should return a clear
    error message rather than crashing.
    """
    # Test implementation...
```

## Pull Request Process

### Preparing Your Changes

Before creating a pull request, you need to ensure your branch is up to date with the latest changes from the main repository.

**Step 1:** Create a feature branch for your changes:
```bash
git checkout -b feature/your-feature-name main
```

Use a descriptive name that reflects what you're working on, such as `feature/storage-carbon-calculation` or `fix/prometheus-timeout`.

**Step 2:** Make your changes and commit them:
```bash
git add .
git commit -m "feat: add carbon calculation for storage services"
```

Follow our conventional commit format (described in detail below).

**Step 3:** Run the full test suite:
```bash
pytest ./backend
```

**Step 4:** Format your code:
```bash
black .
```

**Step 5:** Check for linting issues:
```bash
pylint ./backend
```

**Step 6:** Push your changes to your fork:
```bash
git push origin feature/your-feature-name
```

### Creating the Pull Request

Navigate to the Carmen repository on GitHub and click the "New Pull Request" button. Fill out the pull request template with a clear description of what your changes do and why they're needed. Link any related issues so reviewers have full context.

## Commit Message Guidelines

### Conventional Commits Format

We follow the Conventional Commits specification for all commit messages. This provides a structured format that makes it easy to understand what each commit does and helps with automated changelog generation. The basic format consists of a type, an optional scope, and a subject line. You can also include a body and footer for more detailed commits.

The format looks like this:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

Different types of commits serve different purposes:

- **feat** - New features that add functionality
- **fix** - Bug fixes that resolve issues
- **docs** - Documentation changes only
- **style** - Code style changes (formatting, missing semicolons, etc.)
- **refactor** - Code refactoring without changing functionality
- **perf** - Performance improvements
- **test** - Adding or updating tests
- **chore** - Maintenance tasks and dependency updates
- **ci** - CI/CD configuration changes
- **build** - Build system or external dependency changes

### Examples of Good Commit Messages

Here are some examples of well-formatted commit messages:

A feature commit:
```bash
feat(daemon): add support for storage service carbon calculations
```

A bug fix:
```bash
fix(api): handle missing Prometheus metrics gracefully
```

Documentation updates:
```bash
docs(readme): update installation instructions for Windows
```

Test additions:
```bash
test(emissions): add edge case tests for zero usage scenarios
```

Refactoring commits:
```bash
refactor(core): simplify carbon calculation logic
```

Performance improvements:
```bash
perf(api): optimize database queries for large time ranges
```

### Best Practices

When writing commit messages, use the imperative mood. Write "add" instead of "added" or "adds". Keep the subject line under 72 characters so it displays properly in git log output. Capitalize the first letter of the subject line and don't end it with a period.

Separate the subject from the body with a blank line. Use the body to explain what changes you made and why, not how you made them. The diff shows the how, but the commit message should explain the reasoning behind the change. This context is invaluable for future maintainers trying to understand the codebase.

## Documentation

### Code Documentation Standards

All public functions, classes, and modules must have docstrings that explain their purpose and usage. While complex logic should be commented, prefer writing self-documenting code where the intent is clear from well-named variables and functions. Use type hints throughout your code to provide better IDE support and make the code's contracts explicit.

### Writing Docstrings

We use Google-style docstrings for all documentation. A well-written docstring includes a brief description of what the function does, detailed information about each parameter, what the function returns, what exceptions it might raise, and often an example of how to use it. 

### Updating Documentation

Whenever you make changes that affect how users interact with Carmen, you must update the relevant documentation. This includes markdown files in the `docs/` directory, code examples that demonstrate API usage, the README file if installation or basic usage changes, and the CHANGELOG if the project maintains one.

Good documentation is just as important as good code. Users can't benefit from features they don't know about or don't understand how to use. Take the time to write clear, accurate documentation that helps users succeed.

----