import time
import unittest
from .debounce import debounce


class TestDebounce(unittest.TestCase):

    @debounce(0.1)
    def increment(self):
        """ Simple function that
            increments a counter when
            called, used to test the
            debounce function decorator """
        self.count += 1

    @debounce(0.1)
    def set_count(self, count):
        self.count = count

    def setUp(self):
        self.count = 0

    def test_debounce(self):
        """ Test that the increment
            function is being debounced.
            The counter should only be incremented
            once 10 seconds after the last call
            to the function """
        self.assertTrue(self.count == 0)
        self.increment()
        self.increment()
        time.sleep(0.09)
        self.assertTrue(self.count == 0)
        self.increment()
        self.increment()
        self.increment()
        self.increment()
        self.assertTrue(self.count == 0)
        time.sleep(0.11)
        self.assertTrue(self.count == 1)

    def test_call_with_last_args(self):
        self.set_count(1)
        self.set_count(2)
        self.set_count(3)
        time.sleep(0.11)
        self.assertTrue(self.count == 3)


if __name__ == '__main__':
    unittest.main()
