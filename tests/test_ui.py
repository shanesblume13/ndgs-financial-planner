from streamlit.testing.v1 import AppTest
import unittest
import sys
import os

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAppUI(unittest.TestCase):
    def test_app_load(self):
        """Smoke test: Verify the app runs without error"""
        at = AppTest.from_file("app.py", default_timeout=30)
        at.run()
        
        # Check title
        self.assertFalse(at.exception, "App crashed with an exception")
        
    def test_sidebar_defaults(self):
        """Verify sidebar inputs exist"""
        at = AppTest.from_file("app.py", default_timeout=30)
        at.run()
        
        # Check for key inputs in sidebar
        # Note: Accessing by key is most reliable
        self.assertIsNotNone(at.sidebar.number_input('loan_amount'))
        self.assertIsNotNone(at.sidebar.slider('operating_hours'))
        
        # Verify default loan amount
        self.assertEqual(at.sidebar.number_input('loan_amount').value, 320000.0)

    def test_interaction(self):
        """Verify changing an input triggers rerun and no error"""
        at = AppTest.from_file("app.py", default_timeout=30)
        at.run()
        
        # Change Operating Hours
        at.sidebar.slider('operating_hours').set_value(10).run()
        
        self.assertFalse(at.exception)
        
if __name__ == '__main__':
    unittest.main()
