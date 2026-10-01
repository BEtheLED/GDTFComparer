# Phase 3: Compare Profiles & Export - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-30
**Phase:** 3-Compare Profiles & Export
**Areas discussed:** Profile storage & management, Profile portability across fixtures, CSV export format & scope, Where the buttons live

---

## Profile storage & management

| Option | Description | Selected |
|--------|-------------|----------|
| Dropdown in the side panel | A small dropdown at the top of the Attributes panel to pick a saved profile | ✓ |
| Separate 'Open Profile' dialog | A popup window listing saved profiles by name | |

**User's choice:** Dropdown in the side panel

| Option | Description | Selected |
|--------|-------------|----------|
| Replace them entirely | Loading a profile clears current checks and checks exactly the profile's set | ✓ |
| Add to what's checked | Loading a profile adds to the current selection without unchecking anything | |

**User's choice:** Replace them entirely (confirmed again later, after the workflow was clarified — see Profile portability section below)
**Notes:** First time this was asked (before the real workflow was clarified), the user said "we should talk about this it sound like you don't get the workflow" — the question was re-asked after clarifying what a profile actually represents (see below), and the user then confirmed "Replace them entirely."

| Option | Description | Selected |
|--------|-------------|----------|
| Ask before overwriting | Confirmation popup before overwriting an existing profile name | ✓ |
| Just overwrite it | Silent overwrite | |
| Require a unique name | Block saving under a taken name | |

**User's choice:** Ask before overwriting

| Option | Description | Selected |
|--------|-------------|----------|
| Save + load is enough for now | No rename/delete this phase | |
| I want rename/delete too | Add profile management (rename/delete) | ✓ |

**User's choice:** I want rename/delete too
**Notes:** First time this was asked, the user said "define what profiles you are talking about" — re-asked after the workflow clarification below, with a concrete example ("Moving Head Spec" needing updates).

---

## Profile portability across fixtures

**Context/clarification (not an AskUserQuestion — free-text from the user):**
> "The goal of this tool is to help with flexibility in fixture replacement. In my design I might know some things that I need to have out of a fixture. Like color mixing or maybe a size max or power draw, or whatever it might be. I will ask for a type of fixture maybe MAC Aura XB for example, and the company that I am getting the fixture from might not have a MAC Aura but I can say I need these parts like color mixing and zoom and a max weight and as long as I have that I am okay so the company might look and have R2X wash and it fits so they can supply that vs sending me an email and asking they can just look and know what they can send."

This reframed "compare profile" from a convenience re-check shortcut into a reusable spec sheet used across unrelated fixture types for substitution/sourcing decisions.

| Option | Description | Selected |
|--------|-------------|----------|
| Tell me which ones didn't apply | Explicit message (e.g. status bar) when saved spec items aren't found in the current files | ✓ |
| Just show what's available, no message | Silently show only what exists, no notification | |

**User's choice:** Tell me which ones didn't apply
**Notes:** Rationale given: the user is making go/no-go sourcing calls from this, so silently dropping unmatched spec items risked giving false confidence that a candidate met requirements that were never actually checked.

---

## CSV export format & scope

**Note:** This area's outcome changed the phase's scope — see "Scope Flag" below. The option tables are preserved for audit purposes; treat the underlying feature as flagged for removal pending a requirements-doc update.

| Option | Description | Selected |
|--------|-------------|----------|
| Just what I've checked | CSV includes only checked properties | (user response: "I don't even know why I would need to export") |
| Everything, every property | Full raw dump regardless of checkboxes | |

**User's choice:** Did not pick an option — responded "I don't even know why I would need to export," which led to a direct scope-flag question (see below).

| Option | Description | Selected |
|--------|-------------|----------|
| Just flag any difference | Binary matches/doesn't-match, same as Phase 2 highlighting | |
| Something stricter (pass/fail) | Per-property tolerance/direction logic | |

**User's choice:** Neither — responded "I think a traffic light, red is not going to work, yellow is not that same but Acceptable, Green is direct match." Identified as a bigger feature (tolerance-rule system) and deferred to a future phase (see Deferred Ideas).

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include fixture names | CSV includes identifying header info | ✓ |
| No, just the data table | No extra header info | |

**User's choice:** Yes, include fixture names

| Option | Description | Selected |
|--------|-------------|----------|
| Two separate buttons | "Export Full CSV" and "Export Differences Only" as separate buttons | ✓ (low confidence) |
| One button with a choice | Single "Export CSV" with a full/diff-only choice | |

**User's choice:** "I don't know I guess 1" (Two separate buttons) — low-confidence answer; treat as provisional only if export is reinstated.

**Follow-up — Scope Flag:**

| Option | Description | Selected |
|--------|-------------|----------|
| Keep it as scoped | Continue with export as originally written in requirements | |
| Flag it for removal | Note for formal removal from REQUIREMENTS.md/ROADMAP.md rather than build something unused | ✓ |

**User's choice:** Flag it for removal
**Notes:** Export (EXPORT-01, EXPORT-02) has NOT been removed from REQUIREMENTS.md/ROADMAP.md yet — this is a flag for the user to act on outside this discussion, or to confirm before planning proceeds. See CONTEXT.md Scope Flag section.

---

## Where the buttons live

| Option | Description | Selected |
|--------|-------------|----------|
| Same panel, small toolbar row | Dropdown + Save + Manage all in the Attributes panel | ✓ |
| Main menu bar instead | A "Profiles" menu elsewhere | |

**User's choice:** Same panel, small toolbar row

---

## Claude's Discretion

- Exact CSV column layout, file naming convention, and default save location (contingent on the export Scope Flag being resolved in favor of keeping it).
- Visual/layout details of the profile toolbar row (icon vs. text buttons, dropdown width, how many profiles display before scrolling/searching is needed).

## Deferred Ideas

- **Red/Yellow/Green acceptability rating per property** (e.g. 5% over max weight = Yellow/Acceptable, missing a required feature = Red, exact match = Green). Requires defining tolerance/acceptability rules per attribute (numeric tolerance vs. feature presence vs. exact match) — nothing like this exists today. User explicitly asked this be noted for a future phase, not Phase 3.

## Scope Flag Raised

- User asked to flag CSV export (EXPORT-01, EXPORT-02) for removal from requirements, rather than build it. This was NOT applied to REQUIREMENTS.md/ROADMAP.md during this discussion — flagged prominently in CONTEXT.md for the user/planner to resolve before Phase 3 planning proceeds.
