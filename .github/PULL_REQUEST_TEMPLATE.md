## Architectural Context

<!--
  Explain WHY this change is necessary. Describe the problem, the root cause,
  and why the chosen approach is the correct solution. Link to any related
  issues or discussions.
-->

## Summary of Changes

<!--
  Provide a concise description of WHAT changed. List modified files or modules
  and the nature of each change (new feature, bug fix, refactor, documentation).
-->

## Pre-Merge Checklist

Before requesting review, confirm that every item below is satisfied.
A pull request with unchecked items will not be reviewed.

- [ ] `pytest -v` passes locally with zero failures.
- [ ] All new and modified functions include complete type hints (`-> type`).
- [ ] All terminal output uses `Rich` via `shuffler.display.console` -- no bare `print()` calls.
- [ ] No synchronous blocking calls (`time.sleep()`, `requests.get()`, etc.) introduced in async contexts.
- [ ] `README.md` updated if this PR changes CLI flags, adds commands, or modifies installation steps.
- [ ] New attack vectors include corresponding test coverage in `tests/`.
- [ ] Commit messages follow Conventional Commits format.

## Test Evidence

<!--
  Paste the output of `pytest -v` or describe how the change was validated.
-->

```
<paste pytest output here>
```
