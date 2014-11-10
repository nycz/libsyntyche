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

    def test_getitem(self):
        self.assertEqual(self.matrix[0,1], 'Aye')
        self.assertEqual(self.matrix[2,0], 'Three')
        self.assertNotEqual(self.matrix[1,1], 'See')

    def test_setitem(self):
        newval = 'NEW!!'
        self.matrix[2,1] = newval
        self.assertEqual(self.matrix.data[1][2], newval)