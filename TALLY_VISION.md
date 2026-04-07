# TALLY_VISION.md
> Zenbid AI Layer — North Star Document  
> Status: Living Document | Last Updated: 2026-04

---

## What Tally Is

Tally is Zenbid's integrated AI estimating collaborator. It is not a chatbot bolted onto the side of an estimate. It is not an audit tool that runs at the end of a workflow. It is a work executor — woven into the estimate surface itself — that handles quantification, analysis, and reporting work so the estimator can focus on judgment, not labor.

Tally's name and identity (tape measure character, job-site aesthetic) are intentional. It reads as a tool, not a tech feature. Contractors trust tools.

---

## The Core Principle

**Every Tally output lands in the grid.**

Not a sidebar. Not a chat thread. Not a floating panel. When Tally generates line items, they appear in the estimate table with the same structure as manually entered rows — same columns, same format, same inline editability. When Tally delivers a report, it surfaces inline in context, not in a separate view.

The estimator never context-switches. They are always in the estimate.

This is the line between bolt-on AI and integrated AI. The output format is identical to what a human estimator would produce. Tally just did the work faster.

---

## The Three Modes

Tally operates in three distinct modes. Each is a different relationship between the user and the AI. All three must feel like the same product.

---

### Mode 1 — Passive (Always On)

Tally watches the estimate silently and surfaces observations without being asked.

**What it does:**
- Flags scope gaps (missing line items implied by existing scope)
- Surfaces production rate deviations vs. regional benchmarks
- Detects pricing drift when live market data diverges from estimate values
- Identifies assembly incompleteness (e.g. concrete poured but no finishing labor)
- Confidence-scores every AI-touched line item

**How it surfaces:**
- AI status badge on each affected row: Verified / AI Tip / Scope Gap / Live Price
- Badge is inline in the grid cell — not a notification, not a modal
- Hover reveals the specific finding
- Sidebar summary panel shows aggregate counts and risk exposure

**Design rule:**
Passive mode must never interrupt. It informs. The estimator decides whether to act. No forced modals, no blocking alerts.

---

### Mode 2 — Reactive (On Demand)

The estimator asks a question. Tally answers in context.

**What it does:**
- Answers scoped questions about the current estimate
- Generates summary reports by division, phase, trade, or cost type
- Surfaces cost breakdowns, labor exposure, material totals on request
- Answers "what if" questions against existing line items
- Explains flagged items in plain language when asked

**Example prompts:**
- *"Tally, what's my total labor exposure on Division 05?"*
- *"Give me a cost breakdown by phase for this estimate."*
- *"Why did you flag the rebar item?"*
- *"What's driving the variance in Division 09 vs. my last estimate?"*

**How it surfaces:**
- Tally response appears as a contextual panel within the estimate view
- Tabular data (breakdowns, reports) renders in the same grid format as the estimate
- Report can be exported to CSV / PDF without leaving the view
- Response is always scoped to the current estimate — no hallucinated generics

**Design rule:**
Reactive mode is not a general-purpose chatbot. It only answers questions it can answer from the current estimate data and Zenbid's cost intelligence layer. Out-of-scope questions get a clear, honest boundary response.

---

### Mode 3 — Generative (Intent-Driven)

The estimator describes an intent. Tally does the quantification work and drafts the result into the estimate for review.

**What it does:**
- Generates complete line item sets from a scope description
- Builds assemblies from high-level prompts
- Populates quantities, units, labor rates, and material costs as a draft
- Applies trade-specific production rates and regional pricing automatically
- Flags its own uncertainty — low-confidence items get a lower confidence score

**Example prompts:**
- *"Tally, add a rough-in electrical package for a 4,000 SF office build-out."*
- *"Give me a material takeoff for a 10,000 SF metal stud partition system."*
- *"Build out Division 03 for a 6-inch slab on grade, 8,500 SF."*
- *"I need a roofing assembly for TPO 60mil on a flat roof."*

**How it surfaces:**
- Generated rows drop into the estimate as a staged draft group
- Each generated row is badged "AI Generated" (distinct from Verified)
- Estimator reviews row by row: Accept / Edit / Reject
- Accepted rows become standard estimate rows — badge clears to Verified
- Rejected rows are logged as training signal (see Data Flywheel below)
- Entire draft can be accepted or rejected in bulk

**Design rule:**
Generative mode never auto-commits. Every generated item requires explicit estimator review before it becomes part of the estimate. Tally does the work; the estimator owns the output.

