# Phase 5: MVR Import & Fixture Substitution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-24
**Phase:** 05-mvr-import-fixture-substitution
**Areas discussed:** Scope fork, Importance model, Candidate source, Match output, Workflow integration, Matching strictness, Workflow pacing, Candidate library existence, Direction rule, Requirements sharing, Shop data needs, MVR custom-data feasibility, Import dedup

---

## Scope fork: how should this fit the roadmap?

| Option | Description | Selected |
|--------|-------------|----------|
| Redefine Phase 5 | Drop live-LAN-discovery framing; Phase 5 becomes file-based MVR import + importance marking + replacement finder | ✓ |
| New Phase 6, keep Phase 5 as-is | Leave Phase 5 as LAN networking for later; new phase for the file-based workflow | |
| Fold into Phase 5, keep networking too | Phase 5 grows to cover both networking and the new file-based workflow | |

**User's choice:** Redefine Phase 5 (Recommended)
**Notes:** Live LAN discovery (former NET-01/02/03) moved to REQUIREMENTS.md v2.

---

## Importance: what does "mark what's important" mean?

| Option | Description | Selected |
|--------|-------------|----------|
| One shared checklist for all fixtures | Reuse the existing Compare Profile concept, applied uniformly | |
| Per-fixture importance | Each fixture type gets its own independent checklist | ✓ |

**User's choice:** Per-fixture importance (Recommended)

---

## Candidates: where do replacement fixtures come from?

| Option | Description | Selected |
|--------|-------------|----------|
| A folder you maintain | User-managed local folder of GDTF files from various manufacturers, scanned by the app | ✓ |
| You pick candidates manually | Browse to specific GDTF files one at a time, like today's comparison picker | |

**User's choice:** A folder you maintain (Recommended)

---

## Match output: what should "find a replacement" show?

| Option | Description | Selected |
|--------|-------------|----------|
| Ranked list, best match first | Candidates scored and sorted best-to-worst | ✓ (refined below) |
| Simple match/no-match per candidate | Pass/fail only, no ranking | |

**User's choice:** Ranked list, best match first (Recommended) — later refined into the three-state traffic-light model (see "Matching strictness" below), which drives the ranking rather than replacing it.

---

## Workflow integration: how does MVR import fit the current picker?

| Option | Description | Selected |
|--------|-------------|----------|
| MVR import builds the file list | Importing an MVR produces the comparison set automatically | ✓ |
| Separate standalone tool | A different screen/mode untouched by today's workflow | |

**User's choice:** MVR import builds the file list (Recommended)

---

## Matching strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Close enough counts | Numeric tolerance band, not exact match | (superseded) |
| Exact match only | Every attribute must be identical | |

**User's free-text answer:** "3 light system, green meets or is better (note some fields might be lower is better) yellow it's close so it might work. Red way outside the set range will not work. Ask questions if needed."

**Notes:** This replaced the simple tolerance-band framing with an explicit three-state (green/yellow/red) model, captured verbatim in CONTEXT.md D-10. Follow-up questions were asked (and answered) about direction rules and per-attribute tolerance as a direct result of this answer.

---

## Workflow pacing

| Option | Description | Selected |
|--------|-------------|----------|
| One fixture at a time | Pick one, mark its requirements, search — repeat as needed | ✓ |
| All fixtures at once, batch report | Mark everything up front, one combined report | |

**User's choice:** One fixture at a time (Recommended)

---

## Candidate library existence

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, I have one (or will point to one) | A folder already exists or can be gathered | |
| Not yet — need to figure that out | No such folder exists yet | ✓ |

**User's choice:** Not yet — need to figure that out
**Notes:** Resolved in the next round: the user collects candidate GDTF files themselves (from GDTF-Share, manufacturer sites, etc.); the app only needs to scan a folder, no built-in acquisition feature.

---

## Direction rule (higher/lower/closer-is-better)

**First pass answer (free text):** "The workflow should be that the LD imports the MVR and sets what is needed for each GDTF. They or a local shop can then use the GDTF Comparer with the info set by the LD to see what in their inventory can be used."

**Notes:** This answer revealed the two-role (LD / shop) workflow shape rather than directly answering the direction-rule question, so it was re-asked cleanly in the next round.

| Option (re-asked) | Description | Selected |
|--------|-------------|----------|
| Smart default, LD can override | App guesses sensibly per attribute, LD can flip it | ✓ |
| LD picks manually every time | No guessing, full manual control every time | |

**User's choice:** Smart default, LD can override (Recommended)

---

## Requirements sharing (LD → shop)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — a saved/exportable spec file | LD saves requirements to a file, sends it to the shop | ✓ (after a technical detour) |
| No — always the same machine/session | No handoff needed | |

**User's free-text answer (technical detour):** "MVR files allow for extra data correct? If so we could just use that? Might find some workflow gaps so maybe a separate file might be better."

**Claude's response:** Explained that MVR is a spec-governed General Scene Description format with no known generic custom-data extension point, and that embedding custom data risks being dropped/mangled by other lighting software that resaves the file. Recommended a separate sidecar file instead.

**User's follow-up:** "I was concerned about that when working at Vectorworks too, lets make a separate file to reduce frustration."

**Final decision:** Separate, standalone shareable requirements file — never embedded in the MVR (CONTEXT.md D-08), confirmed by the user's own professional experience.

---

## What the shop needs

| Option | Description | Selected |
|--------|-------------|----------|
| Just the fixture requirements | Only the one fixture's important attributes + tolerances | ✓ |
| The whole MVR file | The complete show file, every fixture | |

**User's choice:** Just the fixture requirements (Recommended)

---

## Import dedup

| Option | Description | Selected |
|--------|-------------|----------|
| One entry per unique GDTF type | Duplicates in the plot collapse to a single entry | ✓ |
| One entry per physical fixture instance | Every individual fixture instance listed separately | |

**User's choice:** One entry per unique GDTF type (Recommended)

---

## Claude's Discretion

- Exact on-disk format of the fixture-requirements file (likely JSON, mirroring `core/profile_repository.py`'s atomic-write pattern).
- UI flow/screen layout for marking importance, exporting/importing requirements, and the ranked-results view.
- Smart-default direction rules per GDTF attribute (which attributes are "higher is better" vs "lower is better" vs "closest to target").
- Tie-breaking logic for the ranked list when candidates have equal green/yellow/red counts.

## Deferred Ideas

- Live LAN discovery of other MVR-xchange stations (formerly NET-01) — moved to REQUIREMENTS.md v2.
- Live MVR pull from a discovered station over the network (formerly NET-02) — moved to REQUIREMENTS.md v2.
- Built-in browsing/downloading of an online GDTF database (e.g. GDTF-Share integration) to acquire candidate fixtures — explicitly out of scope; user manages their own folder.
