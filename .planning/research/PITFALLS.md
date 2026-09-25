# Pitfalls Research

**Domain:** Desktop GDTF/MVR fixture-comparison tool — cross-platform packaging, GDTF/MVR/XML parsing, MVRxchange network protocol integration
**Researched:** 2026-09-25
**Confidence:** MEDIUM (web-sourced community/vendor knowledge; MVRxchange protocol specifics are LOW-MEDIUM — spec pages are thin and the protocol has no public reference implementation to cross-check against)

## Critical Pitfalls

### Pitfall 1: Shipping a "frozen" app that works on the dev machine but fails on a clean install

**What goes wrong:**
PyInstaller (and similar tools) bundle only what static analysis can detect. Tkinter's Tcl/Tk data files, hidden imports pulled in dynamically (e.g. by a plugin-style parsing library), and platform-specific binaries are silently omitted. The app runs fine on the developer's machine (where a system Python/Tk install papers over the gap) but crashes or shows a blank window on a clean macOS or Windows machine with no Python installed — exactly the target user.

**Why it happens:**
PyInstaller does not compile Python; it bundles the interpreter + bytecode + detected dependencies into an archive that self-extracts at runtime. Detection is static/heuristic, so dynamic imports, Tcl/Tk asset directories, and OS-specific extension modules are easy to miss. Developers test only on their own machine, which has all the "ambient" dependencies already installed.

**How to avoid:**
- Build and smoke-test on a genuinely clean VM/machine per target OS (no system Python, no dev tools) before calling packaging "done."
- Use `--onedir` builds during development/debugging (faster iteration, easier to inspect what got bundled) and only produce `--onefile` for final distribution if still desired.
- Explicitly test the packaged binary's file-dialog, zip-extraction, and XML-parsing paths — these touch OS-level file APIs that behave differently across platforms.
- For Tkinter specifically, verify Tcl/Tk data dirs are bundled (PyInstaller has hooks, but versions of Tcl/Tk on the build machine must match what's bundled).

**Warning signs:**
- App only ever tested via `python app.py`, never via the built artifact.
- No CI step that builds and launches the packaged app headlessly (or via smoke script) on macOS and Windows.
- "It worked when I ran the exe" reports only from the same machine that built it.

**Phase to address:** Packaging/distribution phase — should include a "clean machine" verification step as an explicit gate, not just "build succeeds."

---

### Pitfall 2: macOS Gatekeeper "app is damaged" blocking distribution to other users

**What goes wrong:**
An unsigned (or ad-hoc signed) `.app` built with PyInstaller opens fine for the developer but shows "app is damaged and can't be opened, move to Trash" for anyone else who downloads it — even via a simple zip/tar, because macOS quarantine-flags downloaded files and Gatekeeper refuses to run unsigned/unnotarized bundles from an "unidentified developer" once the quarantine bit differs from what a plain double-click bypass allows.

**Why it happens:**
Gatekeeper enforces code-signing + notarization for anything that isn't explicitly allowed by the user (right-click → Open once, which most non-technical users don't know to do). PyInstaller's `.app` output places `base_library.zip` and other loose files in `Contents/MacOS`, which can itself break notarization if not handled correctly. Full notarization requires a paid Apple Developer account ($99/yr), the hardened runtime, and specific entitlements — notably `com.apple.security.cs.allow-unsigned-executable-memory` for Python's dynamic code execution.

**How to avoid:**
- Decide early whether the project will pay for an Apple Developer account. If not, document the "right-click → Open" workaround prominently for users, and prefer `--onedir` distribution as a zip (drag out of quarantine more predictably) over a single unsigned binary.
- If signing: use the hardened runtime, add the entitlements PyInstaller's docs specify for Python apps, sign *after* the full bundle is assembled (including all bundled `.so`/`.dylib` files — every executable/library inside the bundle needs signing, not just the top-level binary), then notarize and staple the ticket.
- Budget real time for this — notarization failures are common on first attempt and debugging cycles (submit → wait → check log) are slow.