---

## Multi-Trade Flexibility

Tally's intelligence must work across trade sectors without requiring a different product per trade. This is achieved through configuration, not code.

**Trade context layer (data-driven):**
- Unit vocabularies per trade (LF of conduit for electrical, CY for concrete, EA for panels)
- Production rate libraries per trade and region
- Assembly templates per trade (e.g. "standard light commercial electrical rough-in")
- Scope gap rules per trade (what's typically missing from each trade's estimates)

**How Tally uses trade context:**
- Trade profile is set at the company level during onboarding
- Tally loads the appropriate context automatically — the estimator never configures it per session
- When a prompt spans multiple trades, Tally identifies the relevant trade context per line item

**Expansion principle:**
Adding support for a new trade sector = loading a new configuration set. Not a new development sprint. Not a new product. The core AI layer is trade-agnostic; the context layer is trade-specific.

---

## The Data Flywheel

Every Tally interaction is a training signal. This is not a future consideration — it must be captured from day one.

| Interaction | Signal |
|---|---|
| Estimator accepts a generated row | Positive — Tally's output was correct |
| Estimator edits a generated row | Partial — captures the delta between AI output and ground truth |
| Estimator rejects a generated row | Negative — Tally's output was wrong or irrelevant |
| Estimator ignores a scope gap flag | Neutral / negative — flag may have been a false positive |
| Estimator acts on a scope gap flag | Positive — flag was correct and actionable |
| Estimate is marked Won | Strong positive on all contributing line items |
| Estimate is marked Lost | Weak signal — may reflect pricing strategy, not accuracy |

**Schema requirements (must be captured from day one):**
- `ai_generated: boolean` on every line item
- `ai_confidence: float` on every AI-touched line item
- `estimator_action: enum(accepted, edited, rejected, ignored)` on every AI suggestion
- `edit_delta: jsonb` capturing original vs. final values on edited rows
- `estimate_outcome: enum(won, lost, pending, abandoned)` on every estimate
- `location_tag` on every line item (for regional pricing intelligence)

This data accumulates into a proprietary cost intelligence dataset. At sufficient volume, it becomes the foundation for fine-tuning an open-source LLM (Mistral, LLaMA 3, or Qwen) on contractor-sourced cost data — the "Cost Intelligence" premium tier comparable to RSMeans but AI-enhanced and continuously updated.

---

## What Tally Is Not

**Not a general-purpose chatbot.**  
Tally does not answer questions outside of estimating. It does not have a personality that dominates the interaction. It is a professional tool with a clear job.

**Not a replacement for estimator judgment.**  
Tally does the quantification labor. The estimator owns the estimate. Every generative output requires human review before it commits. This is non-negotiable.

**Not a required dependency.**  
The platform must function fully without Tally. An experienced estimator who prefers manual entry should never feel forced into AI workflows. Tally is a multiplier on an already useful tool — not the reason the tool works.

**Not a bolt-on.**  
Tally outputs use the same data model, same grid format, same UI components as the rest of the estimate. If a Tally-generated row looks or behaves differently from a manually entered row, that is a bug.

---

## Integration Checklist

Every Tally feature must pass these checks before shipping:

- [ ] Output lands in the grid, not in a separate panel or thread
- [ ] Generated rows are indistinguishable in format from manual rows (except badge state)
- [ ] No Tally feature auto-commits without explicit estimator review
- [ ] Feature is useful without AI enabled (or gracefully absent if AI-only)
- [ ] Interaction is logged as a training signal with correct schema fields
- [ ] Trade context is applied from company profile — not re-prompted per session
- [ ] UI follows Zenbid design tokens (no color, spacing, or typography deviations)
- [ ] Feature works for at least two distinct trade sectors without code changes

---

## Roadmap Sequence

| Phase | Capability |
|---|---|
| 1 — Now | Passive mode: scope gap detection, confidence scoring, badge system |
| 2 — Next | Reactive mode: on-demand report generation, division summaries |
| 3 — Near | Generative mode: assembly generation from scope description |
| 4 — Future | Cross-estimate intelligence: variance analysis, win/loss correlation |
| 5 — Future | Fine-tuned model: Cost Intelligence tier on proprietary dataset |

---

*This document is the source of truth for all Tally-related product and engineering decisions. When a feature decision conflicts with this document, resolve it here first.*
