# Related Work Map: Blackhole_AI Research

Status: planning only, not final paper text.

## Purpose

This file maps the research areas that Blackhole_AI must be compared against.

The purpose is not to write the related-work section yet.

The purpose is to identify where Blackhole_AI fits, what it is similar to, and what it should not claim.

## Working paper direction

Evidence-gated human-in-the-loop AI assistance for vulnerability research planning.

## Related work category 1: LLM-assisted penetration testing

Representative work:

- PentestGPT: An LLM-empowered Automatic Penetration Testing Tool
- PentestEval: Benchmarking LLM-based Penetration Testing with Modular and Stage-Level Design

Why this matters:

These papers study LLMs for penetration testing workflows.

They show that LLMs can assist with sub-tasks, but full end-to-end autonomous penetration testing remains difficult.

How Blackhole_AI differs:

Blackhole_AI should not compete as a fully autonomous pentesting system.

The first Blackhole_AI paper should focus on structured planning, evidence discipline, safety gates, validation readiness, and reportability control.

Useful contrast:

- PentestGPT focuses on LLM-assisted pentesting task execution.
- PentestEval focuses on modular benchmark evaluation of pentesting stages.
- Blackhole_AI should focus on evidence-gated human-in-the-loop research planning.

Sources to review:

- https://arxiv.org/abs/2308.06782
- https://arxiv.org/abs/2512.14233

## Related work category 2: Automated pentesting agents

Representative work:

- APT-Agent: Automated Penetration Testing using Large Language Models
- Other LLM-based agentic penetration testing systems

Why this matters:

These systems try to automate reconnaissance, exploitation, and multi-step attack execution.

How Blackhole_AI differs:

Blackhole_AI's first paper should not claim autonomous exploitation.

The stronger contribution is workflow control and safety-aware planning for human researchers.

Useful contrast:

- Automated agents optimize for task completion or exploitation success.
- Blackhole_AI should be evaluated on planning quality, evidence completeness, safety discipline, blocker detection, and overclaim control.

Sources to review:

- https://arxiv.org/abs/2605.24949

## Related work category 3: AI cyber reasoning and autonomous vulnerability remediation

Representative work:

- DARPA AI Cyber Challenge
- Cyber Grand Challenge history
- AIxCC-related papers and reports

Why this matters:

This area focuses on autonomous systems that find, prove, and patch vulnerabilities.

How Blackhole_AI differs:

Blackhole_AI is not trying to be a fully autonomous cyber reasoning system in the first paper.

The first paper should position Blackhole_AI as a human-in-the-loop research workbench for authorized vulnerability research planning.

Useful contrast:

- AIxCC-style systems focus on automatic vulnerability discovery and patching.
- Blackhole_AI focuses on human-controlled planning, evidence, safety, and disclosure readiness.

Sources to review:

- https://www.darpa.mil/research/programs/ai-cyber
- https://en.wikipedia.org/wiki/DARPA#Projects
- https://www.axios.com/2024/08/13/darpa-ai-cyber-challenge-def-con

## Related work category 4: Vulnerability disclosure and responsible reporting

Representative topics:

- Coordinated vulnerability disclosure
- Responsible disclosure
- CERT/CC coordination
- CISA coordinated vulnerability disclosure process
- ISO/IEC 29147 vulnerability disclosure

Why this matters:

Blackhole_AI's workflow includes evidence readiness, blocker tracking, reportability decisions, and responsible disclosure boundaries.

How Blackhole_AI relates:

The first paper can argue that AI-assisted security research should not only generate attack ideas.

It should also help researchers decide whether evidence is sufficient, whether validation is safe, and whether a finding is ready for disclosure.

Sources to review:

- https://www.cisa.gov/coordinated-vulnerability-disclosure-process
- https://vuls.cert.org/confluence/display/CVD
- https://www.iso.org/standard/45170.html

## Related work category 5: AI safety, governance, and risk management

Representative topics:

- NIST AI Risk Management Framework
- AI governance for agentic systems
- risk-based AI assurance
- human oversight and accountability

Why this matters:

Blackhole_AI uses safety gates and human review boundaries.

This connects to broader AI risk management, especially for agentic or semi-agentic AI systems used in high-risk domains.

How Blackhole_AI differs:

The first paper should not become a general AI governance paper.

It should use AI safety and risk-management literature only to support the need for safety-gated workflows in AI-assisted cybersecurity research.

Sources to review:

- https://www.nist.gov/itl/ai-risk-management-framework
- https://arxiv.org/abs/2401.15229
- https://arxiv.org/abs/2510.25863

## Related work category 6: Security workflow, evidence, and reproducibility

Representative topics:

- vulnerability validation workflows
- evidence quality in bug bounty reports
- reproducibility of security findings
- triage-readiness
- empirical security research ethics

Why this matters:

This may become the most important gap for Blackhole_AI.

Many AI-pentesting papers focus on task completion, exploitation success, or benchmark performance.

Blackhole_AI should focus on whether AI assistance improves the quality and safety of the research process itself.

Potential gap:

There appears to be less work focused specifically on evidence-gated, human-in-the-loop vulnerability research planning for responsible disclosure workflows.

This gap must be verified through deeper literature review before making a final novelty claim.

## Initial novelty hypothesis

Blackhole_AI may be novel if positioned as:

A safety-gated, evidence-driven, human-in-the-loop workflow for AI-assisted vulnerability research planning.

The novelty is not simply using an LLM.

The novelty would be the combination of:

- structured research packets
- hypothesis generation and selection
- evidence checklist generation
- blocker identification
- validation planning
- safety gating
- report-readiness decisions
- responsible disclosure orientation

## Claims to avoid in related work

Do not claim that no one has used AI for penetration testing.

Do not claim that Blackhole_AI is the first AI security assistant.

Do not claim that Blackhole_AI outperforms pentesting agents unless evaluated.

Do not claim that Blackhole_AI discovers more vulnerabilities unless proven.

Do not claim novelty until the deeper related-work review is complete.

## Current decision

The related-work argument should position Blackhole_AI as complementary to autonomous pentesting and cyber reasoning systems.

Blackhole_AI should be framed as a workflow and safety-control contribution for human researchers, not as another autonomous exploitation agent.
