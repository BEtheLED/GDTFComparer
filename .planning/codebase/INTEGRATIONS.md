---
last_mapped_commit: cc5e31ad5dc120a4b6fefe52dd199e0ff45c464d
last_mapped_at: 2026-09-25
---
# External Integrations

**Analysis Date:** 2026-09-25

## APIs & External Services

**None Detected**

The GDTFComparer application operates entirely standalone with no external API dependencies or remote service calls.

## Data Storage

**Databases:**

- None used - Application operates entirely on local file system

**File Storage:**

- Local filesystem only - GDTF files are read from and compared locally
  - Input: User-selected `.gdtf` files via `filedialog.askopenfilename()` in `BEtheLD`
  - Processing: Files extracted to temporary directory via `tempfile.mkdtemp()` in `parse_gdtf()` function (`BEtheLD` lines 142-182)
  - Output: Comparison results displayed in GUI treeview, not persisted

**Caching:**

- None implemented - Temporary files cleaned up immediately after parsing

## Authentication & Identity

**Auth Provider:**

- None required - Application has no user authentication or external identity integration

## Monitoring & Observability

**Error Tracking:**

- None configured - Errors are raised to caller (application UI or tests)

**Logs:**

- None configured - Application uses exception raising for error handling:
  - `zipfile.BadZipFile` raised in `parse_gdtf()` for invalid archives (`BEtheLD` lines 150-152)
  - `ET.ParseError` raised for malformed XML (`BEtheLD` lines 169-171)
  - `messagebox.showerror()` displays error dialogs to user in GUI (`BEtheLD` lines 100, 103)

## CI/CD & Deployment

**Hosting:**

- None - Standalone desktop application

**CI Pipeline:**

- None detected - No GitHub Actions, GitLab CI, or similar configurations

**Deployment:**

- Manual: Direct Python script execution or Blender addon installation
- No automated deployment pipeline

## Environment Configuration

**Required env vars:**

- None

**Secrets location:**

- No secrets used or stored

## Webhooks & Callbacks

**Incoming:**

- None

**Outgoing:**

- None

## Blender Integration (Addon-Specific)

**Blender Version:**

- Target: Blender 2.80.0+
- Implementation: `blender_addon/__init__.py` with `bl_info` metadata

**Blender API Usage:**

- Currently minimal - skeleton implementation only
- Addon registration system: `register()` and `unregister()` functions (currently no-op)
- Future planned: MVR/GDTF file import operators, custom fixture properties

**Communication:**

- Blender's embedded Python interpreter (no external IPC/RPC)
- File I/O: Load GDTF/MVR files from user's file system

---

*Integration audit: 2026-09-25*
