"""Unit tests for core.profile_repository: round trip, naming rules,
idempotency, path-safety and per-OS folder resolution (ATTR-03, D-01..D-05).

ProfileRepository.save()/load_all() persist a reusable (category, attribute)
spec sheet as one JSON file, keyed by name so a profile name is never a
filesystem path component (RESEARCH Pitfall 4). Every test here uses
ProfileRepository(base_dir=str(tmp_path)), never the default per-user folder.
"""

import os
import sys

import pytest

from gdtf_comparer.core.errors import ProfileNameError
from gdtf_comparer.core.profile_repository import ProfileRepository, app_data_dir


def test_save_and_load_round_trip(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))
    zoom_attrs = {("Beam", "Zoom")}
    aura_attrs = {("Physical Properties", "Weight"), ("Beam", "BeamAngle")}

    repo.save("Zoom Spec", zoom_attrs)
    repo.save("aura spec", aura_attrs)

    fresh = ProfileRepository(base_dir=str(tmp_path))
    profiles = fresh.load_all()

    assert [p.name for p in profiles] == ["aura spec", "Zoom Spec"]
    by_name = {p.name: p.attributes for p in profiles}
    assert by_name["Zoom Spec"] == frozenset(zoom_attrs)
    assert by_name["aura spec"] == frozenset(aura_attrs)


def test_profile_names_are_trimmed_normalised_and_matched_ignoring_case(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))

    repo.save("  Moving Head Spec  ", {("Beam", "BeamAngle")})
    stored = repo.find("moving head SPEC")
    assert stored is not None
    assert stored.name == "Moving Head Spec"

    repo.save("moving head spec", {("Beam", "FieldAngle")})
    profiles = repo.load_all()
    assert len(profiles) == 1
    assert profiles[0].name == "moving head spec"
    assert profiles[0].attributes == frozenset({("Beam", "FieldAngle")})

    combining_cedilla_name = "Façade"
    precomposed_name = "Façade"
    repo.save(combining_cedilla_name, {("Beam", "BeamType")})
    found = repo.find(precomposed_name)
    assert found is not None
    assert found.name == precomposed_name

    fresh = ProfileRepository(base_dir=str(tmp_path))
    roundtripped = fresh.find(precomposed_name)
    assert roundtripped is not None
    assert roundtripped.name == precomposed_name

    repo.save("Collision Test", {("Beam", "BeamAngle"), ("Beam", "beamangle")})
    collision = repo.find("Collision Test")
    assert collision.attributes == frozenset({("Beam", "BeamAngle"), ("Beam", "beamangle")})


@pytest.mark.parametrize(
    "bad_name",
    ["", "   ", "a" * 81, "tab\there", "line\nbreak"],
)
def test_invalid_profile_names_are_refused(tmp_path, bad_name):
    repo = ProfileRepository(base_dir=str(tmp_path))

    with pytest.raises(ProfileNameError) as exc_info:
        repo.save(bad_name, {("Beam", "BeamAngle")})

    message = str(exc_info.value)
    assert "Traceback" not in message
    assert os.path.exists(repo.path) is False


def test_exactly_80_character_name_saves(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))
    name = "x" * 80

    saved = repo.save(name, {("Beam", "BeamAngle")})

    assert saved.name == name
    assert os.path.exists(repo.path) is True


def test_saving_same_profile_twice_is_idempotent(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))
    attrs = {("Beam", "BeamAngle"), ("Physical Properties", "Weight")}

    repo.save("Spec", attrs)
    first_bytes = open(repo.path, "rb").read()

    repo.save("Spec", attrs)
    second_bytes = open(repo.path, "rb").read()

    assert first_bytes == second_bytes
    assert len(repo.load_all()) == 1


def test_empty_selection_can_be_saved(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))

    repo.save("Empty", [])
    profiles = repo.load_all()

    assert len(profiles) == 1
    assert profiles[0].attributes == frozenset()

    fresh_repo = ProfileRepository(base_dir=str(tmp_path / "never-created"))
    assert fresh_repo.load_all() == []
    assert fresh_repo.find("x") is None


def test_profile_name_is_never_used_as_a_path(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))
    parent_before = sorted(os.listdir(tmp_path.parent))

    dangerous_names = [
        "../../escape",
        "a/b",
        "CON",
        "x:*?<>|",
        "back\\slash",
    ]
    for index, name in enumerate(dangerous_names):
        repo.save(name, {("Beam", f"Attr{index}")})

    assert sorted(os.listdir(tmp_path)) == ["profiles.json"]
    assert sorted(os.listdir(tmp_path.parent)) == parent_before


def test_app_data_dir_per_platform():
    assert app_data_dir("darwin", {}, "/Users/u") == os.path.join(
        "/Users/u", "Library", "Application Support", "GDTF Comparer"
    )

    assert app_data_dir("win32", {"APPDATA": "/win/appdata"}, "/win/home") == os.path.join(
        "/win/appdata", "GDTF Comparer"
    )
    assert app_data_dir("win32", {}, "/win/home") == os.path.join(
        "/win/home", "GDTF Comparer"
    )

    assert app_data_dir("linux", {"XDG_CONFIG_HOME": "/x/cfg"}, "/home/u") == os.path.join(
        "/x/cfg", "GDTF Comparer"
    )
    assert app_data_dir(
        "linux", {"XDG_CONFIG_HOME": "relative/cfg"}, "/home/u"
    ) == os.path.join("/home/u", ".config", "GDTF Comparer")
    assert app_data_dir("linux", {"XDG_CONFIG_HOME": ""}, "/home/u") == os.path.join(
        "/home/u", ".config", "GDTF Comparer"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file permissions only")
def test_profiles_file_is_owner_only(tmp_path):
    repo = ProfileRepository(base_dir=str(tmp_path))
    repo.save("Spec", {("Beam", "BeamAngle")})

    mode = os.stat(repo.path).st_mode
    assert mode & 0o077 == 0
