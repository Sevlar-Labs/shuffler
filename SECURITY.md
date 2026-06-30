# Security Policy

## Supported Versions

Only the latest minor release line receives security patches. Older versions
are considered end-of-life and will not be updated.

| Version   | Supported          |
|-----------|--------------------|
| >= 1.0.x  | Yes                |
| < 1.0     | No                 |

## Reporting a Vulnerability

**Do not open a public GitHub issue to report a security vulnerability.**
Public disclosure before a fix is available puts all users of the tool at risk.

Instead, use GitHub's native **Private Vulnerability Reporting** feature:

1. Navigate to the **Security** tab of this repository.
2. Click **"Report a vulnerability"**.
3. Complete the form with a detailed description of the vulnerability,
   including steps to reproduce, affected versions, and potential impact.

This ensures that the report is delivered securely and is visible only to the
repository maintainers.

## Response SLA

The Sevlar Labs security team commits to the following response timeline:

- **Acknowledgment**: Within **48 hours** of receiving the report, we will
  confirm receipt and assign an internal tracking identifier.
- **Assessment**: Within **5 business days**, we will provide an initial
  severity assessment and an estimated timeline for remediation.
- **Patch Release**: A fix will be developed, reviewed, and published as a
  patch release. The reporter will be notified before public disclosure.

We request that reporters allow a reasonable coordination window before any
public disclosure so that a patch can be made available to all users.

## Attribution

Reporters who follow this responsible disclosure process will be credited in the
release notes accompanying the security patch, unless they request anonymity.
