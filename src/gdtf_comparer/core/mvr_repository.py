"""Imports an MVR show file into unique fixture types (PARSE-02, SUB-01, D-02).

pymvr only ever parses bytes core.hardening has already validated
(core.hardening.prevalidate_mvr_document); an embedded GDTF is looked up by
exact member name in the archive's own member list and run through the
standalone-GDTF pipeline (core.repository.FixtureRepository.load_bytes) --
nothing is ever unpacked to disk (RESEARCH Patterns 1-3).
"""

import io
import os
import zipfile
from dataclasses import dataclass
from typing import Any, FrozenSet, Iterator, Optional

import pymvr

from gdtf_comparer.core.errors import GDTFError, MVRParseError
from gdtf_comparer.core.hardening import prevalidate_mvr_document, read_mvr_member_bytes
from gdtf_comparer.core.models import FixtureModel
from gdtf_comparer.core.repository import FixtureRepository

MISSING_EMBEDDED_GDTF_REASON = "its GDTF file is not included in this MVR."

# Every node type besides fixtures/layers themselves that can carry its own
# child_list and so must be walked recursively for nested fixtures (RESEARCH
# correction: ChildList also carries scene_objects, and every node type below
# has its own child_list, not only GroupObject).
_CHILD_NODE_LISTS = ("group_objects", "scene_objects", "trusses", "supports", "video_screens", "projectors")

# import_summary_message's building blocks (RESEARCH Pitfall 4; SUB-01
# prohibition: every skipped type and unreferenced fixture is always named).
NO_FIXTURES_TEMPLATE = "'{file}' doesn't contain any fixtures."
NONE_IMPORTED_TEMPLATE = "None of the fixture types in '{file}' could be imported."
FOUND_TEMPLATE = "Found {types} in '{file}' ({fixtures})."
SKIPPED_TEMPLATE = " Couldn't import {count}: {details}."
UNREFERENCED_TEMPLATE = " {count} in the show {verb} no GDTF file and {pronoun} left out."


@dataclass(frozen=True)
class FixtureTypeEntry:
    """One unique GDTF fixture type found in an imported MVR (D-02).

    Parameters:
        gdtf_spec: The MVR zip member name this fixture type's GDTF file was
            imported from.
        instance_count: How many Fixture nodes in the MVR reference this
            gdtf_spec.
        fixture: The loaded FixtureModel for this fixture type.
    """

    gdtf_spec: str
    instance_count: int
    fixture: FixtureModel


@dataclass(frozen=True)
class SkippedFixtureType:
    """A fixture type referenced by the MVR that could not be imported.

    Parameters:
        gdtf_spec: The MVR zip member name that was referenced.
        instance_count: How many Fixture nodes in the MVR reference this
            gdtf_spec.
        reason: Lowercase sentence fragment describing why it was skipped.
    """

    gdtf_spec: str
    instance_count: int
    reason: str


@dataclass(frozen=True)
class MVRImport:
    """The result of importing one MVR show file.

    Parameters:
        source_path: Path to the .mvr file that was imported.
        fixture_types: The unique fixture types successfully imported, in
            first-seen order (SUB-01).
        skipped: The unique fixture types that could not be imported.
        unreferenced_fixture_count: How many Fixture nodes carried no
            GDTFSpec reference at all.
        total_fixture_count: How many Fixture nodes the walk found in total
            (referenced plus unreferenced), used only to tell "the show has
            no fixtures at all" apart from "every fixture type failed to
            import" in import_summary_message. Defaults to 0 so existing
            positional construction keeps working.
    """

    source_path: str
    fixture_types: tuple
    skipped: tuple
    unreferenced_fixture_count: int
    total_fixture_count: int = 0

    @property
    def file_name(self) -> str:
        """Return the base file name of source_path."""
        return os.path.basename(self.source_path)


def iter_fixtures(child_list: Optional[Any]) -> Iterator[Any]:
    """Yield every pymvr.Fixture reachable from a ChildList, recursively.

    Parameters:
        child_list: A pymvr ChildList (or None).

    Returns:
        Every Fixture directly in child_list.fixtures, then every Fixture
        nested inside each of those fixtures' own child_list, then every
        Fixture reachable from each group_object/scene_object/truss/support/
        video_screen/projector's own child_list, recursively. This order is
        the first-encountered order SUB-01 lists types in.
    """
    if child_list is None:
        return

    for fixture in child_list.fixtures:
        yield fixture
        yield from iter_fixtures(getattr(fixture, "child_list", None))

    for name in _CHILD_NODE_LISTS:
        for node in getattr(child_list, name, None) or ():
            yield from iter_fixtures(getattr(node, "child_list", None))


def readable_gdtf_spec(gdtf_spec: str) -> str:
    """Recover a GDTFSpec's original archive spelling from pymvr's mojibake.

    pymvr's BaseChildNode._read_xml unconditionally re-decodes every
    <GDTFSpec> element's text with .encode("utf-8").decode("cp437") ("IBM PC
    encoding") -- a transform correct for a zip written without the UTF-8
    name flag, but one that mangles any non-ASCII manufacturer/fixture name
    when the archive (as Python's zipfile always writes one) lists member
    names as real Unicode (RESEARCH Pitfall 4). Reversing the same
    byte-for-byte transform recovers the original text.

    Parameters:
        gdtf_spec: The gdtf_spec string a pymvr.Fixture reported.

    Returns:
        gdtf_spec.encode("cp437").decode("utf-8") when that round trip
        succeeds and differs from gdtf_spec, else gdtf_spec unchanged (an
        encode/decode failure just means no recovery is possible -- exact
        matching is always tried first in resolve_member_name).
    """
    try:
        candidate = gdtf_spec.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return gdtf_spec
    return candidate if candidate != gdtf_spec else gdtf_spec


