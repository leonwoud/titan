#!/usr/bin/env python3
"""Native QTest-based tests for Qt widgets."""

import sys
import os
import unittest

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from titan.qt import QtCore, QtGui, QtWidgets, QtTest


class TestColorPicker(unittest.TestCase):
    """Test the ColorPicker widget using native QTest."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        from titan._internal.qt.widgets.color_picker import ColorPicker
        self.color_picker = ColorPicker()
        self.color_picker.show()
        QtTest.QTest.qWaitForWindowExposed(self.color_picker)
    
    def tearDown(self):
        """Clean up after each test."""
        self.color_picker.close()
        self.color_picker = None
    
    def test_color_picker_creation(self):
        """Test that color picker can be created."""
        self.assertIsNotNone(self.color_picker)
        self.assertIsInstance(self.color_picker, QtWidgets.QWidget)
    
    def test_color_picker_set_color(self):
        """Test setting color on color picker."""
        red_color = QtGui.QColor(255, 0, 0)
        self.color_picker.set_color(red_color)
        self.assertEqual(self.color_picker._color.red(), 255)
        self.assertEqual(self.color_picker._color.green(), 0)
        self.assertEqual(self.color_picker._color.blue(), 0)
    
    def test_color_picker_csv_input(self):
        """Test setting color using CSV string."""
        self.color_picker.set_csv("255,127,80")
        color = self.color_picker._color
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.green(), 127)
        self.assertEqual(color.blue(), 80)
    
    def test_color_picker_paint_event(self):
        """Test that paint event doesn't crash (the antialiasing issue)."""
        # Force a paint event
        self.color_picker.update()
        # Process events to trigger paint
        QtTest.QTest.qWait(100)
        # If we get here without crashing, the paint event worked
        self.assertTrue(True)
    
    def test_color_picker_mouse_interaction(self):
        """Test mouse click on color picker."""
        # Get the center of the widget
        center = self.color_picker.rect().center()
        
        # Simulate mouse click
        QtTest.QTest.mouseClick(self.color_picker, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, center)
        
        # Process events
        QtTest.QTest.qWait(100)
        
        # Test passed if no crash occurred
        self.assertTrue(True)


class TestPreferenceWidgets(unittest.TestCase):
    """Test preference widgets using native QTest."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def test_field_widget(self):
        """Test Field preference widget."""
        from titan._internal.preferences.widgets import Field
        
        field = Field(str, "test value", "default value")
        field.show()
        QtTest.QTest.qWaitForWindowExposed(field)
        
        # Test setting value
        field.set_value("new value")
        self.assertEqual(field.get_value(), "new value")
        
        # Test keyboard input
        field.clear()
        QtTest.QTest.keyClicks(field, "typed value")
        field.editingFinished.emit()  # Trigger the signal manually
        
        field.close()
    
    def test_checkbox_widget(self):
        """Test CheckBox preference widget."""
        from titan._internal.preferences.widgets import CheckBox
        
        checkbox = CheckBox(False, True, "Test Checkbox")
        checkbox.show()
        QtTest.QTest.qWaitForWindowExposed(checkbox)
        
        # Test initial state
        self.assertFalse(checkbox.get_value())
        
        # Test mouse click
        QtTest.QTest.mouseClick(checkbox, QtCore.Qt.LeftButton)
        self.assertTrue(checkbox.get_value())
        
        checkbox.close()
    
    def test_combobox_widget(self):
        """Test ComboBox preference widget."""
        from titan._internal.preferences.widgets import ComboBox
        
        items = ["option1", "option2", "option3"]
        combobox = ComboBox(str, "option2", "option1", items)
        combobox.show()
        QtTest.QTest.qWaitForWindowExposed(combobox)
        
        # Test initial value
        self.assertEqual(combobox.get_value(), "option2")
        
        # Test changing selection
        combobox.setCurrentText("option3")
        self.assertEqual(combobox.get_value(), "option3")
        
        combobox.close()


class TestPreferences(unittest.TestCase):
    """Test preference system with Qt widgets."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def test_preferences_widget_creation(self):
        """Test creating preference widget from JSON."""
        from titan._internal.preferences.main import Preferences, create_preferences_widget
        
        logger_path = "resources/preferences/logger.json"
        if not os.path.exists(logger_path):
            self.skipTest(f"Logger preferences file not found: {logger_path}")
        
        preferences = Preferences.from_file(logger_path)
        widget = create_preferences_widget(preferences)
        
        self.assertIsNotNone(widget)
        
        # Show widget to test rendering
        widget.show()
        QtTest.QTest.qWaitForWindowExposed(widget)
        
        # Process events to ensure everything renders
        QtTest.QTest.qWait(200)
        
        widget.close()
    
    def test_preferences_dialog(self):
        """Test preferences dialog."""
        from titan._internal.preferences.main import Preferences, PreferencesDialog
        
        logger_path = "resources/preferences/logger.json"
        if not os.path.exists(logger_path):
            self.skipTest(f"Logger preferences file not found: {logger_path}")
        
        preferences = Preferences.from_file(logger_path)
        dialog = PreferencesDialog(preferences)
        
        self.assertIsNotNone(dialog)
        
        # Show dialog briefly
        dialog.show()
        QtTest.QTest.qWaitForWindowExposed(dialog)
        QtTest.QTest.qWait(100)
        dialog.close()


def run_tests():
    """Run all Qt tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestColorPicker))
    suite.addTests(loader.loadTestsFromTestCase(TestPreferenceWidgets))
    suite.addTests(loader.loadTestsFromTestCase(TestPreferences))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)