**Warning signs:**
- No macOS distribution ever tested by someone other than the developer on a different Mac.
- Users report "damaged" or "unidentified developer" dialogs.
- Signing/notarization treated as a last-minute step rather than part of the packaging phase.

**Phase to address:** Packaging/distribution phase (macOS track). Should be verified with an actual second machine/second Apple ID download, not just `codesign --verify` locally.

---

### Pitfall 3: Windows SmartScreen / antivirus flags the built .exe as malware

**What goes wrong:**
A freshly built PyInstaller `.exe`, especially `--onefile`, gets flagged by Windows Defender or third-party AV as a trojan/generic threat, or SmartScreen shows "Windows protected your PC" with a scary "don't run this" default — for a tool that a lighting professional downloaded specifically to try. This kills adoption instantly for non-technical users who won't click through "More info → Run anyway."

**Why it happens:**
PyInstaller's bootloader stub is reused by malware authors constantly, so its byte signature is on many heuristic blocklists. `--onefile` self-extracts to a temp dir at startup, which looks like classic dropper behavior to AV heuristics. Unsigned binaries have no reputation with SmartScreen's cloud reputation system, so cold downloads are treated with maximum suspicion regardless of actual content.

**How to avoid:**
- Prefer `--onedir` over `--onefile` for the primary distribution — no runtime self-extraction, and it's the most-cited fix for AV false positives.
- Code-sign the Windows binary if at all affordable (even an inexpensive OV cert helps SmartScreen reputation build up over downloads far faster than unsigned).
- Compile the PyInstaller bootloader locally rather than using the pip-distributed prebuilt one — changes the binary hash away from known-flagged signatures.
- Proactively submit the built binary to Microsoft (Defender) and major AV vendors for false-positive review before public release; most respond within hours to days.
- Document the SmartScreen click-through path for users in the README/release notes so it's not a surprise.

**Warning signs:**
- No AV/VirusTotal scan run against release builds before publishing.
- User reports of "Windows says this is a virus" with no prepared response/documentation.

**Phase to address:** Packaging/distribution phase (Windows track). Add a pre-release checklist item: scan build with VirusTotal, note any detections, decide whether to pursue signing.

---

### Pitfall 4: Treating GDTF's flat-attribute extraction as "the parser" instead of a real GDTF-spec-aware reader

**What goes wrong:**
The existing hand-rolled parser (`parse_gdtf()`) walks every XML element and dumps all attributes into one flat dict, so `Name="Iris"` on a `<Geometry>` collides with `Name="Iris"` on a `<Channel>` or `<Wheel>`, and there is no notion of which section (Geometries vs. DMXModes vs. PhysicalDescriptions) an attribute came from. When this milestone swaps in MVRxchange-adjacent parsing libraries (e.g. `python-gdtf`), it's tempting to keep the same flat comparison model on top of the new library's richer object model — silently reintroducing the same collision bug with a fancier data source.

**Why it happens:**
GDTF's `description.xml` is a hierarchical spec (FixtureType → Geometries, DMXModes, PhysicalDescriptions, Wheels, etc.) with mandatory sections and repeated attribute names across different node types by design (e.g. many nodes have a `Name` attribute). A flat dict model is the easiest thing to write against any tree, but it throws away the structure that disambiguates identical attribute names.

**How to avoid:**
- Model comparisons around GDTF's actual sections/paths (e.g. `Geometries/Geometry[@Name]`, `DMXModes/DMXMode/DMXChannel`, `PhysicalDescriptions/Properties`) rather than a global attribute bag.
- If adopting `python-gdtf` (MIT-licensed, actively maintained, used by BlenderDMX) or an MVRxchange-derived parsing library, use its structured object model (typed access to DMX modes, channels, geometries) directly rather than flattening its output back into a generic dict.
- Add regression tests using real-world GDTF files from multiple manufacturers (ETC, Martin, Chauvet, Robe) — different tools produce structurally-valid-but-differently-shaped XML (e.g. varying nesting depth, optional sections present/absent) and this is where naive parsers break.

