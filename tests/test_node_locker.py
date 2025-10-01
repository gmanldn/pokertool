import unittest

from src.pokertool.node_locker import NodeLock, NodeLocker


class TestNodeLock(unittest.TestCase):
    """Unit tests for individual node lock behaviour."""

    def test_clamp_respects_bounds(self):
        """Clamp should return values within configured min/max range."""
        lock = NodeLock(node_id="n1", action="raise", min_frequency=0.2, max_frequency=0.4)

        self.assertEqual(lock.clamp(0.1), 0.2)
        self.assertEqual(lock.clamp(0.3), 0.3)
        self.assertEqual(lock.clamp(0.5), 0.4)

    def test_to_dict_serialises_fields(self):
        """NodeLock serialises to dictionary with all fields."""
        lock = NodeLock(node_id="n1", action="call", min_frequency=0.1, max_frequency=0.3)

        data = lock.to_dict()

        self.assertEqual(
            data,
            {
                "node_id": "n1",
                "action": "call",
                "min_frequency": 0.1,
                "max_frequency": 0.3,
            },
        )


class TestNodeLocker(unittest.TestCase):
    """Unit tests for NodeLocker management and application."""

    def setUp(self):
        self.locker = NodeLocker()

    def test_lock_action_validates_bounds(self):
        """lock_action rejects invalid bounds."""
        with self.assertRaises(ValueError):
            self.locker.lock_action("node", "raise", min_frequency=-0.1, max_frequency=0.5)
        with self.assertRaises(ValueError):
            self.locker.lock_action("node", "raise", min_frequency=0.1, max_frequency=1.5)
        with self.assertRaises(ValueError):
            self.locker.lock_action("node", "raise", min_frequency=0.8, max_frequency=0.6)

    def test_unlock_action_specific_and_all(self):
        """unlock_action removes specific locks and entire nodes."""
        self.locker.lock_action("node", "raise", 0.2, 0.4)
        self.locker.lock_action("node", "call", 0.1, 0.3)

        self.locker.unlock_action("node", "raise")
        locks_after_partial = self.locker.get_locks("node")
        self.assertNotIn("raise", {lock.action for lock in locks_after_partial["node"]})

        self.locker.unlock_action("node")
        self.assertEqual(self.locker.get_locks("node"), {})

    def test_apply_all_actions_locked_with_zero_mass(self):
        """When all actions are locked and mass is zero, strategy becomes uniform."""
        for action in ("raise", "call"):
            self.locker.lock_action("node", action, 0.0, 0.0)

        strategy = {"raise": 0.0, "call": 0.0}
        adjusted, locks = self.locker.apply("node", strategy)

        self.assertAlmostEqual(adjusted["raise"], 0.5)
        self.assertAlmostEqual(adjusted["call"], 0.5)
        self.assertEqual(set(locks.keys()), {"raise", "call"})

    def test_apply_free_actions_zero_total_distributes_evenly(self):
        """When free actions have zero total, residual mass is shared evenly."""
        self.locker.lock_action("node", "raise", 0.4, 0.6)

        strategy = {"raise": 0.5, "call": 0.0, "fold": 0.0}
        adjusted, _ = self.locker.apply("node", strategy)

        self.assertAlmostEqual(adjusted["raise"], 0.5, places=6)
        self.assertAlmostEqual(adjusted["call"], 0.25, places=6)
        self.assertAlmostEqual(adjusted["fold"], 0.25, places=6)

    def test_export_and_clear(self):
        """export returns all locks and clear resets state."""
        self.locker.lock_action("node", "raise", 0.2, 0.4)

        exported = self.locker.export()
        self.assertIn("node", exported)
        self.assertIn("raise", exported["node"])

        self.locker.clear()
        self.assertEqual(self.locker.get_locks(), {})


if __name__ == "__main__":
    unittest.main()
