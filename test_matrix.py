import unittest

from matrix import Matrix

def default_item():
    return 'TEST'

class MatrixGenericTest(unittest.TestCase):

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

    def test_has_coord(self):
        self.assertTrue(self.matrix.has_coord(1, 0))
        self.assertTrue(self.matrix.has_coord(2, 1))
        self.assertFalse(self.matrix.has_coord(3, 1))

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

    def test_remove_row(self):
        data = [
            ['One', 'Two', 'Three']
        ]
        self.matrix.remove_row(1)
        self.assertEqual(self.matrix.data, data)

    def test_remove_col(self):
        data = [
            ['One', 'Two'],
            ['Aye', 'Bee']
        ]
        self.matrix.remove_col(2)
        self.assertEqual(self.matrix.data, data)

    def test_copy_row_down(self):
        data = [
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See'],
            ['One', 'Two', 'Three']
        ]
        self.matrix.copy_row(0,2)
        self.assertEqual(self.matrix.data, data)

    def test_copy_row_up(self):
        data = [
            ['Aye', 'Bee', 'See'],
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See']
        ]
        self.matrix.copy_row(1,0)
        self.assertEqual(self.matrix.data, data)

    def test_copy_col_left(self):
        data = [
            ['One', 'Three', 'Two', 'Three'],
            ['Aye', 'See', 'Bee', 'See'],
        ]
        self.matrix.copy_col(2,1)
        self.assertEqual(self.matrix.data, data)

    def test_copy_col_right(self):
        data = [
            ['One', 'Two', 'Three', 'One'],
            ['Aye', 'Bee', 'See', 'Aye'],
        ]
        self.matrix.copy_col(0,3)
        self.assertEqual(self.matrix.data, data)


class MatrixMoveTest(unittest.TestCase):

    def setUp(self):
        data = [
            ['One', 'Two', 'Three', 'Four'],
            ['Aye', 'Bee', 'See', 'Door'],
            ['Bip', 'Blop', 'Foo', 'Bar'],
            ['Cats', 'Dogs', 'Yay', 'Oops']
        ]
        self.matrix = Matrix(default_item, data)

    def test_move_row_down(self):
        data = [
            ['Aye', 'Bee', 'See', 'Door'],
            ['Bip', 'Blop', 'Foo', 'Bar'],
            ['One', 'Two', 'Three', 'Four'],
            ['Cats', 'Dogs', 'Yay', 'Oops']
        ]
        self.matrix.move_row(0,2)
        self.assertEqual(self.matrix.data, data)

    def test_move_row_up(self):
        data = [
            ['One', 'Two', 'Three', 'Four'],
            ['Aye', 'Bee', 'See', 'Door'],
            ['Cats', 'Dogs', 'Yay', 'Oops'],
            ['Bip', 'Blop', 'Foo', 'Bar']
        ]
        self.matrix.move_row(3,2)
        self.assertEqual(self.matrix.data, data)

    def test_move_row_last_to_first(self):
        data = [
            ['Cats', 'Dogs', 'Yay', 'Oops'],
            ['One', 'Two', 'Three', 'Four'],
            ['Aye', 'Bee', 'See', 'Door'],
            ['Bip', 'Blop', 'Foo', 'Bar']
        ]
        self.matrix.move_row(3,0)
        self.assertEqual(self.matrix.data, data)

    def test_move_row_first_to_last(self):
        data = [
            ['Aye', 'Bee', 'See', 'Door'],
            ['Bip', 'Blop', 'Foo', 'Bar'],
            ['Cats', 'Dogs', 'Yay', 'Oops'],
            ['One', 'Two', 'Three', 'Four']
        ]
        self.matrix.move_row(0,3)
        self.assertEqual(self.matrix.data, data)

    def test_move_col_right(self):
        data = [
            ['One', 'Three', 'Four', 'Two'],
            ['Aye', 'See', 'Door', 'Bee'],
            ['Bip', 'Foo', 'Bar', 'Blop'],
            ['Cats', 'Yay', 'Oops', 'Dogs']
        ]
        self.matrix.move_col(1,3)
        self.assertEqual(self.matrix.data, data)

    def test_move_col_left(self):
        data = [
            ['One', 'Three', 'Two', 'Four'],
            ['Aye', 'See', 'Bee', 'Door'],
            ['Bip', 'Foo', 'Blop', 'Bar'],
            ['Cats', 'Yay', 'Dogs', 'Oops']
        ]
        self.matrix.move_col(2,1)
        self.assertEqual(self.matrix.data, data)

    def test_move_col_last_to_first(self):
        data = [
            ['Four', 'One', 'Two', 'Three'],
            ['Door', 'Aye', 'Bee', 'See'],
            ['Bar', 'Bip', 'Blop', 'Foo'],
            ['Oops', 'Cats', 'Dogs', 'Yay']
        ]
        self.matrix.move_col(3,0)
        self.assertEqual(self.matrix.data, data)

    def test_move_col_first_to_last(self):
        data = [
            ['Two', 'Three', 'Four', 'One'],
            ['Bee', 'See', 'Door', 'Aye'],
            ['Blop', 'Foo', 'Bar', 'Bip'],
            ['Dogs', 'Yay', 'Oops', 'Cats']
        ]
        self.matrix.move_col(0,3)
        self.assertEqual(self.matrix.data, data)