**Warning signs:**
- Comparison output shows two clearly-different fixture properties as "the same value" or vice versa, because they share an attribute name from different XML nodes.
- New parsing code still funnels through a single `dict[str, str]`-shaped intermediate representation.

**Phase to address:** GDTF/MVRxchange parsing integration phase. Verification: unit tests comparing known-distinct attributes (e.g. `Name` on a Geometry vs. `Name` on a DMXChannel) don't collide.

---

### Pitfall 5: Parsing untrusted GDTF/MVR XML with the stdlib parser (XXE / billion-laughs DoS)

**What goes wrong:**
GDTF/MVR files are just ZIP archives containing XML that the app will parse from two untrusted sources this milestone: files the user picks off disk (could come from anywhere — a colleague, a random manufacturer download, a file received over MVRxchange) and, once MVRxchange networking is added, files/data received directly from other stations on the network with zero prior vetting. Python's `xml.etree.ElementTree` (used today) and `xml.dom.minidom`/`xml.sax` all sit on top of `expat` without hardened defaults, so a malicious `description.xml` or `GeneralSceneDescription.xml` with a crafted `<!ENTITY>` chain can trigger exponential memory/CPU blowup (billion-laughs) from a document a few KB in size, freezing or crashing the app.

**Why it happens:**
`ElementTree.parse(user_supplied_file)` looks identical whether the file is trusted or not — nothing in the API signals "this needs hardening." Most tutorials and the current codebase treat XML parsing as inherently safe because "it's just data files," ignoring that GDTF/MVR files are now an attacker-reachable input class once network exchange is added.

**How to avoid:**
- Swap `xml.etree.ElementTree` for `defusedxml.ElementTree` everywhere GDTF/MVR XML is parsed — it's a drop-in import replacement that blocks XXE, external DTD retrieval, billion-laughs, quadratic blowup, and malicious namespace expansion with no other code changes.
- Apply this to *all* XML entry points: file-picked GDTF/MVR files, and any MVR/GDTF payload arriving via the MVRxchange protocol.
- If adopting a third-party GDTF/MVR parsing library, check whether it already uses a hardened parser — don't assume it.

**Warning signs:**
- Any `import xml.etree.ElementTree` (or `minidom`/`sax`) remaining in code paths that touch files from disk-pick or network.
- No test with a maliciously-crafted small XML file (entity bomb) verifying the app rejects/times out gracefully instead of hanging or OOM-crashing.

**Phase to address:** GDTF/MVR parsing integration phase — swap parser as part of the "robust parsing" work, before MVRxchange networking phase begins (networking multiplies the attack surface for the same bug).

---

### Pitfall 6: Zip-bomb / oversized-archive DoS via GDTF/MVR files (local or network-received)

**What goes wrong:**
GDTF and MVR files are ZIP archives. A file (whether picked from disk or pulled down via an `MVR_REQUEST` over the network) can claim a small compressed size but expand to gigabytes on extraction, exhausting disk or memory and hanging the app — especially dangerous once MVRxchange lets a remote peer push/announce files with no size cap enforced by the protocol itself.

**Why it happens:**
`zipfile` extraction (and especially the "copy to temp dir then extract" pattern already present in the codebase) doesn't check compression ratio or total uncompressed size before extracting. The existing code has no file-size limit at all (see CONCERNS.md — "No File Size Limits"), and that gap becomes more dangerous when the file source is a network peer rather than a deliberate user file-pick.

**How to avoid:**
- Enforce a sane max file size (e.g. reject GDTF/MVR files above some threshold like 100-200MB) before attempting extraction, for both local file-pick and MVRxchange-received files.
- Before extracting, inspect `ZipInfo.file_size` / `compress_size` for each entry and reject archives with implausible compression ratios or entry counts, rather than trusting the archive's own metadata blindly during extraction.
- Extract to a bounded temp location using `tempfile.TemporaryDirectory()` (auto-cleanup) rather than manual `shutil.rmtree`, and set a ceiling on total bytes written during extraction (abort if exceeded mid-stream).

