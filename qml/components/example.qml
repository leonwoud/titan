__mouseArea: MouseArea {
    id: mouseArea

    parent: __listView
    width: __listView.width
    height: __listView.height
    z: -1
    propagateComposedEvents: true
    focus: true
    // If there is not a touchscreen, keep the flickable from eating our mouse drags.
    // If there is a touchscreen, flicking is possible, but selection can be done only by tapping, not by dragging.
    preventStealing: false // !Settings.hasTouchScreen

    property var clickedIndex: undefined
    property var pressedIndex: undefined
    property bool selectOnRelease: false
    property int pressedColumn: -1
    readonly property alias currentRow: root.__currentRow
    readonly property alias currentIndex: root.currentIndex

    // Handle vertical scrolling whem dragging mouse outside boundaries
    property int autoScroll: 0 // 0 -> do nothing; 1 -> increment; 2 -> decrement
    property bool shiftPressed: false // forward shift key state to the autoscroll timer

    Timer {
        running: mouseArea.autoScroll !== 0  //&& __verticalScrollBar.visible
        interval: 20
        repeat: true
        onTriggered: {
            var oldPressedIndex = mouseArea.pressedIndex
            var row
            if (mouseArea.autoScroll === 1) {
                __listView.incrementCurrentIndexBlocking();
                row = __listView.indexAt(0, __listView.height + __listView.contentY)
                if (row === -1)
                    row = __listView.count - 1
            } else {
                __listView.decrementCurrentIndexBlocking();
                row = __listView.indexAt(0, __listView.contentY)
            }

            var index = modelAdaptor.mapRowToModelIndex(row)
            if (index !== oldPressedIndex) {
                mouseArea.pressedIndex = index
                var modifiers = mouseArea.shiftPressed ? Qt.ShiftModifier : Qt.NoModifier
                mouseArea.mouseSelect(index, modifiers, true /* drag */)
            }
        }
    }

    function mouseSelect(modelIndex, modifiers, drag) {
        if (!selection) {
            maybeWarnAboutSelectionMode()
            return
        }

        if (selectionMode) {
            selection.setCurrentIndex(modelIndex, ItemSelectionModel.NoUpdate)
            if (selectionMode === enumSelectionMode.singleSelection) {
                selection.select(modelIndex, ItemSelectionModel.ClearAndSelect)
            } else {
                var selectRowRange = (drag && (selectionMode === enumSelectionMode.multiSelection
                                                || (selectionMode === enumSelectionMode.extendedSelection
                                                    && modifiers & Qt.ControlModifier)))
                                        || modifiers & Qt.ShiftModifier
                var itemSelection = !selectRowRange || clickedIndex === modelIndex ? modelIndex
                                    : modelAdaptor.selectionForRowRange(clickedIndex, modelIndex)

                if (selectionMode === enumSelectionMode.multiSelection
                    || selectionMode === enumSelectionMode.extendedSelection && modifiers & Qt.ControlModifier) {
                    if (drag)
                        selection.select(itemSelection, ItemSelectionModel.ToggleCurrent)
                    else
                        selection.select(modelIndex, ItemSelectionModel.Toggle)
                } else if (modifiers & Qt.ShiftModifier) {
                    selection.select(itemSelection, ItemSelectionModel.SelectCurrent)
                } else {
                    clickedIndex = modelIndex // Needed only when drag is true
                    selection.select(modelIndex, ItemSelectionModel.ClearAndSelect)
                }
            }
        }
    }

    function keySelect(keyModifiers) {
        if (selectionMode) {
            if (!keyModifiers)
                clickedIndex = currentIndex
            if (!(keyModifiers & Qt.ControlModifier))
                mouseSelect(currentIndex, keyModifiers, keyModifiers & Qt.ShiftModifier)
        }
    }

    function selected(row) {
        if (selectionMode === enumSelectionMode.noSelection)
            return false

        var modelIndex = null
        if (!!selection) {
            modelIndex = modelAdaptor.mapRowToModelIndex(row)
            if (modelIndex.valid) {
                if (selectionMode === enumSelectionMode.singleSelection)
                    return selection.currentIndex === modelIndex
                return selection.hasSelection && selection.isSelected(modelIndex)
            } else {
                return false
            }
        }

        return row === currentRow
                && (selectionMode === enumSelectionMode.singleSelection
                    || (selectionMode > enumSelectionMode.singleSelection && !selection))
    }

    function branchDecorationContains(x, y) {
        var clickedItem = __listView.itemAt(0, y + __listView.contentY)
        if (!(clickedItem && clickedItem.rowItem))
            return false
        var branchDecoration = clickedItem.rowItem.branchDecoration
        if (!branchDecoration)
            return false
        var pos = mapToItem(branchDecoration, x, y)
        return branchDecoration.contains(Qt.point(pos.x, pos.y))
    }

    function maybeWarnAboutSelectionMode() {
        if (selectionMode > enumSelectionMode.singleSelection)
            console.warn("TreeView: Non-single selection is not supported without an ItemSelectionModel.")
    }

    onPressed: {
        var pressedRow = __listView.indexAt(0, mouseY + __listView.contentY)
        pressedIndex = modelAdaptor.mapRowToModelIndex(pressedRow)
        pressedColumn = __listView.columnAt(mouseX)
        selectOnRelease = false
        __listView.forceActiveFocus()
        if (pressedRow === -1
            /*|| Settings.hasTouchScreen*/
            || branchDecorationContains(mouse.x, mouse.y)) {
            return
        }
        if (selectionMode === enumSelectionMode.extendedSelection
            && selection.isSelected(pressedIndex)) {
            selectOnRelease = true
            return
        }
        __listView.currentIndex = pressedRow
        if (!clickedIndex)
            clickedIndex = pressedIndex
        mouseSelect(pressedIndex, mouse.modifiers, false)
        if (!mouse.modifiers)
            clickedIndex = pressedIndex
    }

    onReleased: {
        if (selectOnRelease) {
            var releasedRow = __listView.indexAt(0, mouseY + __listView.contentY)
            var releasedIndex = modelAdaptor.mapRowToModelIndex(releasedRow)
            if (releasedRow >= 0 && releasedIndex === pressedIndex)
                mouseSelect(pressedIndex, mouse.modifiers, false)
        }
        pressedIndex = undefined
        pressedColumn = -1
        autoScroll = 0
        selectOnRelease = false
    }

    onPositionChanged: {
        // NOTE: Testing for pressed is not technically needed, at least
        // until we decide to support tooltips or some other hover feature
        if (mouseY > __listView.height && pressed) {
            if (autoScroll === 1) return;
            autoScroll = 1
        } else if (mouseY < 0 && pressed) {
            if (autoScroll === 2) return;
            autoScroll = 2
        } else  {
            autoScroll = 0
        }

        if (pressed && containsMouse) {
            var oldPressedIndex = pressedIndex
            var pressedRow = __listView.indexAt(0, mouseY + __listView.contentY)
            pressedIndex = modelAdaptor.mapRowToModelIndex(pressedRow)
            pressedColumn = __listView.columnAt(mouseX)
            if (pressedRow > -1 && oldPressedIndex !== pressedIndex) {
                __listView.currentIndex = pressedRow
                mouseSelect(pressedIndex, mouse.modifiers, true /* drag */)
            }
        }
    }

    onExited: {
        pressedIndex = undefined
        pressedColumn = -1
        selectOnRelease = false
    }

    onCanceled: {
        pressedIndex = undefined
        pressedColumn = -1
        autoScroll = 0
        selectOnRelease = false
    }

    onClicked: {
        var clickIndex = __listView.indexAt(0, mouseY + __listView.contentY)
        if (clickIndex > -1) {
            var modelIndex = modelAdaptor.mapRowToModelIndex(clickIndex)
            if (branchDecorationContains(mouse.x, mouse.y)) {
                if (modelAdaptor.isExpanded(modelIndex))
                    modelAdaptor.collapse(modelIndex)
                else
                    modelAdaptor.expand(modelIndex)
            } else {
                // compensate for the fact that onPressed didn't select on press: do it here instead
                pressedIndex = modelAdaptor.mapRowToModelIndex(clickIndex)
                pressedColumn = __listView.columnAt(mouseX)
                selectOnRelease = false
                __listView.forceActiveFocus()
                __listView.currentIndex = clickIndex
                if (!clickedIndex)
                    clickedIndex = pressedIndex
                mouseSelect(pressedIndex, mouse.modifiers, false)
                if (!mouse.modifiers)
                    clickedIndex = pressedIndex

                if (root.__activateItemOnSingleClick && !mouse.modifiers)
                    root.activated(modelIndex)
            }
            root.clicked(modelIndex)
        }
    }

    onDoubleClicked: {
        var clickIndex = __listView.indexAt(0, mouseY + __listView.contentY)
        if (clickIndex > -1) {
            var modelIndex = modelAdaptor.mapRowToModelIndex(clickIndex)
            if (!root.__activateItemOnSingleClick)
                root.activated(modelIndex)
            root.doubleClicked(modelIndex)
        }
    }

    onPressAndHold: {
        var pressIndex = __listView.indexAt(0, mouseY + __listView.contentY)
        if (pressIndex > -1) {
            var modelIndex = modelAdaptor.mapRowToModelIndex(pressIndex)
            root.pressAndHold(modelIndex)
        }
    }
}