---
name: shuffler:autonomous-contribution-lifecycle
description: Governs the deterministic Git workflow for isolated feature development, branch provisioning, and open-source contribution delivery. Use whenever initializing a new technical task, bug fix, or preparing a pull request.
---

# Autonomous Contribution Lifecycle

This skill enforces a strict, isolated version control lifecycle for autonomous agents operating within the Shuffler repository. To prevent chaotic or unreviewed code from entering production, agents must treat branch provisioning and pull requests as absolute systemic barriers. Agents are strictly forbidden from committing directly to production branches.

## When to use this skill

- Use this before writing any code to provision an isolated working environment.
- Use this when finalizing a feature or bug fix and preparing it for human review.
- This is helpful for ensuring the repository maintains a clean, semantic history and that all AI-generated code undergoes mandatory human-in-the-loop validation.

## How to use it

When acting on an issue, feature request, or refactoring task, you must strictly follow this phased sequence:

### 1. Branch Provisioning (Pre-Flight Isolation)
* **Convention:** You must never write code directly to the `main` or `master` branch.
* **Pattern:** Before executing any file modifications, compute a descriptive branch name using standard prefixes (e.g., `feature/type-validation`, `bugfix/async-timeout`, `chore/docs-update`) and check out this new branch.

### 2. Iterative Development & Atomic Commits
* **Convention:** Execute all code changes, test generation, and linting strictly within the isolated branch boundary. 
* **Pattern:** Bundle logical changes into clear, atomic commits. Use semantic commit messages (e.g., `feat:`, `fix:`, `docs:`) that reference the specific task or intent.

### 3. Pull Request Automation & Human Handoff
* **Convention:** Agents must never merge pull requests autonomously. The Pull Request is the definitive boundary where the agentic loop pauses and the human reviewer enters the loop.
* **Pattern:** Once the implementation is finalized, push the branch to the remote repository and open a Pull Request. The PR description must clearly summarize the architectural intent, the files changed, and instructions for local testing to facilitate a high-signal human review.
