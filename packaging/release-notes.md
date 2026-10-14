## Download and run (no Python needed)

No Python or other software is needed.

| Your computer | File to download |
| --- | --- |
| A Mac with Apple silicon (M1 or newer) | `GDTF-Comparer-macos.zip` |
| A Windows 10 or 11 PC | `GDTF-Comparer-windows.zip` |

The Mac version does not run on older Intel-based Macs.

### On a Mac

1. Download `GDTF-Comparer-macos.zip` above. It goes to your Downloads
   folder.
2. Open Downloads in Finder and double-click the zip file. "GDTF Comparer"
   appears next to it.
3. Drag "GDTF Comparer" into your Applications folder.
4. Open Applications and double-click GDTF Comparer. The first time, macOS
   stops it with a message like "Apple could not verify 'GDTF Comparer' is
   free of malware" (the exact wording differs between macOS versions).
   Click **Done**, not Move to Trash.
5. Open **System Settings** from the Apple menu and click
   **Privacy & Security** in the sidebar.
6. Scroll down to the Security section and click **Open Anyway** next to
   the note about GDTF Comparer. This button only shows for about an hour
   after step 4, so if it isn't there, double-click the app again and
   come back.
7. A window appears — click **Open Anyway** (on some versions this just
   says **Open**), then enter your Mac password or use Touch ID if asked.
8. From now on, a normal double-click opens the app.

On older macOS versions, the same button is under System Preferences,
then Security & Privacy, then General.

**If macOS says the app "is damaged and can't be opened"** — click
**Cancel**, open Terminal (Applications, then Utilities, then Terminal),
paste this line exactly as shown, and press Return:

```bash
xattr -cr "/Applications/GDTF Comparer.app"
```

Close Terminal and double-click the app again. This clears the
"downloaded from the internet" mark from GDTF Comparer only.

### On Windows

1. Download `GDTF-Comparer-windows.zip` above. If your browser says the
   file "isn't commonly downloaded," keep it anyway (in Microsoft Edge:
   the three dots next to the download, then **Keep**, then **Show
   more**, then **Keep anyway**).
2. Open Downloads, right-click the zip file, choose **Extract All…**,
   then **Extract**.
3. Open the extracted "GDTF Comparer" folder and double-click "GDTF
   Comparer" (GDTF Comparer.exe). Keep the whole folder together — the
   app needs the `_internal` folder beside it.
4. The first time, a blue box says "Windows protected your PC." Click
   **More info**, then **Run anyway**.
5. Next time, just double-click the app.

If Windows says Smart App Control blocked the app, there is no Run
anyway button — Smart App Control blocks every app that isn't signed, so
GDTF Comparer can't run on that PC yet. Please tell us at the issues page
below rather than switching Smart App Control off.

### Why do I see a warning?

GDTF Comparer is free, and its downloads are not signed with a paid
Apple or Microsoft developer certificate, so your computer can't confirm
who made them and asks you once. The steps above allow only GDTF
Comparer and change nothing else about your computer's security.

Only do this for a copy you downloaded from
https://github.com/BEtheLED/GDTFComparer/releases. If the file came from
anywhere else, delete it and download it from that page instead.

Full instructions and troubleshooting: https://github.com/BEtheLED/GDTFComparer#download-and-run-no-python-needed

Looking for the newest build? https://github.com/BEtheLED/GDTFComparer/releases/latest

Report a problem: https://github.com/BEtheLED/GDTFComparer/issues
