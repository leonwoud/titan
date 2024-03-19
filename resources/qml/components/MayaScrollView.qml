import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.5


ScrollView {
    id: root
    anchors.fill: parent
    property int scrollBarSize: 14

    rightPadding: verticalScrollBar.visible ? root.scrollBarSize : 0
    bottomPadding: horizontalScrollBar.visible ? root.scrollBarSize : 0

    ScrollBar.vertical: ScrollBar {
        id: verticalScrollBar
        parent: root.parent
        active: root.ScrollBar.horizontal || root.ScrollBar.horizontal.active
        width: root.scrollBarSize
        height: root.availableHeight
        x: parent.width - width
        topPadding: 12 * root.scrollBarSize / 14
        bottomPadding: 12 * root.scrollBarSize / 14
        contentItem: Rectangle {
            implicitWidth: root.scrollBarSize
            color: "#5D5D5D"
            radius: width / 2
        }
        background: Rectangle {
            color: "#373737"
            Shape {
                id: upArrow
                y: 3
                x: parent.width / 2 - width / 2
                width: 10 * root.scrollBarSize / 14
                height: 4 * root.scrollBarSize / 14
                ShapePath {
                    fillColor: "#A4A4A4"
                    strokeColor: "transparent"
                    startX: upArrow.width / 2; startY: 0
                    PathLine {x: upArrow.width; y: upArrow.height}
                    PathLine {x: 0; y: upArrow.height}
                    PathLine {x: upArrow.width / 2; y: 0}
                }
            }
            Shape {
                id: downArrow
                y: parent.height - downArrow.height - 3
                x: parent.width / 2 - width / 2
                width: 10 * root.scrollBarSize / 14
                height: 4 * root.scrollBarSize / 14
                ShapePath {
                    fillColor: "#A4A4A4"
                    strokeColor: "transparent"
                    startX: downArrow.width / 2; startY: downArrow.height
                    PathLine {x: downArrow.width; y: 0}
                    PathLine {x: 0; y: 0}
                    PathLine {x: downArrow.width / 2; y: downArrow.height}
                }
            }
        }
        visible: root.contentHeight > root.height
    }
    ScrollBar.horizontal: ScrollBar {
        id: horizontalScrollBar
        parent: root.parent
        active: root.ScrollBar.vertical || root.ScrollBar.vertical.active
        width: root.availableWidth
        height: root.scrollBarSize
        leftPadding: root.scrollBarSize
        rightPadding: root.scrollBarSize
        y: parent.height - height
        contentItem: Rectangle {
            implicitWidth: root.scrollBarSize
            color: "#5D5D5D"
            radius: width / 2
        }
        background: Rectangle {
            color: "#373737"
            Shape {
                id: leftArrow
                x: 3
                y: parent.height / 2 - height / 2
                width: 4 * root.scrollBarSize / 14
                height: 10 * root.scrollBarSize / 14
                ShapePath {
                    fillColor: "#A4A4A4"
                    strokeColor: "transparent"
                    startX: 0; startY: leftArrow.height / 2
                    PathLine {x: leftArrow.width; y: 0}
                    PathLine {x: leftArrow.width; y: leftArrow.height}
                    PathLine {x: 0; y: leftArrow.height / 2}
                }
            }
            Shape {
                id: rightArrow
                x: parent.width - rightArrow.width - 3
                y: parent.height / 2 - height / 2
                width: 4 * root.scrollBarSize / 14
                height: 10 * root.scrollBarSize / 14
                ShapePath {
                    fillColor: "#A4A4A4"
                    strokeColor: "transparent"
                    startX: rightArrow.width; startY: rightArrow.height / 2
                    PathLine {x: 0; y: 0}
                    PathLine {x: 0; y: rightArrow.height}
                    PathLine {x: rightArrow.width; y: rightArrow.height / 2}
                }
            }
        }
        visible: root.contentWidth > root.width
    }
}