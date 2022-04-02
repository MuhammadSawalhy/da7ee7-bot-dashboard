import time
import unittest
import asyncio
from .debounce_async import debounce_async


class TestDebounceAsync(unittest.TestCase):

    @debounce_async(0.1)
    async def increment(self):
        """ Simple function that
            increments a counter when
            called, used to test the
            debounce function decorator """
        self.count += 1

    @debounce_async(0.1)
    async def set_count(self, count):
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
        asyncio.run(self.increment())
        asyncio.run(self.increment())
        time.sleep(0.09)
        self.assertTrue(self.count == 0)
        asyncio.run(self.increment())
        asyncio.run(self.increment())
        asyncio.run(self.increment())
        asyncio.run(self.increment())
        self.assertTrue(self.count == 0)
        time.sleep(0.11)
        self.assertTrue(self.count == 1)

    def test_call_with_last_args(self):
        asyncio.run(self.set_count(1))
        asyncio.run(self.set_count(2))
        asyncio.run(self.set_count(3))
        time.sleep(0.11)
        self.assertTrue(self.count == 3)

if __name__ == '__main__':
    unittest.main()
