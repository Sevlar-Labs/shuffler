# Contributing to Shuffler

Thank you for your interest in contributing to Shuffler. This document outlines
the standards and workflows required for all code submissions. Please read it in
full before opening a pull request.

---

## Local Development Setup

### For Contributors (Virtual Environment)

All development work must be done inside an isolated virtual environment to
avoid polluting the system Python installation.

```bash
git clone https://github.com/Sevlar-Labs/shuffler.git
cd shuffler
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the package in editable mode along with all test dependencies.

### For End Users (Global Installation)

If you only need to run the tool, install it globally via
[pipx](https://pipx.pypa.io/):

```bash
pipx install --editable . --force
```

---

## Testing Standards

All pull requests **must** satisfy the following requirements before review:

1. **The existing test suite must pass.** Run the full suite locally and confirm
   zero failures:

   ```bash
   pytest -v
   ```

2. **New attack vectors must include tests.** Any new module added under
   `shuffler/vectors/` must be accompanied by corresponding test coverage in the
   `tests/` directory. At minimum, cover the success path, the failure path, and
   any edge cases related to payload parsing or response validation.

3. **Bug fixes must include a regression test.** If your PR fixes a defect,
   include a test that reproduces the original failure and passes with your fix
   applied.

4. **No test may depend on external network access.** All HTTP interactions must
   be mocked. Tests that require a running Docker sandbox or a live API key will
   not be accepted into the automated suite.

---

## Coding Standards

### Type Hints

All function signatures **must** include full type annotations, including the
return type. Untyped functions will not be merged.

```python
# Correct
def execute(target: str, burst: int) -> AttackReport:
    ...

# Incorrect -- missing return type
def execute(target, burst):
    ...
```

### Terminal Output

All user-facing terminal output **must** use the
[Rich](https://rich.readthedocs.io/) library via the shared `console` instance
exported from `shuffler.display`. Direct calls to the built-in `print()`
function are strictly prohibited in library and CLI code.

```python
# Correct
from shuffler.display import console
console.print("[bold green]Operation complete.[/]")

# Incorrect
print("Operation complete.")
```

### Asynchronous Discipline

Shuffler's attack vectors execute concurrently using `asyncio`. The following
rules apply to all code in async contexts:

- **No synchronous blocking calls.** Never use `time.sleep()`,
  synchronous `requests`, or any other call that blocks the event loop inside
  an `async def` function. Use `asyncio.sleep()` and `httpx.AsyncClient`
  instead.

- **No bare `asyncio.run()` inside async functions.** The event loop is managed
  exclusively by the CLI entry point in `shuffler/main.py`.

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Keep line length at or below **99 characters**.
- Use double quotes for strings unless single quotes avoid escaping.
- Maintain existing comment banners and section separators for consistency.

---

## Commit Messages

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add latency injection attack vector
fix: handle empty response body in hallucination vector
docs: update CLI reference with new --delay flag
test: add regression test for duplicate payload deduplication
```

---

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Implement your changes following the standards above.
3. Run `pytest -v` and confirm all tests pass.
4. Open a pull request against `main` and complete the PR template checklist.
5. A maintainer will review your submission. Address any requested changes
   promptly.

---

## Questions

If you are unsure whether a contribution is in scope or how to approach an
implementation, open a
[Discussion](https://github.com/Sevlar-Labs/shuffler/discussions) before
writing code. This avoids wasted effort on changes that may not align with the
project's roadmap.
