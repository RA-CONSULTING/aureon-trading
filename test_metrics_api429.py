import unittest
from metrics import api_429_counter, get_metric_value

class TestMetricsApi429(unittest.TestCase):
    def test_api_429_counter(self):
        # Resetting not available; just increment and assert readback
        api_429_counter.inc(1, exchange='testex', endpoint='testpath')
        val = get_metric_value(api_429_counter, exchange='testex', endpoint='testpath')
        self.assertEqual(val, 1.0)

if __name__ == '__main__':
    unittest.main()
