# Releasing GDTF Comparer

Pushing a tag that starts with `v` builds both downloads on GitHub's own
Mac and Windows machines and publishes them as one GitHub Release,
automatically. You never build or upload a release file from your own
computer.

## Make a new release

1. Choose the next version (for example `0.1.1` for fixes, `0.2.0` for new
   features) and set `version` under `[project]` in `pyproject.toml` to
   that value. Commit the change.
2. `git push origin HEAD:main`
3. Tag the commit you just pushed and push the tag:
   ```bash
   git tag -a v<version> -m "GDTF Comparer <version>"
   git push origin v<version>
   ```
   (`<version>` is the same number you set in `pyproject.toml`, for example
   `v0.1.1`.)
4. Watch the "Build and release" run in the repository's Actions tab. It
   builds the macOS app, builds the Windows app, opens each one to check
   it ("smoke-checks" it), and then publishes the release — only if both
   builds and checks succeed.
5. Open the repository's Releases page and confirm both downloads
   (`GDTF-Comparer-macos.zip` and `GDTF-Comparer-windows.zip`) are
   attached.
6. Try the downloads yourself by following README.md's "Download and run
   (no Python needed)" steps exactly as a real user would.

## Test a build without releasing

Go to the Actions tab, open "Build and release," and click "Run workflow"
on `main`. This builds and smoke-checks both downloads exactly like a real
release, but publishes nothing. The two zips appear under that run's
Artifacts list for 14 days, then they're deleted automatically.

## If something goes wrong

A failed run never publishes a release — the release step only runs after
both the macOS and Windows builds succeed, and only if the tag's version
matches `pyproject.toml`.

**If the tag's run failed before any release was created:** fix the
problem, commit the fix, push it to `main`, then delete and recreate the
tag:
```bash
git push origin :refs/tags/v<version>
git tag -d v<version>
git tag -a v<version> -m "GDTF Comparer <version>"
git push origin v<version>
```

**Once a release is published, never move or reuse its tag.** If a
published release turns out to be broken, delete that release on the
Releases page (the tag can stay or be deleted separately) and publish a
new patch version instead, following "Make a new release" above from
step 1.

## Rules

- Never upload or replace release files by hand or from your own
  computer. The only files that should ever be attached to a release are
  the ones the "Build and release" run itself builds.
- The tag must equal `v` followed by `pyproject.toml`'s `[project]`
  version exactly, or the release step refuses to publish. This also
  means a GSD milestone tag (which doesn't follow this pattern) can never
  accidentally trigger a publish.
- The workflow uses no secrets. Nothing confidential needs to be
  configured to cut a release.

## Changing the first-launch instructions

If the Gatekeeper (macOS) or SmartScreen (Windows) screens ever look
different from what's documented, edit README.md and
`packaging/release-notes.md` together — they must describe the same
steps. Then run:
```bash
python -m pytest tests/test_release_docs.py
```
to confirm both files stayed in sync.

## Adding code signing later

Shipping unsigned was a deliberate, reversible choice (no paid Apple
Developer Program enrollment or Windows code-signing certificate yet).
Signing can be added later without changing the shape of this pipeline:

- **macOS:** sign the built `.app` with an Apple Developer ID certificate
  and notarize it with Apple, after the PyInstaller build step and before
  the `ditto` zip step in the `build-macos` job. This needs a paid Apple
  Developer Program membership and a signing certificate stored as a
  repository secret.
- **Windows:** sign `GDTF Comparer.exe` after the PyInstaller build step
  and before the `Compress-Archive` step in the `build-windows` job. This
  needs a Windows code-signing certificate, also stored as a repository
  secret.

Everything else in the pipeline — the job structure, the smoke checks,
the version-tag guard, and the release publishing step — stays exactly
the same. Adding signing would be the first and only reason to add a
secret to this workflow.
