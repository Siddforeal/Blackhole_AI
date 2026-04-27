# BugIntel AI Workbench

Human-in-the-loop AI-assisted vulnerability discovery and bug intelligence workbench.

BugIntel AI Workbench is a research prototype for authorized security testing. It helps security researchers define target scope, map attack surfaces, analyze endpoints, store evidence, and generate structured vulnerability intelligence.

## Current Status

Version `0.1.0` is under active development.

Completed:

- Scope Guard
- Target scope model
- URL/method/domain/path authorization checks
- Unit tests for scope validation

## Core Principle

The tool is designed for authorized testing only. Every future agent, browser action, and command runner must pass through the Scope Guard before execution.

## Planned Modules

- Target workspace
- Evidence store
- Endpoint miner
- Safe Kali command runner
- Browser/HAR/Burp import
- Task tree expansion
- Response analyzer
- AI-assisted report generation