class MatrixOffsetTest(unittest.TestCase):

    def setUp(self):
        data = [
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See']
        ]
        self.matrix = Matrix(default_item, data, offset=1)

    def test_getitem(self):
        self.assertEqual(self.matrix[1,2], 'Aye')
        self.assertEqual(self.matrix[3,1], 'Three')
        self.assertNotEqual(self.matrix[1,1], 'See')

    def test_setitem(self):
        newval = 'NEW!!'
        self.matrix[2,1] = newval
        self.assertEqual(self.matrix.data[0][1], newval)

    def test_has_coord(self):
        self.assertTrue(self.matrix.has_coord(1, 1))
        self.assertTrue(self.matrix.has_coord(3, 2))
        self.assertFalse(self.matrix.has_coord(5, 1))
        self.assertFalse(self.matrix.has_coord(2, 0))

    def test_add_row(self):
        newrow = [default_item()]*3
        data = [
            ['One', 'Two', 'Three'],
            newrow,
            ['Aye', 'Bee', 'See']
        ]
        self.matrix.add_row(2)
        self.assertEqual(self.matrix.data, data)
        data = [
            newrow,
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
        self.matrix.add_col(2)
        self.assertEqual(self.matrix.data, data)
        data = [
            [default_item(), 'One', default_item(), 'Two', 'Three'],
            [default_item(), 'Aye', default_item(), 'Bee', 'See']
        ]
        self.matrix.add_col(1)
        self.assertEqual(self.matrix.data, data)
        data = [
            [default_item(), 'One', default_item(), 'Two', 'Three', default_item()],
            [default_item(), 'Aye', default_item(), 'Bee', 'See', default_item()]
        ]
        self.matrix.add_col()
        self.assertEqual(self.matrix.data, data)

    def test_remove_row(self):
        data = [
            ['One', 'Two', 'Three']
        ]
        self.matrix.remove_row(2)
        self.assertEqual(self.matrix.data, data)

    def test_remove_col(self):
        data = [
            ['One', 'Two'],
            ['Aye', 'Bee']
        ]
        self.matrix.remove_col(3)
        self.assertEqual(self.matrix.data, data)

    def test_copy_row_down(self):
        data = [
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See'],
            ['One', 'Two', 'Three']
        ]
        self.matrix.copy_row(1,3)
        self.assertEqual(self.matrix.data, data)

    def test_copy_row_up(self):
        data = [
            ['Aye', 'Bee', 'See'],
            ['One', 'Two', 'Three'],
            ['Aye', 'Bee', 'See']
        ]
        self.matrix.copy_row(2,1)
        self.assertEqual(self.matrix.data, data)

    def test_copy_col_left(self):
        data = [
            ['One', 'Three', 'Two', 'Three'],
            ['Aye', 'See', 'Bee', 'See'],
        ]
        self.matrix.copy_col(3,2)
        self.assertEqual(self.matrix.data, data)

    def test_copy_col_right(self):
        data = [
            ['One', 'Two', 'Three', 'One'],
            ['Aye', 'Bee', 'See', 'Aye'],
        ]
        self.matrix.copy_col(1,4)
        self.assertEqual(self.matrix.data, data)
