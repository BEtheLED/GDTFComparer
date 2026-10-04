"""Always-visible attribute selection side panel (D-01, D-02, D-03, D-04).

The picker groups every (category, attribute) pair from
core.comparator.attribute_catalog into collapsible sections (D-01) inside an
always-visible side panel (D-02). Selection is per (category, attribute),
never per full AttributeKey (Research Pattern 2): a fixture with several
geometry instances of the same beam still shows one checkbox, and checking
it shows every element path's row for that attribute at once. The checked
set is the single source of truth for what the results table shows; the
search box only narrows what is visible in the picker, never what is
checked (D-03). A section checkbox covers the whole category, including
leaves the search is currently hiding. Manual expand/collapse of a section
lasts until the next rebuild or search change.
"""

from typing import FrozenSet, Iterable, Optional, Set, Tuple

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from gdtf_comparer.core.models import DEFAULT_SELECTED_CATEGORIES

Catalog = Tuple[Tuple[str, Tuple[str, ...]], ...]
AttributePair = Tuple[str, str]

# Payload role storing the (category, attribute) tuple on each leaf item, and
# the "this is a section, not a leaf" absence marker on each top-level item.
_PAYLOAD_ROLE = Qt.ItemDataRole.UserRole

SEARCH_PLACEHOLDER = "Search attributes…"


