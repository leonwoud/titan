import QtQuick 2.15
import QtQuick.Shapes 1.5
import QtGraphicalEffects 1.15

Item {
    id: i_progress
    implicitWidth: properties.width
    implicitHeight: properties.height

    property bool round_cap: true
    property int start_angle: -90
    property real max_value: 100
    property bool reverse: properties.reverse
    property real value: properties.value
    property int samples: 12

    property color transparent: "transparent"
    property color groove_color: properties.groove_color
    property int groove_width: properties.groove_size

    property color progress_color: properties.progress_color
    property int progress_width: properties.progress_size

    property string text: properties.text
    property bool show_text: properties.show_percent
    property string text_font: properties.text_font
    property int text_size: properties.text_size
    property color text_color: properties.text_color

    Shape {
        id: shape
        anchors.fill: parent
        layer.enabled: true
        layer.samples: i_progress.samples

        ShapePath {
            id: pathBG
            strokeColor: i_progress.groove_color
            fillColor: i_progress.transparent
            strokeWidth: i_progress.groove_width
            capStyle: i_progress.round_cap ? ShapePath.RoundCap : ShapePath.FlatCap

            PathAngleArc {
                id: arcBG
                radiusX: ( i_progress.width / 2 ) - ( pathBG.strokeWidth / 2 )
                radiusY: ( i_progress.height /  2) - ( pathBG.strokeWidth / 2 )
                centerX: i_progress.width / 2
                centerY: i_progress.height / 2
                startAngle: i_progress.start_angle
                sweepAngle: 360
            }
        }

        ShapePath {
            id: path
            strokeColor: i_progress.progress_color
            fillColor: "transparent"
            strokeWidth: i_progress.progress_width
            capStyle: i_progress.round_cap ? ShapePath.RoundCap : ShapePath.FlatCap

            PathAngleArc {
                id: progressArcBG
                radiusX: ( i_progress.width / 2 ) - ( i_progress.progress_width / 2 )
                radiusY: ( i_progress.height /  2) - ( i_progress.progress_width / 2 )
                centerX: i_progress.width / 2
                centerY: i_progress.height / 2
                startAngle: i_progress.start_angle
                sweepAngle: i_progress.reverse ? 360 - (360 / i_progress.max_value * i_progress.value) : (360 / i_progress.max_value * i_progress.value)
            }
        }

        Text {
            id: textProgress
            text: i_progress.show_text ? parseInt(i_progress.reverse ? 100 - i_progress.value : i_progress.value) + "%" : i_progress.text
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            color: i_progress.text_color
            font.pointSize: i_progress.text_size
            font.family: i_progress.text_font
        }

    }
}