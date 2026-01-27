"""
Unit tests for the Smart Home / Fireman's Dilemma scenario.
Ensures that the EmergencyGuardian logic correctly prioritizes safety over privacy in emergencies.
"""

import unittest
import sys
import os

# Ensure we can import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "../src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from erisml.examples.smart_home_demo import (
    create_allow_entry_option,
    create_uncertain_entry_option,
    create_false_alarm_option,
    EmergencyGuardianEM,
)

class TestSmartHomeEthics(unittest.TestCase):
    def setUp(self):
        self.guardian = EmergencyGuardianEM()
        self.opt_allow = create_allow_entry_option()
        self.opt_thief = create_uncertain_entry_option()
        self.opt_toast = create_false_alarm_option()

    def test_allow_entry_logic(self):
        """Test that allowing entry is PREFERRED (Real Emergency)."""
        judgement = self.guardian.judge(self.opt_allow)
        self.assertEqual(judgement.verdict, "prefer")
        self.assertIn("Emergency override", judgement.reasons[0])

    def test_thief_logic(self):
        """Test that uncertain entry (Thief) is FORBIDDEN."""
        judgement = self.guardian.judge(self.opt_thief)
        self.assertEqual(judgement.verdict, "forbid")
        self.assertIn("Suspicious activity", judgement.reasons[0])

    def test_false_alarm_logic(self):
        """Test that low benefit (Burnt Toast) is AVOIDED."""
        judgement = self.guardian.judge(self.opt_toast)
        self.assertEqual(judgement.verdict, "avoid")
        self.assertIn("Benefit", judgement.reasons[0])


if __name__ == "__main__":
    unittest.main()