class AttributePicker(QWidget):
    """Checkable, category-grouped attribute picker (D-01, D-02, D-03, D-04).

    Signals:
        selection_changed: Emitted once per event-loop turn after one or
            more checkboxes change, coalescing a section-click's cascade of
            per-leaf itemChanged signals into a single emission.
    """

    selection_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText(SEARCH_PLACEHOLDER)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_search)
        layout.addWidget(self.search_edit)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setUniformRowHeights(True)
        layout.addWidget(self.tree)

        self._known: Set[AttributePair] = set()
        self._checked: Set[AttributePair] = set()
        self._default_categories: FrozenSet[str] = frozenset(DEFAULT_SELECTED_CATEGORIES)
        self._rebuilding = False
        # Phase 3 D-01/D-03: once a compare profile has been loaded via
        # set_checked(), Phase 2's D-04 first-use defaults stop seeding new
        # pairs for the rest of the session. Without this, a comparison run
        # after loading a spec sheet would silently widen it with the Beam /
        # Physical Properties defaults, which D-03's replace semantics forbid.
        self._defaults_enabled = True

        self._emit_timer = QTimer(self)
        self._emit_timer.setSingleShot(True)
        self._emit_timer.setInterval(0)
        self._emit_timer.timeout.connect(self.selection_changed.emit)

        self.tree.itemChanged.connect(self._on_item_changed)

    def set_catalog(self, catalog: Catalog) -> None:
        """Rebuild the tree from a fresh attribute_catalog() result.

        Parameters:
            catalog: The (category, attribute_names) pairs from
                core.comparator.attribute_catalog.

        Seeds D-04's first-use default: every (category, attribute) pair not
        yet known is added to the known set, and also checked when its
        category is in DEFAULT_SELECTED_CATEGORIES -- but only while
        self._defaults_enabled is True. Once a compare profile has been
        loaded via set_checked() (Phase 3 D-01, D-03), default seeding stops
        for the rest of the session: a pair seen for the first time later
        joins the picker unchecked, so a loaded spec sheet is never silently
        widened by a later comparison's Beam / Physical Properties defaults.
        A pair already known keeps the user's prior choice, including one
        missing from this catalog (it gets its old state back if its files
        return later). This never emits selection_changed -- the caller
        applies the selection itself after calling this.
        """
        for category, attributes in catalog:
            for attribute in attributes:
                pair = (category, attribute)
                if pair not in self._known:
                    self._known.add(pair)
                    if self._defaults_enabled and category in self._default_categories:
                        self._checked.add(pair)

        self._rebuilding = True
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            for category, attributes in catalog:
                section_item = QTreeWidgetItem(self.tree, [category])
                section_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsAutoTristate
                )

                has_checked_leaf = False
                for attribute in attributes:
                    pair = (category, attribute)
                    leaf_item = QTreeWidgetItem(section_item, [attribute])
                    leaf_item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemNeverHasChildren
                    )
                    leaf_item.setData(0, _PAYLOAD_ROLE, pair)
                    checked = pair in self._checked
                    leaf_item.setCheckState(
                        0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                    )
                    has_checked_leaf = has_checked_leaf or checked

                section_item.setExpanded(has_checked_leaf)
        finally:
            self.tree.blockSignals(False)
            self._rebuilding = False

        self._apply_search()

    def checked_attributes(self) -> FrozenSet[AttributePair]:
        """Return the currently checked (category, attribute) set."""
        return frozenset(self._checked)

    def set_checked(self, pairs: Iterable[AttributePair]) -> None:
        """Replace the checked set wholesale (D-03: a profile load replaces, never merges).

        Parameters:
            pairs: The (category, attribute) pairs to check. Every pair not
                in this set becomes unchecked, including anything the user
                had checked by hand or a prior profile load.

        A pair not yet present in the current tree (not in self._known) is
        still recorded in self._checked and renders checked automatically
        the first time a later catalog includes it (set_catalog's existing
        "pair already known keeps its state" bookkeeping, unchanged by this
        method). After this call, Phase 2 D-04's first-use defaults stop for
        the rest of the session (self._defaults_enabled = False), so a later
        comparison's never-seen-before attributes join the picker unchecked
        instead of silently widening a loaded spec sheet (D-01).

        Emits selection_changed via the same coalescing timer as a manual
        checkbox edit, exactly once, so a profile load drives the identical
        downstream path (MainWindow._apply_attribute_selection) as a user
        click.
        """
        self._checked = {tuple(pair) for pair in pairs}
        self._defaults_enabled = False

        self._rebuilding = True
        self.tree.blockSignals(True)
        try:
            for section_index in range(self.tree.topLevelItemCount()):
                section = self.tree.topLevelItem(section_index)
                for child_index in range(section.childCount()):
                    leaf = section.child(child_index)
                    pair = tuple(leaf.data(0, _PAYLOAD_ROLE))
                    leaf.setCheckState(
                        0,
                        Qt.CheckState.Checked if pair in self._checked else Qt.CheckState.Unchecked,
                    )
        finally:
            self.tree.blockSignals(False)
            self._rebuilding = False

        self._apply_search()
        self._emit_timer.start()

    def section_item(self, category: str) -> Optional[QTreeWidgetItem]:
        """Return the top-level tree item for category, or None."""
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            if item.text(0) == category:
                return item
        return None

    def leaf_item(self, category: str, attribute: str) -> Optional[QTreeWidgetItem]:
        """Return the child tree item for (category, attribute), or None."""
        section = self.section_item(category)
        if section is None:
            return None
        for index in range(section.childCount()):
            child = section.child(index)
            if child.data(0, _PAYLOAD_ROLE) == (category, attribute):
                return child
        return None

    def _apply_search(self, text: Optional[str] = None) -> None:
        """Show/hide tree items to match the search box (D-03: visibility only).

        Parameters:
            text: The search text to apply, or None to read
                self.search_edit.text() directly (the textChanged-connected
                case, and the internal call at the end of set_catalog so an
                active search survives a rebuild).

        Never changes a check state, never modifies the checked set and
        never starts the coalescing emit timer -- this method only ever
        calls setHidden()/setExpanded() on tree items.
        """
        query = (text if text is not None else self.search_edit.text()).strip().casefold()

        for section_index in range(self.tree.topLevelItemCount()):
            section = self.tree.topLevelItem(section_index)
            category_text = section.text(0).casefold()
            section_matches = not query or query in category_text
            any_visible_leaf = False

            for child_index in range(section.childCount()):
                leaf = section.child(child_index)
                leaf_matches = (
                    section_matches or not query or query in leaf.text(0).casefold()
                )
                leaf.setHidden(not leaf_matches)
                any_visible_leaf = any_visible_leaf or leaf_matches

            section.setHidden(not any_visible_leaf)
            if any_visible_leaf:
                if query:
                    section.setExpanded(True)
                else:
                    section.setExpanded(
                        any(
                            section.child(i).checkState(0) == Qt.CheckState.Checked
                            for i in range(section.childCount())
                        )
                    )

    def visible_attributes(self) -> Tuple[AttributePair, ...]:
        """Return the (category, attribute) payload of every visible leaf.

        A leaf counts as visible only when neither it nor its section is
        hidden, in tree order (top to bottom, section by section).
        """
        visible = []
        for section_index in range(self.tree.topLevelItemCount()):
            section = self.tree.topLevelItem(section_index)
            if section.isHidden():
                continue
            for child_index in range(section.childCount()):
                leaf = section.child(child_index)
                if not leaf.isHidden():
                    visible.append(tuple(leaf.data(0, _PAYLOAD_ROLE)))
        return tuple(visible)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Record a leaf's new check state and schedule a coalesced emission."""
        if self._rebuilding:
            return

        payload = item.data(0, _PAYLOAD_ROLE)
        if payload is None:
            # A section row: its leaves report their own changes via Qt's
            # ItemIsAutoTristate propagation; nothing to record here.
            return

        pair = tuple(payload)
        if item.checkState(0) == Qt.CheckState.Checked:
            self._checked.add(pair)
        else:
            self._checked.discard(pair)

        self._emit_timer.start()
