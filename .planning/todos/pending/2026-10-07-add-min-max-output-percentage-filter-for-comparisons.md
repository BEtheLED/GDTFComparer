---
created: 2026-10-07T13:54:57.769Z
title: Add min/max output-percentage filter for comparisons
area: general
severity: major
files: []
---

## Problem

Comparisons currently treat fixtures purely on their raw spec values (e.g. beam
angle, power draw, output), so a fixture that's objectively "overkill" on paper
can still be the right practical choice when it will only be run at a reduced
output. Example raised by the user: comparing an Aura XB they'd only run at
30-40% output against an R2X Wash run at full — on raw specs the Aura XB looks
like overkill, but at the intended output level it may actually be a close or
reasonable match. There's currently no way to tell the comparison "treat this
fixture's output as if it were dialed down to X%" before judging how close it
is to the target.

## Solution

TBD. The user flagged the UX risk themselves: "How to make this easy to use
without taking forever or frustrating the user is going to be hard." Needs
design thought on:
- Where a min/max (or single target %) output field would live per
  comparison file — likely near the existing "Compare with" list rather than
  a global setting, since it's per-fixture.
- Whether this adjusts displayed attribute values (e.g. scaled
  LuminousFlux/PowerConsumption) or just the match-indicator dot logic, or
  both.
- Keeping the common case (no scaling, compare as-is) a zero-click default so
  this doesn't add friction for users who don't need it.
</content>
