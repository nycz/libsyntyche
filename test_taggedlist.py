from collections import namedtuple
import unittest

import taggedlist

class TaggedlistTest(unittest.TestCase):

    # def setUp(self):
    #     self.entrylist = (
    #         ()
    #     )

    def test_filter_text(self):
        Entry = namedtuple('Entry', 'text')
        entrylist = (Entry('foo bar'), Entry('fishies'), Entry('bars in cars'))
        flist1 = taggedlist.filter_text('text', 'foo', entrylist)
        flist2 = taggedlist.filter_text('text', 'bar', entrylist)
        flist3 = taggedlist.filter_text('text', 'f', entrylist)
        flist4 = taggedlist.filter_text('text', 'BAR', entrylist)
        self.assertEqual(tuple(flist1), (Entry('foo bar'),))
        self.assertEqual(tuple(flist2), (Entry('foo bar'), Entry('bars in cars')))
        self.assertEqual(tuple(flist3), (Entry('foo bar'), Entry('fishies')))
        self.assertEqual(tuple(flist4), ())


    def test_filter_number(self):
        Entry = namedtuple('Entry', 'length')
        entrylist = (Entry(1000), Entry(800), Entry(16790), Entry(12))
        flist1 = taggedlist.filter_number('length', '>800', entrylist)
        flist2 = taggedlist.filter_number('length', '>20<=1000', entrylist)
        flist3 = taggedlist.filter_number('length', '>16k', entrylist)
        flist4 = taggedlist.filter_number('length', '<=1k', entrylist)
        self.assertEqual(tuple(flist1), (Entry(1000), Entry(16790)))
        self.assertEqual(tuple(flist2), (Entry(1000), Entry(800)))
        self.assertEqual(tuple(flist3), (Entry(16790),))
        self.assertEqual(tuple(flist4), (Entry(1000), Entry(800), Entry(12)))
