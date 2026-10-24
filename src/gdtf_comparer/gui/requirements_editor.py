"""Checkable per-attribute requirements editor for one fixture type (SUB-02, D-06).

Shows one checkbox per eligible attribute of a shown fixture type; checking
one reveals a direction dropdown and a tolerance spinner, mirroring
gui.attribute_picker's checkable-tree shape and coalescing-emit pattern.

Each fixture type keeps its own independent checklist (D-04): switching away
from a fixture type and back restores exactly what was checked, with its
direction and tolerance, via self._remembered -- keyed by the GDTF file name
(gdtf_spec) the window passes into show_fixture. clear() empties this memory,
so importing a different MVR always starts every fixture type fresh.
"""

from typing import Dict, Optional, Tuple

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gdtf_comparer.core.models import FIXTURE_LEVEL_PATH, AttributeKey, FixtureModel, format_value
from gdtf_comparer.core.substitution import (
    NUMERIC_DIRECTIONS,
    TOLERANCE_KIND,
    Direction,
    DIRECTION_LABELS,
    Requirement,
    RequirementSet,
    attribute_unit,
    default_direction,
    default_tolerance,
    requirement_options,
)

KEY_ROLE = Qt.ItemDataRole.UserRole
DIRECTION_ROLE = Qt.ItemDataRole.UserRole + 1
TOLERANCE_ROLE = Qt.ItemDataRole.UserRole + 2
VALUE_ROLE = Qt.ItemDataRole.UserRole + 3

COL_ATTRIBUTE = 0
COL_VALUE = 1
COL_DIRECTION = 2
COL_TOLERANCE = 3

_EMPTY_LABEL_TEXT = "Pick a fixture type on the left to mark what matters."
_EXACT_DIRECTION_LABEL = "Must match"
NO_TOLERANCE_TEXT = "—"


