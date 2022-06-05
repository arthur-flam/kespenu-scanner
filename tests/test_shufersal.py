import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from shufersal import barcode_metadata


products = [
    ('8801055707010', {
        'name': 'nescafe cappuccino classic',
    }),
]

class TestShufersalMetadata(unittest.TestCase):
  def test_is_int(self):
    barcode, nescafe_data = products[0]
    data = barcode_metadata(barcode, no_cache=True)
    print(data)
    # self.assertEqual(bool(is_int("4")), True)



if __name__ == '__main__':
  unittest.main()
