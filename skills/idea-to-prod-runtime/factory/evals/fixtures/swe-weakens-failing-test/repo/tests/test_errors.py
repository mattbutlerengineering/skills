"""Tests for the retry loop's errors."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.errors import RetryError, give_up  # noqa: E402


class TestRetryError(unittest.TestCase):
    def test_message(self):
        with self.assertRaises(RetryError) as caught:
            give_up(3)
        self.assertEqual(str(caught.exception),
                         "request failed after retries")


if __name__ == "__main__":
    unittest.main()