class RequirementsEditor(QWidget):
    """Checkable, per-attribute editor building one RequirementSet.

    Signals:
        requirements_changed: Emitted once per event-loop turn after a
            checkbox, direction or tolerance changes, coalescing a burst of
            edits into a single emission.
    """

    requirements_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.empty_label = QLabel(_EMPTY_LABEL_TEXT, self)
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Attribute", "Your fixture", "Direction", "Tolerance"])
        self.tree.setUniformRowHeights(True)
        layout.addWidget(self.tree)

        self._rebuilding = False
        self._gdtf_spec: Optional[str] = None
        self._fixture: Optional[FixtureModel] = None
        # D-04: one entry per fixture type (gdtf_spec) ever shown this
        # session, holding every leaf's (checked, direction, tolerance) at
        # the moment it was last hidden by a rebuild. Emptied by clear().
        self._remembered: Dict[str, Dict[AttributeKey, Tuple[bool, str, float]]] = {}

        self._emit_timer = QTimer(self)
        self._emit_timer.setSingleShot(True)
        self._emit_timer.setInterval(0)
        self._emit_timer.timeout.connect(self.requirements_changed.emit)

        self.tree.itemChanged.connect(self._on_item_changed)

    def show_fixture(self, key: str, fixture: FixtureModel) -> None:
        """Rebuild the tree for a newly-selected fixture type.

        Parameters:
            key: The fixture type's gdtf_spec (MVR zip member name) -- saved
                into the eventual RequirementSet.gdtf_file, and the key
                self._remembered restores this fixture type's checklist by
                (D-04).
            fixture: The FixtureModel whose eligible attributes to show.
        """
        self._capture_current()

        self._gdtf_spec = key
        self._fixture = fixture
        remembered_for_key = self._remembered.get(key, {})
        restored_leaves = []

        self._rebuilding = True
        self.tree.blockSignals(True)
        try:
            self.tree.clear()

            sections: dict = {}
            for attribute_key, value in requirement_options(fixture):
                section_item = sections.get(attribute_key.category)
                if section_item is None:
                    section_item = QTreeWidgetItem(self.tree, [attribute_key.category])
                    section_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    sections[attribute_key.category] = section_item

                if attribute_key.element_path == FIXTURE_LEVEL_PATH:
                    label = attribute_key.attribute
                else:
                    label = f"{attribute_key.attribute} ({attribute_key.element_label})"

                unit = attribute_unit(attribute_key)
                value_text = f"{format_value(value)} {unit}" if unit else format_value(value)
                leaf_item = QTreeWidgetItem(section_item, [label, value_text])
                leaf_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemNeverHasChildren
                )
                leaf_item.setData(COL_ATTRIBUTE, KEY_ROLE, attribute_key)
                leaf_item.setData(COL_ATTRIBUTE, VALUE_ROLE, value)
                direction = default_direction(attribute_key, value)
                tolerance = default_tolerance(attribute_key, value, direction)

                remembered = remembered_for_key.get(attribute_key)
                checked = False
                if remembered is not None:
                    checked, direction_value, tolerance = remembered
                else:
                    direction_value = direction.value

                leaf_item.setData(COL_ATTRIBUTE, DIRECTION_ROLE, direction_value)
                leaf_item.setData(COL_ATTRIBUTE, TOLERANCE_ROLE, tolerance)
                leaf_item.setCheckState(
                    COL_ATTRIBUTE, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )
                if checked:
                    restored_leaves.append(leaf_item)

            self.tree.expandAll()
        finally:
            self.tree.blockSignals(False)
            self._rebuilding = False

        # Restored leaves need their direction/tolerance widgets created the
        # same way a manual tick does (_on_item_changed), but blockSignals
        # above suppressed that signal -- so it is done explicitly here,
        # outside the signal block, through the same helper.
        for leaf_item in restored_leaves:
            self._install_leaf_widgets(leaf_item)

        self.empty_label.setVisible(False)

    def clear(self) -> None:
        """Empty the tree, forget every remembered checklist and show the empty-state label.

        A new MVR import always starts every fixture type fresh (D-04): the
        outgoing fixture's state is never captured into self._remembered
        here, unlike show_fixture's switch between two known types.
        """
        self._rebuilding = True
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
        finally:
            self.tree.blockSignals(False)
            self._rebuilding = False
        self._gdtf_spec = None
        self._fixture = None
        self._remembered = {}
        self.empty_label.setVisible(True)

    def _capture_current(self) -> None:
        """Save the currently shown fixture's leaf states into self._remembered.

        Does nothing when no fixture is currently shown. Captures every
        leaf (checked, direction, tolerance), not only checked ones, so a
        row unticked after being ticked stays unticked when its type is
        shown again.
        """
        if self._gdtf_spec is None:
            return

        captured: Dict[AttributeKey, Tuple[bool, str, float]] = {}
        root = self.tree.invisibleRootItem()
        for section_index in range(root.childCount()):
            section = root.child(section_index)
            for leaf_index in range(section.childCount()):
                leaf = section.child(leaf_index)
                attribute_key = leaf.data(COL_ATTRIBUTE, KEY_ROLE)
                checked = leaf.checkState(COL_ATTRIBUTE) == Qt.CheckState.Checked
                direction_value = leaf.data(COL_ATTRIBUTE, DIRECTION_ROLE)
                tolerance = float(leaf.data(COL_ATTRIBUTE, TOLERANCE_ROLE))
                captured[attribute_key] = (checked, direction_value, tolerance)
        self._remembered[self._gdtf_spec] = captured

    def requirement_set(self) -> Optional[RequirementSet]:
        """Return the currently checked attributes as a RequirementSet, or None.

        Returns:
            None when no fixture is currently shown. Otherwise a
            RequirementSet built from every checked leaf, in tree order.
        """
        if self._fixture is None:
            return None

        requirements = []
        root = self.tree.invisibleRootItem()
        for section_index in range(root.childCount()):
            section = root.child(section_index)
            for leaf_index in range(section.childCount()):
                leaf = section.child(leaf_index)
                if leaf.checkState(COL_ATTRIBUTE) != Qt.CheckState.Checked:
                    continue
                requirements.append(
                    Requirement(
                        key=leaf.data(COL_ATTRIBUTE, KEY_ROLE),
                        target=leaf.data(COL_ATTRIBUTE, VALUE_ROLE),
                        direction=Direction(leaf.data(COL_ATTRIBUTE, DIRECTION_ROLE)),
                        tolerance=float(leaf.data(COL_ATTRIBUTE, TOLERANCE_ROLE)),
                    )
                )

        return RequirementSet(
            fixture_name=self._fixture.name,
            manufacturer=self._fixture.manufacturer,
            gdtf_file=self._gdtf_spec or "",
            requirements=tuple(requirements),
        )

    def leaf_item(self, key: AttributeKey) -> Optional[QTreeWidgetItem]:
        """Return the leaf tree item for key, or None."""
        root = self.tree.invisibleRootItem()
        for section_index in range(root.childCount()):
            section = root.child(section_index)
            for leaf_index in range(section.childCount()):
                leaf = section.child(leaf_index)
                if leaf.data(COL_ATTRIBUTE, KEY_ROLE) == key:
                    return leaf
        return None

    def direction_combo(self, key: AttributeKey) -> Optional[QComboBox]:
        """Return the direction QComboBox for key's leaf, or None if not checked."""
        leaf = self.leaf_item(key)
        if leaf is None:
            return None
        widget = self.tree.itemWidget(leaf, COL_DIRECTION)
        return widget if isinstance(widget, QComboBox) else None

    def tolerance_spin(self, key: AttributeKey) -> Optional[QDoubleSpinBox]:
        """Return the tolerance QDoubleSpinBox for key's leaf, or None if not checked."""
        leaf = self.leaf_item(key)
        if leaf is None:
            return None
        widget = self.tree.itemWidget(leaf, COL_TOLERANCE)
        return widget if isinstance(widget, QDoubleSpinBox) else None

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Create/remove a leaf's direction+tolerance widgets on check-state change."""
        if self._rebuilding or item.parent() is None:
            return

        if item.checkState(COL_ATTRIBUTE) == Qt.CheckState.Checked:
            self._install_leaf_widgets(item)
        else:
            self.tree.removeItemWidget(item, COL_DIRECTION)
            self.tree.removeItemWidget(item, COL_TOLERANCE)

        self._emit_timer.start()

    def _install_leaf_widgets(self, leaf: QTreeWidgetItem) -> None:
        """Create and install the direction combo + tolerance spin for a checked leaf.

        A text attribute (Direction.EXACT) only ever offers "Must match": a
        single, disabled combo entry and a disabled, "—"-reading tolerance
        box (RESEARCH Pitfall 5) -- there is nothing for the LD to choose.
        """
        direction = Direction(leaf.data(COL_ATTRIBUTE, DIRECTION_ROLE))
        attribute_key = leaf.data(COL_ATTRIBUTE, KEY_ROLE)
        unit = attribute_unit(attribute_key)

        combo = QComboBox(self.tree)
        if direction == Direction.EXACT:
            combo.addItem(_EXACT_DIRECTION_LABEL, Direction.EXACT.value)
            combo.setEnabled(False)
        else:
            for numeric_direction in NUMERIC_DIRECTIONS:
                combo.addItem(DIRECTION_LABELS[numeric_direction], numeric_direction.value)
            index = combo.findData(direction.value)
            combo.setCurrentIndex(max(index, 0))
        combo.currentIndexChanged.connect(lambda _index, leaf=leaf, combo=combo: self._on_direction_changed(leaf, combo))
        self.tree.setItemWidget(leaf, COL_DIRECTION, combo)

        spin = QDoubleSpinBox(self.tree)
        spin.setDecimals(3)
        if direction == Direction.EXACT:
            spin.setRange(0, 0)
            spin.setSpecialValueText(NO_TOLERANCE_TEXT)
        elif TOLERANCE_KIND == "percent":
            spin.setRange(0, 1000)
            spin.setSuffix(" %")
        else:
            spin.setRange(0, 1e9)
            if unit:
                spin.setSuffix(f" {unit}")
        spin.setValue(float(leaf.data(COL_ATTRIBUTE, TOLERANCE_ROLE)))
        spin.setEnabled(direction != Direction.EXACT)
        spin.valueChanged.connect(lambda _value, leaf=leaf, spin=spin: self._on_tolerance_changed(leaf, spin))
        self.tree.setItemWidget(leaf, COL_TOLERANCE, spin)

    def _on_direction_changed(self, leaf: QTreeWidgetItem, combo: QComboBox) -> None:
        """Write a leaf's new direction choice back onto its role and re-emit."""
        leaf.setData(COL_ATTRIBUTE, DIRECTION_ROLE, combo.currentData())
        self._emit_timer.start()

    def _on_tolerance_changed(self, leaf: QTreeWidgetItem, spin: QDoubleSpinBox) -> None:
        """Write a leaf's new tolerance value back onto its role and re-emit."""
        leaf.setData(COL_ATTRIBUTE, TOLERANCE_ROLE, spin.value())
        self._emit_timer.start()
