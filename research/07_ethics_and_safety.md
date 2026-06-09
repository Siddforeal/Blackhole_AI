# Ethics and Safety Plan: Blackhole_AI Research

Status: planning only, not final paper text.

## Purpose

This file defines the ethical and safety boundaries for a research paper based on Blackhole_AI.

The research should study vulnerability research planning, evidence discipline, validation readiness, and responsible disclosure workflow.

The research should not perform unauthorized security testing or autonomous exploitation.

## Core ethical position

Blackhole_AI should be evaluated as a human-in-the-loop planning and review system.

The system should support authorized security researchers, not replace human judgment or remove responsibility from the researcher.

## Allowed research activities

The evaluation may include:

- controlled local lab scenarios
- intentionally vulnerable applications
- synthetic vulnerability-research cases
- sanitized historical research notes
- public advisory-derived planning tasks
- offline evaluation of generated plans
- comparison of manual notes, direct LLM assistance, and Blackhole_AI outputs
- scoring of evidence completeness, safety, overclaim control, validation quality, blocker detection, and usefulness

## Disallowed research activities

The evaluation should not include:

- unauthorized testing of third-party systems
- exploitation of live production targets
- destructive testing
- interaction with real users
- credential attacks
- brute force attacks
- secret abuse
- malware deployment
- data exfiltration
- bypassing real access controls
- purchases or financial transactions
- automatic bug bounty report submission
- automatic vulnerability confirmation without human review

## Safety gates

Blackhole_AI should preserve safety boundaries such as:

- no tool execution by default
- no network interaction by default
- no browser execution by default
- no Kali command execution by default
- no live validation without explicit human approval
- no report submission without explicit human approval
- no claim of confirmed vulnerability without evidence
- no claim of reportability when evidence is incomplete

## Responsible disclosure boundary

If any real vulnerability is discovered during unrelated authorized research, it should be handled through normal responsible disclosure or bug bounty processes.

However, the evaluation for the first paper should avoid depending on undisclosed vulnerabilities.

The paper should not reveal private program information, private reports, secrets, customer data, or non-public vulnerability details.

## Data handling

Evaluation data should avoid sensitive information.

The research dataset should remove or avoid:

- real tokens
- API keys
- credentials
- private URLs
- customer data
- personal data
- proprietary screenshots
- non-public bounty report details
- undisclosed vulnerability details

## Human oversight

All outputs should be treated as planning assistance.

A human researcher remains responsible for:

- checking authorization
- validating scope
- deciding whether testing is allowed
- approving any validation step
- interpreting evidence
- deciding whether a finding is reportable
- handling disclosure

## Risk analysis

Possible risks include:

- generated plans may include unsafe steps
- generated plans may overclaim severity
- generated plans may omit important evidence
- researchers may over-trust AI output
- evaluation cases may accidentally include sensitive details
- workflow structure may create false confidence

The evaluation should measure and discuss these risks honestly.

## Paper limitations

The paper should clearly state that the evaluation does not prove:

- autonomous vulnerability discovery
- universal safety
- replacement of human expertise
- real-world exploit success
- superiority over all security tools

## Current ethical decision

The first paper should evaluate Blackhole_AI using safe, controlled, offline, human-reviewed planning tasks.

The research should prioritize academic defensibility, researcher safety, responsible disclosure, and avoidance of unsupported claims.
