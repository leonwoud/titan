import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11
import QtQuick.Shapes 1.5
import QtQml.Models 2.15


Rectangle {
    id: root
    width: 800
    height: 600
    color: "#444444"

    property color trace_color: "mediumorchid"
    property color debug_color: "limegreen"
    property color info_color: "ghostwhite"
    property color warning_color: "orange"
    property color error_color: "orangered"
    property color critical_color: "red"

    MenuBar {
        id: menuBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 2

        Menu {
            title: qsTr("&File")
            MayaMenuItem {
                text: "Export..."
            }
            MayaMenuItem {
                text: "Import..."
            }
            MayaMenuSeparator { }
            MayaMenuItem {
                text: "Quit"
            }
        }
        Menu {
            title: qsTr("&Edit")
            MayaMenuItem {
                text: "Copy"
                onClicked: logger.copy_selected()
            }
            MayaMenuItem {
                text: "Clear"
            }
        }
        Menu {
            title: qsTr("&View")
            MayaMenuSeparator {
                text: "Log Level"
            }
            ButtonGroup {
                id: buttonGroup
                exclusive: true
                onClicked: logger.set_level(button.labelText)
            }
            MayaMenuItem {
                text: "Trace"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("trace")
            }
            MayaMenuItem {
                text: "Debug"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("debug")
                isCheckedByDefault: true
            }
            MayaMenuItem {
                text: "Info"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("info")
            }
            MayaMenuItem {
                text: "Warning"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("warning")
            }
            MayaMenuItem {
                text: "Error"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("error")
            }
            MayaMenuItem {
                text: "Critical"
                showRadioButton: true
                buttonGroup: buttonGroup
                onClicked: logger.set_level("critical")
            }
        }
    }

    Row {
        id: edit
        anchors.top: menuBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 5

        TextField {
            height: 25
            width: parent.width
            placeholderText: "Filter.."
            onTextChanged: logger.set_filter(text)
            color: "#C8C8C8"
            background: Rectangle { color: "#2B2B2B" }
        }
    }

    Rectangle {
        id: logList
        color: "#2B2B2B"
        radius: 2

        anchors.top: edit.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 5
        anchors.topMargin: 5

        MayaScrollView {
            ListView {
                id: listView
                clip: true
                contentWidth: contentItem.childrenRect.width
                model: proxy_model
                anchors.margins: 5
                delegate: itemDelegate
                flickableDirection: Flickable.HorizontalAndVerticalFlick
            }
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            propagateComposedEvents: true
            property int clicked_row: -1
            property int prev_row: -1

            onPressed: function(mouse) {
                var curY = listView.contentY
                clicked_row = listView.indexAt(0, mouseY + curY)
                if (prev_row == -1) {
                        prev_row = clicked_row
                }
                if (clicked_row == -1) {
                    proxy_model.clear_selection()
                    listView.contentY = curY
                    return
                }
                if (mouse.modifiers & Qt.ShiftModifier) {
                    var start = Math.min(clicked_row, prev_row)
                    var end = Math.max(clicked_row, prev_row)
                    proxy_model.select_range(start, end)
                } else if (mouse.modifiers & Qt.ControlModifier) {
                    proxy_model.toggle_index(clicked_row)
                } else {
                    proxy_model.clear_selection()
                    proxy_model.select_index(clicked_row)
                }
                listView.contentY = curY
            }

            onPositionChanged: function(mouse) {
                if (!pressed || mouse.modifiers & Qt.ControlModifier){
                    return
                }
                var curY = listView.contentY
                var current_row = listView.indexAt(0, mouseY + curY)
                if (current_row == -1) {
                    return
                }
                var start = Math.min(start_row, current_row)
                var end = Math.max(start_row, current_row)
                proxy_model.toggle_range(start, end)
                listView.contentY = curY
            }

            onReleased: function(mouse) {
                prev_row = start_row
            }
        }
    }

    Component {
        id: itemDelegate
        MouseArea {
            id: delegate
            width: Math.max(ListView.view.width, text.width)
            height: text.height
            clip: true
            z: -1
            hoverEnabled: true
            Rectangle {
                function opacity() {
                    var val = 0
                    if (proxy_model.is_selected(index)) {
                        val = 0.2
                    }
                    if (delegate.containsMouse) {
                        val += 0.1
                    }
                    return val
                }
                anchors.fill: parent
                color: "steelblue"
                opacity: opacity()
            }
            Text {
                function level_color(number) {
                    switch (number) {
                    case 5:
                        return root.trace_color
                    case 10:
                        return root.debug_color
                    case 20:
                        return root.info_color
                    case 30:
                        return root.warning_color
                    case 40:
                        return root.error_color
                    case 50:
                        return root.critical_color
                    }
                }
                id: text
                anchors.verticalCenter: parent.verticalCenter
                text: message
                elide: Text.ElideRight
                color: level_color(level_number)
                font.family: "Courier New"
                font.pixelSize: 12
            }
        }
    }
}
