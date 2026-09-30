"""Widget-level AttributePicker tests: default seeding, search, rebuild (D-01..D-04)."""

from PySide6.QtCore import Qt

from gdtf_comparer.gui.attribute_picker import AttributePicker

CATALOG = (
    ("Beam", ("BeamAngle", "FieldAngle", "BeamType")),
    ("Physical Properties", ("Weight", "Width")),
    ("Extra Category", ("Zoom", "Focus")),
)


def _make_picker(qtbot) -> AttributePicker:
    picker = AttributePicker()
    qtbot.addWidget(picker)
    return picker


def test_default_seed_checks_only_default_categories(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)

    assert picker.checked_attributes() == frozenset(
        {
            ("Beam", "BeamAngle"),
            ("Beam", "FieldAngle"),
            ("Beam", "BeamType"),
            ("Physical Properties", "Weight"),
            ("Physical Properties", "Width"),
        }
    )

    section_texts = [
        picker.tree.topLevelItem(index).text(0)
        for index in range(picker.tree.topLevelItemCount())
    ]
    assert section_texts == ["Beam", "Physical Properties", "Extra Category"]

    for category, attributes in CATALOG:
        section = picker.section_item(category)
        child_texts = [section.child(i).text(0) for i in range(section.childCount())]
        assert child_texts == list(attributes)

    assert picker.section_item("Beam").isExpanded() is True
    assert picker.section_item("Physical Properties").isExpanded() is True
    assert picker.section_item("Extra Category").isExpanded() is False


def test_search_hides_non_matching_without_changing_checks(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)
    before = picker.checked_attributes()

    emissions = []
    picker.selection_changed.connect(lambda: emissions.append(True))

    qtbot.keyClicks(picker.search_edit, "angle")

    # Substring match on the attribute name (Task 2 action spec): "FieldAngle"
    # also contains "angle", so both Beam leaves stay visible; only sections
    # with no matching leaf (Physical Properties, Extra Category) hide.
    assert set(picker.visible_attributes()) == {
        ("Beam", "BeamAngle"),
        ("Beam", "FieldAngle"),
    }
    assert picker.section_item("Physical Properties").isHidden() is True
    assert picker.section_item("Extra Category").isHidden() is True
    assert picker.checked_attributes() == before

    qtbot.wait(50)
    assert emissions == []


def test_search_is_case_insensitive_and_matches_category_names(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)

    picker.search_edit.setText("EXTRA")
    assert set(picker.visible_attributes()) == {
        ("Extra Category", "Zoom"),
        ("Extra Category", "Focus"),
    }

    picker.search_edit.setText("zoo")
    assert picker.visible_attributes() == (("Extra Category", "Zoom"),)


def test_search_with_no_matches_is_harmless(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)
    before = picker.checked_attributes()

    picker.search_edit.setText("zzz")
    assert picker.visible_attributes() == ()
    assert picker.checked_attributes() == before

    picker.search_edit.setText("")
    assert len(picker.visible_attributes()) == 7
    assert picker.section_item("Beam").isExpanded() is True
    assert picker.section_item("Physical Properties").isExpanded() is True
    assert picker.section_item("Extra Category").isExpanded() is False


def test_section_click_is_one_coalesced_change(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)

    picker.search_edit.setText("zoom")

    emissions = []
    picker.selection_changed.connect(lambda: emissions.append(True))

    with qtbot.waitSignal(picker.selection_changed, timeout=1000):
        picker.section_item("Extra Category").setCheckState(0, Qt.CheckState.Checked)

    checked = picker.checked_attributes()
    assert ("Extra Category", "Zoom") in checked
    assert ("Extra Category", "Focus") in checked

    qtbot.wait(50)
    assert len(emissions) == 1


def test_rebuild_keeps_choices_and_seeds_new_pairs(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)

    picker.leaf_item("Beam", "BeamType").setCheckState(0, Qt.CheckState.Unchecked)
    picker.leaf_item("Extra Category", "Zoom").setCheckState(0, Qt.CheckState.Checked)

    extended_catalog = (
        ("Beam", ("BeamAngle", "FieldAngle", "BeamType", "LuminousFlux")),
        ("Physical Properties", ("Weight", "Width")),
    )
    picker.set_catalog(extended_catalog)

    checked = picker.checked_attributes()
    assert ("Beam", "BeamType") not in checked
    assert ("Beam", "LuminousFlux") in checked

    picker.set_catalog(CATALOG)
    checked = picker.checked_attributes()
    assert ("Extra Category", "Zoom") in checked
    assert ("Extra Category", "Focus") not in checked


def test_search_survives_rebuild(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(CATALOG)

    picker.search_edit.setText("width")
    picker.set_catalog(CATALOG)

    assert picker.visible_attributes() == (("Physical Properties", "Width"),)


def test_empty_catalog_shows_no_sections(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog(())
    assert picker.tree.topLevelItemCount() == 0


def test_single_attribute_category(qtbot):
    picker = _make_picker(qtbot)
    picker.set_catalog((("Only", ("One",)),))
    assert picker.tree.topLevelItemCount() == 1
    section = picker.tree.topLevelItem(0)
    assert section.childCount() == 1
    assert section.child(0).text(0) == "One"
