# Case Study Plan: Blackhole_AI Evaluation

Status: planning only, not final paper text.

## Purpose

The evaluation needs controlled vulnerability-research planning cases.

The cases should test whether Blackhole_AI improves planning quality, evidence discipline, safety discipline, validation readiness, and overclaim control.

The cases should not require live exploitation or testing against third-party production systems.

## Case source categories

### Category A: Intentionally vulnerable local labs

These are safe local environments designed for learning and testing.

Examples may include:

- OWASP Juice Shop
- DVWA
- WebGoat
- intentionally vulnerable toy APIs created for this study
- local mock services with known authorization, upload, or validation issues

These cases are useful because the ground truth can be controlled.

### Category B: Synthetic bug bounty-style scenarios

These are artificial scenarios written to look like realistic vulnerability-research notes.

Examples:

- incomplete endpoint notes
- suspected authorization issue with missing proof
- file upload behavior with unclear impact
- webhook/integration trust-boundary scenario
- API key exposure scenario with missing abuse validation
- mobile deeplink/WebView scenario with unclear privilege boundary

These cases are useful for testing overclaim control and evidence planning.

### Category C: Sanitized historical research workflows

These are based on the researcher's previous real-world experience, but with all sensitive details removed.

Requirements:

- remove target names unless publicly disclosed
- remove private URLs
- remove tokens, secrets, account IDs, and screenshots
- remove any customer or personal data
- avoid undisclosed vulnerability details
- convert into abstract planning tasks

These cases are useful because they reflect real vulnerability-research ambiguity.

### Category D: Public CVE/advisory-derived planning tasks

These use public vulnerability descriptions converted into planning exercises.

Requirements:

- use only public information
- do not include weaponized exploit instructions
- focus on planning evidence and validation boundaries
- use cases after disclosure, not active private issues

These cases are useful because the vulnerability class and ground truth are documented.

## Initial case count

For a first preprint or workshop-style paper, target:

- 8 to 12 total cases

Suggested mix:

- 3 local lab cases
- 3 synthetic bug bounty-style cases
- 2 sanitized historical workflow cases
- 2 public advisory-derived cases

For a stronger later paper, expand to:

- 15 to 25 cases

## Case template

Each case should include:

- case ID
- short title
- source category
- scenario description
- available initial evidence
- known missing evidence
- safety constraints
- expected planning requirements
- expected blockers
- ground-truth notes, if available
- excluded actions
- scoring notes

## Example case types

### Case type 1: Evidence gap

A suspected vulnerability exists, but the provided notes are incomplete.

The workflow should identify missing baselines, reproduction details, impact evidence, and negative controls.

### Case type 2: Unsafe-action temptation

The scenario includes a tempting but unsafe validation step.

The workflow should reject or gate the unsafe step.

### Case type 3: Overclaim risk

The scenario appears severe, but impact is not yet proven.

The workflow should avoid premature severity or reportability claims.

### Case type 4: Validation planning

The scenario requires a careful safe validation plan.

The workflow should produce ordered steps, expected observations, and stopping rules.

### Case type 5: Not-reportable decision

The scenario lacks enough evidence.

The workflow should clearly explain why it is not reportable yet.

## Excluded case types

The first evaluation should not include cases that require:

- live third-party target testing
- bypassing real authentication
- interacting with real users
- purchasing goods or services
- destructive actions
- malware execution
- credential attacks
- secret abuse
- exfiltration of real data

## Ground truth

Where possible, each case should have a ground-truth planning checklist.

Ground truth may include:

- required evidence items
- unsafe actions that should be avoided
- known missing proof
- correct reportability state
- expected validation boundaries

## Current decision

The first evaluation should use safe controlled cases, not live bug bounty programs.

Blackhole_AI should be evaluated as a planning and safety workflow, not as an exploitation system.
