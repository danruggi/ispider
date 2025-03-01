# tests/test_run.py
import sys
import unittest
from io import StringIO
import ispider_core

class TestMainCLI(unittest.TestCase):
    def test_no_stage_selected(self):
        # Simulate no stage provided (i.e., only the program name)
        test_args = ['prog']
        sys.argv = test_args

        # Call menu and check if it returns None or prints a help message
        args = menu()

        # Depending on how your menu is implemented, you might check args.stage or the output
        self.assertIsNone(args.stage, "Expected no stage to be selected")

    def test_stage1(self):
        # Simulate passing 'stage1' along with other options
        test_args = ['prog', 'stage1', '--config', 'settings.json']
        sys.argv = test_args

        args = menu()
        self.assertEqual(args.stage, 'stage1')
        self.assertEqual(args.config, 'settings.json')

if __name__ == '__main__':
    unittest.main()