def resolve_member_name(gdtf_spec: str, member_names: FrozenSet[str]) -> Optional[str]:
    """Resolve a Fixture's gdtf_spec to an exact zip member name.

    Parameters:
        gdtf_spec: The gdtf_spec string a pymvr.Fixture reported.
        member_names: The MVR archive's own member names.

    Returns:
        gdtf_spec itself when it is present in member_names (the common
        case: the zip was written without the UTF-8 name flag, or gdtf_spec
        is pure ASCII, so no mojibake was introduced). Otherwise
        readable_gdtf_spec(gdtf_spec) when that differs from gdtf_spec and
        is itself present in member_names (RESEARCH Pitfall 4: the zip's
        real, accented member name). Otherwise None -- the MVR references a
        GDTF this archive does not actually bundle.
    """
    if gdtf_spec in member_names:
        return gdtf_spec
    readable = readable_gdtf_spec(gdtf_spec)
    if readable != gdtf_spec and readable in member_names:
        return readable
    return None


def import_mvr(path: str, repository: Optional[FixtureRepository] = None) -> MVRImport:
    """Import an MVR show file into its unique fixture types (SUB-01).

    Parameters:
        path: Path to the .mvr file to import.
        repository: The FixtureRepository to load embedded GDTFs with.
            Defaults to a new FixtureRepository() when None.

    Returns:
        An MVRImport covering every unique fixture type referenced by the
        MVR, in first-seen order.

    Raises:
        MVRValidationError: The file is not a valid, safe MVR archive.
        MVRUnsafeFileError: The file was rejected by a safety limit.
        MVRParseError: pymvr itself failed to parse the validated bytes.
    """
    validated = prevalidate_mvr_document(path)

    try:
        with pymvr.GeneralSceneDescription(io.BytesIO(validated.archive_bytes)) as scene_description:
            scene = getattr(scene_description, "scene", None)
            order = []
            counts = {}
            unreferenced = 0
            for layer in scene.layers if scene is not None else ():
                for fixture in iter_fixtures(layer.child_list):
                    spec = fixture.gdtf_spec
                    if not spec:
                        unreferenced += 1
                        continue
                    if spec not in counts:
                        order.append(spec)
                        counts[spec] = 0
                    counts[spec] += 1
    except GDTFError:
        raise
    except Exception as exc:
        raise MVRParseError(
            path, f"its scene data could not be parsed ({type(exc).__name__})."
        ) from exc

    # The archive is re-opened independently rather than relying on pymvr's
    # own internal zip handle, which this module never names (RESEARCH
    # Anti-Patterns: a private attribute with no documented lifecycle).
    with zipfile.ZipFile(io.BytesIO(validated.archive_bytes)) as zf:
        names = frozenset(zf.namelist())

    repo = repository or FixtureRepository()
    entries = []
    skipped = []
    for spec in order:
        count = counts[spec]
        member = resolve_member_name(spec, names)
        if member is None:
            skipped.append(SkippedFixtureType(readable_gdtf_spec(spec), count, MISSING_EMBEDDED_GDTF_REASON))
            continue
        try:
            # member is the archive's own (readable) spelling, resolved by
            # resolve_member_name above -- the entry carries that, never
            # pymvr's possibly-mangled gdtf_spec (RESEARCH Pitfall 4).
            model = repo.load_bytes(read_mvr_member_bytes(validated.archive_bytes, path, member), member)
            entries.append(FixtureTypeEntry(member, count, model))
        except GDTFError as exc:
            skipped.append(SkippedFixtureType(readable_gdtf_spec(spec), count, exc.reason))

    total_fixture_count = unreferenced + sum(counts.values())
    return MVRImport(path, tuple(entries), tuple(skipped), unreferenced, total_fixture_count)


def _count(n: int, singular: str, plural: str) -> str:
    """Return "{n} {singular}" or "{n} {plural}" per standard English pluralization."""
    return f"{n} {singular if n == 1 else plural}"


def import_summary_message(result: MVRImport) -> str:
    """Return a friendly one-line summary of an MVR import result.

    Parameters:
        result: The MVRImport to summarize.

    Returns:
        NO_FIXTURES_TEMPLATE when the MVR's scene walk found no Fixture
        nodes at all; NONE_IMPORTED_TEMPLATE when it found some but none
        imported; otherwise FOUND_TEMPLATE. A SKIPPED_TEMPLATE clause is
        appended when any fixture type could not be imported (prohibition:
        every one is named, never silently dropped), and an
        UNREFERENCED_TEMPLATE clause is appended when any Fixture node
        carried no GDTFSpec at all.
    """
    if result.total_fixture_count == 0:
        message = NO_FIXTURES_TEMPLATE.format(file=result.file_name)
    elif not result.fixture_types:
        message = NONE_IMPORTED_TEMPLATE.format(file=result.file_name)
    else:
        total_fixtures = sum(entry.instance_count for entry in result.fixture_types)
        message = FOUND_TEMPLATE.format(
            types=_count(len(result.fixture_types), "fixture type", "fixture types"),
            file=result.file_name,
            fixtures=_count(total_fixtures, "fixture", "fixtures"),
        )

    if result.skipped:
        details = "; ".join(
            f"{skipped.gdtf_spec} ({skipped.reason.rstrip('.')})" for skipped in result.skipped
        )
        message += SKIPPED_TEMPLATE.format(
            count=_count(len(result.skipped), "fixture type", "fixture types"), details=details
        )

    if result.unreferenced_fixture_count:
        n = result.unreferenced_fixture_count
        message += UNREFERENCED_TEMPLATE.format(
            count=_count(n, "fixture", "fixtures"),
            verb="names" if n == 1 else "name",
            pronoun="was" if n == 1 else "were",
        )

    return message
