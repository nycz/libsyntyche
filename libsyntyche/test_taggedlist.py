from collections import namedtuple
import unittest

import taggedlist

class TaggedlistTest(unittest.TestCase):

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
        self.assertEqual(tuple(flist4), (Entry('foo bar'), Entry('bars in cars')))


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


    def test_replace_tags(self):
        Entry = namedtuple('Entry', 'index tags')
        entrylist = (
            Entry(0, frozenset(['abc', '123'])),
            Entry(1, frozenset(['abc', 'bloop'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123']))
        )
        # Replace tag, all visible
        list1 = taggedlist.replace_tags('abc', 'haha', entrylist, entrylist, 'tags', None)
        result1 = (
            Entry(0, frozenset(['haha', '123'])),
            Entry(1, frozenset(['haha', 'bloop'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123']))
        )
        self.assertEqual(list1, result1)
        # Replace tag, some visible
        list2 = taggedlist.replace_tags('abc', 'haha', entrylist, entrylist[1:], 'tags', None)
        result2 = (
            Entry(0, frozenset(['abc', '123'])),
            Entry(1, frozenset(['haha', 'bloop'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123']))
        )
        self.assertEqual(list2, result2)
        # Remove tag, all visible
        list3 = taggedlist.replace_tags('123', '', entrylist, entrylist, 'tags', None)
        result3 = (
            Entry(0, frozenset(['abc'])),
            Entry(1, frozenset(['abc', 'bloop'])),
            Entry(2, frozenset(['fishies'])),
            Entry(3, frozenset(['oops', 'nope']))
        )
        self.assertEqual(list3, result3)
        # Add tag, some visible
        list4 = taggedlist.replace_tags('', 'BOOP', entrylist, entrylist[:2] + entrylist[-1:], 'tags', None)
        result4 = (
            Entry(0, frozenset(['abc', '123', 'BOOP'])),
            Entry(1, frozenset(['abc', 'bloop', 'BOOP'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123', 'BOOP']))
        )
        self.assertEqual(list4, result4)


    def test_get_diff(self):
        Entry = namedtuple('Entry', 'index tags')
        entrylist = (
            Entry(0, frozenset(['abc', '123'])),
            Entry(1, frozenset(['abc', 'bloop'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123']))
        )
        identicallist = (
            Entry(0, frozenset(['abc', '123'])),
            Entry(1, frozenset(['abc', 'bloop'])),
            Entry(2, frozenset(['123', 'fishies'])),
            Entry(3, frozenset(['oops', 'nope', '123']))
        )
        self.assertEqual(taggedlist.get_diff(entrylist, identicallist), ())

        differentlist = (
            Entry(0, frozenset(['huhu', '123'])),
            Entry(1, frozenset(['abc', 'bloop'])),
            Entry(2, frozenset(['123'])),
            Entry(3, frozenset(['oops', 'nope', '123', 'naaah']))
        )
        diff = (entrylist[:1]+entrylist[2:], differentlist[:1]+differentlist[2:])
        self.assertEqual(taggedlist.get_diff(entrylist, differentlist), diff)


if __name__ == '__main__':
    unittest.main()