**Warning signs:**
- No size/ratio check exists before `ZipFile.extractall()` or per-member `.extract()` calls.
- Temp directory cleanup relies solely on a `finally: shutil.rmtree()` with no fallback (already flagged in CONCERNS.md as fragile).

**Phase to address:** Parsing-robustness phase (local files) and re-verified in the MVRxchange networking phase (network-received files) — same defense, two trust boundaries to apply it at.

---

### Pitfall 7: Bolting MVRxchange networking directly onto the Tkinter/GUI mainloop causes freezes or crashes

**What goes wrong:**
MVRxchange is network I/O by nature — mDNS discovery, TCP or WebSocket connections, waiting on peers to respond to `MVR_REQUEST`. If any of this runs synchronously on the GUI thread (the natural first instinct — "just call the client library from the button handler"), the entire UI freezes for the duration of every network operation, and any failure (timeout, unreachable peer, malformed response) either hangs indefinitely or throws an unhandled exception that crashes the whole app. GUI toolkits are event-loop-based and only process one thing at a time on the main thread.

**Why it happens:**
Tkinter's `mainloop()` must keep running to remain responsive; any blocking call inside a callback stalls it. Networking libraries (raw sockets, `asyncio`-based WebSocket clients like `websockets`) are designed to run their own event loop, which conflicts with Tkinter's if naively combined on one thread ("No current event loop" errors are the most common symptom when asyncio code is dropped into a Tkinter callback without its own loop).

