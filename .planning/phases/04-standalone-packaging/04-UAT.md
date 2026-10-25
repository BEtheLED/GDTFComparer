---
status: testing
phase: 04-standalone-packaging
source: [04-VERIFICATION.md]
started: 2026-10-25T15:15:00Z
updated: 2026-10-25T15:15:00Z
---

## Current Test

number: 1
name: Mac Gatekeeper walkthrough — download, bypass, run a real comparison
expected: |
  Download GDTF-Comparer-macos.zip with a real web browser (so macOS marks it as downloaded)
  from https://github.com/BEtheLED/GDTFComparer/releases/latest. Follow README.md's "On a Mac"
  steps exactly: unzip, move the app into Applications, first launch via System Settings >
  Privacy & Security > Open Anyway. Every screen should match what the README describes (a
  message like "Apple could not verify...", a GDTF Comparer note with an Open Anyway button,
  then a password or Touch ID prompt). Run a real comparison (Browse… for Target GDTF, Add
  Files… for a second fixture, Run Comparison) — the window should have the blue Material look
  and the comparison table should fill in. Quit and relaunch — second launch should open with no
  warning at all.
awaiting: user response

## Tests

### 1. Mac Gatekeeper walkthrough
expected: Browser download → Gatekeeper "Open Anyway" bypass matches README word for word → real comparison runs and fills the table → second launch has no warning
result: [pending]

### 2. Windows SmartScreen walkthrough
expected: Browser download on a real Windows 10/11 PC → "Windows protected your PC" → More info → Run anyway, matching README word for word → Defender does not remove the file → real comparison runs and fills the table → second launch has no warning
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
