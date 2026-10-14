# GDTF Comparer

Compare a target GDTF fixture file against one or more comparison GDTF
files and see which attributes actually differ, side by side. You can
browse and search every attribute the files define, see differing values
highlighted (or show only the differences), and save the attributes you
care about as reusable compare profiles.

## Download and run (no Python needed)

No Python or other software is needed — just download the build for your
computer from the
[latest release](https://github.com/BEtheLED/GDTFComparer/releases/latest).

| Your computer | File to download |
| --- | --- |
| A Mac with Apple silicon (M1 or newer) | `GDTF-Comparer-macos.zip` |
| A Windows 10 or 11 PC | `GDTF-Comparer-windows.zip` |

The Mac version does not run on older Intel-based Macs.

### On a Mac

1. On the release page, click `GDTF-Comparer-macos.zip`. It goes to your
   Downloads folder.
2. Open Downloads in Finder and double-click the zip file. "GDTF Comparer"
   appears next to it.
3. Drag "GDTF Comparer" into your Applications folder.
4. Open Applications and double-click GDTF Comparer. The first time, macOS
   stops it with a message like "Apple could not verify 'GDTF Comparer' is
   free of malware" (the exact wording differs between macOS versions).
   Click **Done**, not Move to Trash.
5. Open **System Settings** from the Apple menu and click
   **Privacy & Security** in the sidebar.
6. Scroll down to the Security section. You'll see a note that GDTF
   Comparer was blocked — click **Open Anyway**. This button only shows
   for about an hour after step 4, so if it isn't there, double-click the
   app again and come back.
7. A window appears — click **Open Anyway** (on some versions this just
   says **Open**), then enter your Mac password or use Touch ID if asked.
8. From now on, a normal double-click opens the app.

On older macOS versions, the same button is under System Preferences, then
Security & Privacy, then General, instead of System Settings.

**If macOS says the app "is damaged and can't be opened"** — that message
has no Open Anyway button. Click **Cancel**, then open Terminal
(Applications, then Utilities, then Terminal). Paste this line exactly as
shown and press Return:

```bash
xattr -cr "/Applications/GDTF Comparer.app"
```

Close Terminal and double-click the app again. This clears the "downloaded
from the internet" mark from GDTF Comparer only — nothing else on your Mac
is affected.

### On Windows

1. On the release page, click `GDTF-Comparer-windows.zip`. If your browser
   says the file "isn't commonly downloaded," keep it anyway (in Microsoft
   Edge: click the three dots next to the download, then **Keep**, then
   **Show more**, then **Keep anyway**).
2. Open Downloads, right-click the zip file, choose **Extract All…**, then
   **Extract**.
3. Open the extracted "GDTF Comparer" folder and double-click "GDTF
   Comparer" (GDTF Comparer.exe). Keep the whole folder together — the app
   needs the `_internal` folder beside it. Move the whole folder somewhere
   permanent first (for example, Documents) if you like. For a desktop
   shortcut, right-click GDTF Comparer.exe, then **Show more options**,
   then **Send to**, then **Desktop (create shortcut)**.
4. The first time, a blue box says "Windows protected your PC." Click
   **More info**, then **Run anyway**.
5. Next time, just double-click the app.

If Windows says Smart App Control blocked the app, there is no Run anyway
button — Smart App Control blocks every app that isn't signed, so GDTF
Comparer can't run on that PC yet. We don't recommend switching Smart App
Control off for this; please tell us at the
[issues page](https://github.com/BEtheLED/GDTFComparer/issues).

If antivirus software removes the file, please report it at the
[issues page](https://github.com/BEtheLED/GDTFComparer/issues) rather than
changing your antivirus settings.

### Why do I see a warning?

GDTF Comparer is free, and its downloads are not signed with a paid Apple
or Microsoft developer certificate, so your computer can't confirm who
made them and asks you once. The steps above allow only GDTF Comparer and
change nothing else about your computer's security.

Only do this for a copy you downloaded from
https://github.com/BEtheLED/GDTFComparer/releases. If the file came from
anywhere else (email, chat, another website), delete it and download it
from that page instead.

Report a problem: https://github.com/BEtheLED/GDTFComparer/issues

## Requirements

Everything from here down is only needed to run GDTF Comparer from its source code.
To just use the app, see "Download and run (no Python needed)" above.

- Python 3.11+
- macOS, Windows, or Linux

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Any Python 3.11 or newer works (for example `python3.11` or `python3.12`) —
substitute the interpreter you have if `python3` doesn't resolve to one.

On Windows, use the equivalent commands:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

## Run

```bash
.venv/bin/gdtf-comparer
```

or, from the repo root, without installing the console script:

```bash
PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app
```

On Windows, substitute `.venv\Scripts\python`.

## Test

```bash
.venv/bin/python -m pytest
```

## Project Layout

- `src/gdtf_comparer/core/` — Qt-free parsing/comparison service (pygdtf
  wrapping, attribute extraction, comparison logic). Never imports Qt.
- `src/gdtf_comparer/gui/` — PySide6 presentation layer. Only talks to
  `core` through `core.comparator`, `core.models` and `core.errors`; never
  imports `pygdtf`, `zipfile` or `defusedxml` directly.
- `src/gdtf_comparer/app.py` — composition root: builds the `QApplication`,
  applies the OS-following qt-material theme, and shows the main window.
- `tests/core`, `tests/gui` — unit/integration tests for each layer;
  `tests/test_architecture.py` enforces the `core`/`gui` boundary above.

## Safety

Every selected `.gdtf` file is treated as untrusted input, including files
you pick yourself. Files over 100 MB, XML containing a DTD or external
entities, and zip archives with an implausible compression ratio (zip
bombs) are rejected with a friendly error message instead of being parsed.
Folders, named pipes and device files are refused with a friendly message
before anything is read from them.

## Blender Addon

This repository now also contains a minimal skeleton for a Blender addon that
aims to provide support for importing MVR and GDTF files. The addon lives in
the `blender_addon` directory and currently only defines the basic structure
needed for a Blender add-on.
