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

    def test_clear(self):
        self.matrix.clear()
        self.assertEqual(self.matrix.data, [[default_item()]])

    def test_flip_orientation(self):
        self.matrix.flip_orientation()
        data = [
            ['One', 'Aye'],
            ['Two', 'Bee'],
            ['Three', 'See']
        ]
        self.assertEqual(self.matrix.data, data)

    def test_count_rows(self):
        self.assertEqual(self.matrix.count_rows(), 2)

    def test_count_cols(self):
        self.assertEqual(self.matrix.count_cols(), 3)

    def test_add_row(self):
        newrow = [default_item()]*3

        data = [
            ['One', 'Two', 'Three'],
            newrow,
            ['Aye', 'Bee', 'See']
        ]
        self.matrix.add_row(1)
        self.assertEqual(self.matrix.data, data)
        data = [
            newrow,
            ['One', 'Two', 'Three'],
            newrow,
            ['Aye', 'Bee', 'See']
        ]
        self.matrix.add_row(0)
        self.assertEqual(self.matrix.data, data)
        data = [
            newrow,
            ['One', 'Two', 'Three'],
            newrow,
            ['Aye', 'Bee', 'See'],
            newrow
        ]
        self.matrix.add_row()
        self.assertEqual(self.matrix.data, data)

    def test_add_col(self):
        data = [
            ['One', default_item(), 'Two', 'Three'],
            ['Aye', default_item(), 'Bee', 'See']
        ]
        self.matrix.add_col(1)
        self.assertEqual(self.matrix.data, data)
        data = [
            [default_item(), 'One', default_item(), 'Two', 'Three'],
            [default_item(), 'Aye', default_item(), 'Bee', 'See']
        ]
        self.matrix.add_col(0)
        self.assertEqual(self.matrix.data, data)
        data = [
            [default_item(), 'One', default_item(), 'Two', 'Three', default_item()],
            [default_item(), 'Aye', default_item(), 'Bee', 'See', default_item()]
        ]
        self.matrix.add_col()
        self.assertEqual(self.matrix.data, data)