import unittest

from matrix import Matrix

def default_item():
    return 'TEST'

class MatrixTest(unittest.TestCase):

    def setUp(self):
        data = [
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See']
        ]
        self.matrix = Matrix(default_item, data)

    def test_contains(self):
        self.assertIn('Two', self.matrix)
        self.assertIn('See', self.matrix)
        self.assertNotIn('Fish', self.matrix)
        self.assertNotIn('whoops', self.matrix)

