//MayaMenuSeparator.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15


MenuSeparator {
    id: root
    property string text: ""

    padding: 0
    topPadding: (root.text != "") ? 8 : 2
    bottomPadding: (root.text != "") ? 8 : 2

    contentItem: Rectangle {
        id: separator
        anchors.top: root.top
        anchors.left: root.left
        anchors.right: root.right
        anchors.bottom: root.bottom
        color: "#525252"
        // The gutter
        Rectangle {
            id: gutter
            width: 20
            height: separator.height
            color: "#444444"
            anchors.verticalCenter: separator.verticalCenter
            anchors.left: separator.left
        }
        // Label for the separator
        Label {
            id: label
            font: root.font
            text: root.text
            anchors.verticalCenter: separator.verticalCenter
            anchors.left: gutter.right 
            anchors.leftMargin: 3
            color: "darkgrey"
            visible: label.text != ""
        }
        // The separator shape
        Rectangle {
            implicitWidth: 200
            implicitHeight: 1
            color: "#717171"
            anchors.verticalCenter: separator.verticalCenter
            anchors.left: label.visible ? label.right : gutter.right
            anchors.leftMargin: label.visible ? 5 : 2
        }
    }


}