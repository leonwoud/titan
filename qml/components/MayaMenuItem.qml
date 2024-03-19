//MayaMenuItem.qml
import QtQuick 2.15
import QtQuick.Controls 2.15

MenuItem {
    id: root
    implicitHeight: 20
    implicitWidth: 200

    // Radio Button
    property bool showRadioButton: false
    property ButtonGroup buttonGroup: null
    property bool isCheckedByDefault: false

    // Internal signal handling
    onClicked: function () {
        if (showRadioButton) {
            radioButton.checked = true
        }
    }

    contentItem: Rectangle {
        id: menu
        anchors.top: root.top
        anchors.left: root.left
        anchors.right: root.right
        anchors.bottom: root.bottom
        color: root.highlighted ? "#5285A6" : "#525252"
        Rectangle {
            id: gutter
            width: 20
            height: menu.height
            color: "#444444"
            anchors.verticalCenter: menu.verticalCenter
            anchors.left: menu.left
        }
        RadioButton {
            id: radioButton
            width: 20
            height: menu.height
            anchors.verticalCenter: gutter.verticalCenter
            anchors.horizontalCenter: gutter.horizontalCenter
            anchors.left: menu.left
            visible: root.showRadioButton
            ButtonGroup.group: root.buttonGroup
            property string labelText: root.text
            checked: isCheckedByDefault
        }
        Label {
            id: label
            text: root.text
            font: root.font
            anchors.verticalCenter: menu.verticalCenter
            anchors.left: gutter.right
            anchors.leftMargin: 15
            color: "white"
        }
    }
}