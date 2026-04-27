# Security Policy

BugIntel AI Workbench is intended for authorized security research only.

## Acceptable Use

Use this project only against:

- Your own systems
- Local labs
- CTF environments
- Explicitly authorized bug bounty or penetration testing scopes

## Not Allowed

Do not use this project for:

- Unauthorized scanning
- Credential attacks
- Destructive testing
- Denial-of-service activity
- Stealth, persistence, or evasion
- Testing targets outside written authorization

## Safety Design

The project includes a Scope Guard that checks URLs, domains, schemes, methods, and forbidden paths before command execution.

Future modules must pass through the Scope Guard before running browser, Kali, or network actions.