**How to avoid:**
- Run all MVRxchange networking (mDNS discovery, TCP/WebSocket client, message handling) on a dedicated background thread with its own explicitly-created asyncio event loop (`asyncio.new_event_loop()` + `asyncio.set_event_loop()` in that thread), never the GUI thread.
- Communicate between the network thread and the GUI thread only via a thread-safe `queue.Queue` (or Tkinter's `after()` polling pattern) — never call Tkinter widget methods directly from the network thread; Tcl's threading model is not the same as Python's and cross-thread Tk calls raise "apartment" errors or corrupt state.
- Wrap every network operation in explicit timeouts and try/except, surfacing failures back to the GUI thread as a queued "error" message rather than letting exceptions propagate silently in the background thread (background-thread exceptions do NOT crash the main thread in Python — they silently vanish unless deliberately caught and reported, which is its own trap: failures look like nothing happened instead of a visible error).

**Warning signs:**
- Any direct call from a network callback/thread into a `ttk.Treeview` or other Tk widget method.
- UI becomes unresponsive ("spinning beachball"/"Not Responding") during MVRxchange discovery or file requests.
- Network errors during MVRxchange operations produce no user-visible feedback at all (silent failure) rather than a dialog/status message.

**Phase to address:** MVRxchange networking integration phase — architecture should be decided (background thread + queue, or a dedicated async runtime) before any protocol code is written, since retrofitting threading onto already-written synchronous network code is expensive.

---

### Pitfall 8: Trusting MVRxchange network peers and their file payloads by default

**What goes wrong:**
The MVRxchange protocol specification (per gdtf.eu) defines no authentication, encryption, or file-integrity verification — it relies on UUID matching alone, with no cryptographic checks. Any station on the local network (mDNS/TCP mode) or reachable via the configured WebSocket relay can announce itself, claim file commits, and push MVR/GDTF data that this app will then parse and display. Without deliberate hardening, "integrate with MVRxchange" silently becomes "parse arbitrary XML/ZIP data from anyone on the network as if it were a trusted local file" — compounding Pitfalls 5 and 6 with a much larger, adversarial-by-default trust boundary (any device on the same LAN, or relay, not just files the user deliberately chose).

**Why it happens:**
The protocol was designed for trusted professional environments (a lighting console and a visualizer on the same show network), so the spec authors left security out of scope, assuming implementers/network operators handle it. Developers integrating the protocol tend to focus on "does the exchange work" and treat protocol conformance as equivalent to safety.

**How to avoid:**
- Treat every byte received via MVRxchange (JOIN announcements, COMMIT metadata, REQUEST responses/file payloads) as fully untrusted input, subject to the same hardened-XML-parsing (Pitfall 5) and size/zip-bomb limits (Pitfall 6) as local files — no exceptions for "it came from the network protocol so it must be a valid MVR file."
- Validate structural conformance (required root elements, GDTF/MVR data-version attributes, plausible file sizes) before acting on any received file, and fail closed (reject + log) rather than best-effort parsing malformed data.
- Make network participation opt-in and clearly scoped (e.g. only listen/respond on explicit user action, not automatically on app launch) so the app isn't silently exposing a listening service to every device on a shared/public network (coffee-shop wifi, conference venue network) the user's laptop happens to be on.
- Consider showing provenance (which station/peer sent a file) in the UI before the user acts on received data, since the protocol itself provides no trust signal beyond a self-reported station name/UUID.

**Warning signs:**
- MVRxchange listener starts automatically on app launch with no user opt-in.
- Received files/messages are parsed with the same code path as local files but with even less validation (because "the protocol already validated it").
- No visible indication in the UI of where a compared/loaded fixture file actually came from (local disk vs. network peer).

**Phase to address:** MVRxchange networking integration phase — should be explicitly scoped as "network protocol + accompanying trust boundary," not just "protocol wire format implementation." Verification: test with a deliberately malformed/oversized payload sent from a peer and confirm graceful rejection, not a crash or hang.

---

### Pitfall 9: MVRxchange feature creep drowning the core comparison value

**What goes wrong:**
MVRxchange is a full bidirectional collaboration protocol (join sessions, commit revisions, request files from multiple peers, handle session-host handoff) built for consoles and visualizers to stay in sync. The stated milestone goal is comparison + sync of fixture/scene data — it's easy to end up half-implementing a general-purpose MVRxchange station (discovery, hosting, multi-peer session state) when the actual user need is much narrower (e.g. "pull the current rig from the network instead of browsing for a file").

**Why it happens:**
Protocol specs describe the full feature surface, and "integrate with MVRxchange" reads as "implement the protocol," not "implement the one or two message flows this app's users actually need."

**How to avoid:**
- Scope MVRxchange integration narrowly in the roadmap: decide up front which message types are actually needed (likely `MVR_JOIN` to discover peers + `MVR_REQUEST`/receiving `MVR_COMMIT` to pull a file for comparison) versus full session-hosting behavior, and treat the rest as explicitly out of scope for this milestone.
- Prefer read/pull-oriented integration first (app requests/receives MVR data to populate comparison) before considering the app also acting as a host/source other tools pull from, since the latter multiplies both protocol surface and security exposure (Pitfall 8).

**Warning signs:**
- Roadmap phase for MVRxchange has no explicit list of which message types/flows are in scope.
- Networking work balloons into implementing session-hosting, multi-peer state management, etc. before the basic "receive one file over the network and compare it" flow works end-to-end.

**Phase to address:** Requirements/roadmap phase — scope the MVRxchange integration to specific message flows before planning the implementation phase.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Keep flat attribute-dict comparison model on top of a new structured parser | Fast to wire up, minimal rewrite of comparison/diff UI code | Reintroduces name-collision bugs (Pitfall 4); wastes the structure the new parser provides | Never for this milestone — the whole point of swapping parsers is to fix this |
| Ship `--onefile` PyInstaller build for speed of "it works" | One file is simpler to hand someone | Higher AV false-positive rate, slower cold start, harder to debug what's missing (Pitfalls 1 & 3) | Acceptable for early internal testing; switch to `--onedir` (or a proper installer) before wider distribution |
| Run MVRxchange client code directly on the GUI thread during initial prototyping | Fastest way to see the protocol "work" | UI freezes, silent failures, hard-to-retrofit threading later (Pitfall 7) | Acceptable only behind a throwaway CLI/test script, never merged into the GUI app |
| Skip defusedxml swap "since GDTF files are usually from trusted manufacturers" | Saves a dependency + import change | One malicious/corrupt file (local or, worse, from a network peer) can hang or crash the app (Pitfall 5) | Never acceptable once MVRxchange network input exists |
| No file-size/zip-bomb guard before extraction | Simpler extraction code | DoS vector once files can arrive from network peers, not just deliberate user picks (Pitfall 6) | Acceptable only if the milestone stays local-file-only; not acceptable once MVRxchange ships |
| Defer macOS notarization/Windows signing indefinitely ("ship unsigned, add later") | No cost/cert setup needed now | Every future release repeats the "damaged app" / SmartScreen support burden; users churn before adoption takes hold | Acceptable for a personal-use-only build; not acceptable once "other lighting/AV professionals" are the stated audience (per PROJECT.md) |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|-------------------|
| MVRxchange (mvrdevelopment/tools) | Treating the repo as a ready-made client/server library to import | The repo primarily ships schemas (XSD), a Schematron validator, and a Wireshark dissector for protocol analysis/debugging — not a batteries-included MVRxchange client SDK. Expect to implement the message flow (JOIN/COMMIT/REQUEST) against the JSON/WebSocket or TCP wire format directly, using the dissector to verify traffic while developing |
| GDTF/MVR parsing libraries (e.g. `python-gdtf`, `python-mvr`) | Flattening the library's structured object model back into a generic `dict[str,str]` to minimize changes to existing comparison code | Redesign the comparison/diff layer around the library's typed model (sections, geometries, channels) so structure — and thus disambiguation — is preserved end to end |
| PyInstaller + Tkinter/PySide | Assuming a working dev-machine build means packaging is "done" | Test on a genuinely clean VM per OS as a required packaging-phase gate (Pitfall 1) |
| zipfile-based GDTF/MVR extraction | Trusting archive-declared sizes and extracting straight to a temp dir with only a `finally: rmtree` | Validate size/ratio before extracting; use `tempfile.TemporaryDirectory()` for guaranteed cleanup even on crash |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| Flat all-attributes extraction re-walking entire XML tree per file, per comparison run | Slow/laggy comparison on large GDTF files (already flagged in CONCERNS.md) | Parse once per file, cache structured result; only re-parse on file change | Noticeable above a few thousand XML elements, i.e. moderately complex fixtures |
| Synchronous mDNS discovery blocking GUI thread while waiting for peer responses | UI freeze whenever "find MVRxchange peers" is triggered | Background thread + queue-based UI updates (Pitfall 7) | Any network with discovery latency (multi-hop networks, WiFi vs wired) — not just "slow" networks |
| Unbounded zip extraction | Disk/memory exhaustion on a single malformed or oversized file | Size ceilings + ratio checks before extraction (Pitfall 6) | Any file at or above the "reasonable GDTF/MVR size" the app hasn't explicitly bounded |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Parsing GDTF/MVR XML with stock `xml.etree.ElementTree` once files can arrive over the network | XXE / billion-laughs DoS from a malicious or corrupted file, local or remote | Swap to `defusedxml.ElementTree` everywhere (Pitfall 5) |
| No cap on extracted archive size | Disk/memory exhaustion (zip bomb), especially dangerous once triggerable by network peers | Enforce max compressed and max uncompressed size before extracting (Pitfall 6) |
| MVRxchange listener auto-starting with no user awareness | App silently exposes a network service on whatever network the laptop is connected to (untrusted WiFi) | Require explicit user opt-in to start network participation; show connection/listening state in the UI |
| Treating MVRxchange peer data as pre-validated because "the protocol handles it" | Protocol spec defines no authentication/encryption/integrity checks (verified against gdtf.eu spec page) — false sense of safety | Apply the same untrusted-input handling to network-received files as to arbitrary local files (Pitfall 8) |
| File path entry field accepting pasted paths with no validation (existing issue, CONCERNS.md) | Path traversal / reading unintended files if carried forward into new UI | Validate paths resolve within expected locations; prefer file-dialog-only selection in the new UI, or sanitize pasted input |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Silent background-thread exceptions during MVRxchange operations | User clicks "sync with network" and nothing visibly happens — looks broken, no error shown | Route all background-thread errors through the same queue used for results, surfaced as a status message or dialog |
| Gatekeeper/SmartScreen warnings with no in-app or README guidance | Non-technical lighting/AV users abandon the app at first launch, assuming it's malware | Ship clear "how to open this the first time" instructions alongside the release; consider signing to eliminate the warning entirely |
| Diff highlighting that only shows "different" vs "same" with no indication of attribute *source* (which GDTF section it came from) | Users see two rows both called "Name" differ, without knowing one is a geometry name and one is a channel name — confusing, erodes trust in the tool | Show section/path context alongside each compared attribute once parsing is structure-aware (ties to Pitfall 4 fix) |

## "Looks Done But Isn't" Checklist

- [ ] **Standalone packaging:** Builds successfully locally — verify it was also launched on a machine with zero Python/Tk installed, for both macOS and Windows, not just "the build command exited 0."
- [ ] **macOS distribution:** App opens for the developer — verify a *second* person, on a *different* Mac, downloading via browser (so the quarantine bit is set), can open it without a Terminal workaround they weren't told about.
- [ ] **GDTF/MVR parsing swap:** New parser library integrated — verify attribute name collisions across different GDTF sections (e.g. `Name` on Geometry vs. `Name` on DMXChannel) are resolved correctly, not just that "parsing doesn't crash."
- [ ] **XML hardening:** `defusedxml` (or equivalent) added as a dependency — verify it's actually the import used at every XML-parsing call site, not just present in `requirements.txt`/`pyproject.toml` unused.
- [ ] **MVRxchange networking:** Protocol messages send/receive successfully on the happy path — verify behavior with a malformed/oversized/unexpected payload from a peer (doesn't hang, doesn't crash, shows an error).
- [ ] **Threading:** No visible UI freeze during a demo — verify by testing with an intentionally slow/unreachable network peer (e.g. block the port), not just a fast local peer.
- [ ] **Error handling:** `messagebox` import fixed — verify by testing every user-facing error path (corrupt file, missing description.xml, network timeout, malformed peer payload) actually shows a dialog instead of crashing or silently doing nothing.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|-----------------|------------------|
| Shipped unsigned macOS build causing "damaged" errors | MEDIUM | Set up Apple Developer account, add hardened-runtime entitlements, re-sign + notarize + staple existing build; re-release |
| PyInstaller `.exe` flagged as malware post-release | LOW-MEDIUM | Switch to `--onedir`, recompile bootloader locally, submit to AV vendors for false-positive review, re-release with updated docs |
| Attribute collisions discovered after structured parser was already flattened back to a dict | MEDIUM | Refactor comparison layer to consume the structured model directly; likely requires touching the diff/highlight UI code too, not just the parser |
| XXE/zip-bomb vulnerability discovered post-release (network integration already shipped) | MEDIUM-HIGH | Patch parsing layer immediately (defusedxml + size limits) and treat as a security release; audit whether any received files were already mishandled |
| MVRxchange listener found to be auto-starting without user awareness | LOW | Gate behind explicit opt-in setting/button; ship as a point release |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| Frozen app fails on clean machine (#1) | Packaging/distribution phase | Launch built artifact on a VM/machine with no Python/Tk installed, both OSes |
| macOS Gatekeeper "damaged" (#2) | Packaging/distribution phase (macOS) | Second person opens the downloaded build on a different Mac without prior instructions |
| Windows SmartScreen/AV false positive (#3) | Packaging/distribution phase (Windows) | VirusTotal scan of release build before publishing |
| Flat attribute collisions carried into new parser (#4) | GDTF/MVRxchange parsing integration phase | Unit test: same-named attributes from different GDTF sections stay distinct in comparison output |
| XXE/billion-laughs on untrusted XML (#5) | Parsing-robustness phase, re-verified before MVRxchange networking phase | Feed a crafted entity-bomb XML file to the parser; confirm rejection, not hang/crash |
| Zip-bomb / oversized archive DoS (#6) | Parsing-robustness phase, re-verified in MVRxchange networking phase | Feed an oversized/high-ratio archive; confirm rejection with bounded resource use |
| GUI freeze from synchronous networking (#7) | MVRxchange networking integration phase | Simulate slow/unreachable peer; confirm UI stays responsive and shows a timeout/error |
| Untrusted network peer data (#8) | MVRxchange networking integration phase | Send malformed/adversarial payload from a test peer; confirm graceful, visible rejection |
| MVRxchange scope creep (#9) | Requirements/roadmap phase | Roadmap phase description names the specific message types/flows in scope before implementation planning |

## Sources

- [PyOxidizer comparisons doc](https://pyoxidizer.readthedocs.io/en/v0.6.0/comparisons.html)
- [Sparx Engineering: PyInstaller vs Nuitka vs cx_Freeze](https://sparxeng.com/blog/software/python-standalone-executable-generators-pyinstaller-nuitka-cx-freeze)
- [pyinstaller/pyinstaller issue #7937 — signed exe fails after notarization](https://github.com/pyinstaller/pyinstaller/issues/7937)
- [pyinstaller/pyinstaller issue #5112 — code signing/notarization fails on .app bundles](https://github.com/pyinstaller/pyinstaller/issues/5112)
- [Signing and notarizing a Python macOS UI application (haim.dev)](https://haim.dev/posts/2020-08-08-python-macos-app)
- [pythonguis.com — Antivirus false positives with PyInstaller](https://www.pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller/)
- [pyinstaller/pyinstaller issue #6754 — onefile exe AV false positive](https://github.com/pyinstaller/pyinstaller/issues/6754)
- [mvrdevelopment/spec — gdtf-spec.md](https://github.com/mvrdevelopment/spec/blob/main/gdtf-spec.md)
- [GDTF & MVR Help Pages — File Format Definition](https://gdtf-development.com/help/developers/gdtf_1_2/file-format-definition/index.html)
- [open-stage/python-gdtf](https://github.com/open-stage/python-gdtf)
- [open-stage/python-mvr](https://github.com/open-stage/python-mvr)
- [GDTF Hub — MVR file format definition](https://www.gdtf.eu/mvr/mvr-spec/file-format-definition/)
- [mvrdevelopment/tools GitHub repo](https://github.com/mvrdevelopment/tools)
- [GDTF Hub — Exploring MVR-xchange Protocol with Wireshark](https://www.gdtf.eu/blog/exploring-mvr-xchange-protocol-with-wireshark/)
- [GDTF Hub — MVR-xchange communication protocol spec](https://www.gdtf.eu/mvr/mvr-spec/xchange/)
- [Sourcery — Python XXE vulnerability](https://www.sourcery.ai/vulnerabilities/python-lang-security-use-defused-xml-parse)
- [defusedxml on PyPI](https://pypi.org/project/defusedxml/)
- [Zip bomb — Wikipedia](https://en.wikipedia.org/wiki/Zip_bomb)
- [python.org bugs.python.org #39341 — zipfile ZIP Bomb vulnerability discussion](https://bugs.python.org/issue39341)
- [python-forum.io — dealing with code that blocks the Tkinter mainloop](https://python-forum.io/thread-17843.html)
- [discuss.python.org — Connecting Asyncio and Tkinter event loops](https://discuss.python.org/t/connecting-asyncio-and-tkinter-event-loops/14722)
- [tkthread on PyPI — thread-safe Tkinter calls](https://pypi.org/project/tkthread/0.2.0)
- `.planning/codebase/CONCERNS.md` — existing baseline issues referenced throughout (personal/project knowledge)

**Confidence note:** Stack/packaging and XML-security findings are broadly corroborated across multiple independent sources (MEDIUM). MVRxchange protocol details (message types, security model) rely primarily on a single vendor page (gdtf.eu) with no independent reference implementation to cross-check — treat protocol specifics as MEDIUM-LOW confidence and re-verify against the actual `mvrdevelopment/spec` repo's `mvr-spec.md`/xchange spec text during the MVRxchange implementation phase, not just this summary.

---
*Pitfalls research for: GDTF/MVR lighting-fixture comparison desktop app*
*Researched: 2026-09-25*
