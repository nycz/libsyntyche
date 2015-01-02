from collections import namedtuple, defaultdict
from functools import partial
from operator import attrgetter
import os
from os.path import exists, join
import re

from common import read_json, read_file
from tagsystem import compile_tag_filter, match_tag_filter

# attributedata = {
#     "filter": (filter_tags, filter_text, filter_number),
#     "parser": (int, lambda x: frozenset(map(lambda y: y.strip(), x.split(',')))),
#     "sortable": bool,
# }



def update_entry(entries, index, attribute, newvalue):
    entry = entries[index]._replace({attribute: newvalue})
    return entries[:index] + (entry,) + entries[index+1:]


def edit_entry(index, entries, attribute, rawnewvalue, attributedata, undostack):
    # if index not in range(len(entries)):
    #     raise IndexError('Entry index out of bounds')
    # if attribute not in attributedata:
    #     raise KeyError('Attribute doesn\'t exist')
    if attributedata[attribute]['parser'] is None:
        raise AttributeError('Attribute is read-only')
    newvalue = attributedata[attribute]['parser'](rawnewvalue)
    return update_entry(entries, index, attribute, newvalue)
    
def replace_tags(oldtag, newtag, entries, attribute, attributedata):
    pass

def undo():
    pass

# (entry, attribute, oldvalue)



# filters = (
#   ('attributename', '>92759<=49792'),
#   ('attrlol', 'fishies'),
#   ('bloopbleep', '(fish, lol) | nope')
# )

def filter_text(attribute, f, entries):
    return filter(lambda entry: f in getattr(entry, attribute), entries)

def filter_number(attribute, f, entries):
    from operator import lt,gt,le,ge
    compfuncs = {'<':lt, '>':gt, '<=':le, '>=':ge}
    expressions = [(compfuncs[m.group(1)], int(m.group(2).replace('k','000')))
                   for m in re.finditer(r'([<>][=]?)(\d+k?)', f)]
    def matches(entry):
        return all(fn(getattr(entry, attribute), num) for fn, num in expressions)
    return filter(matches, entries)

def filter_tags(attribute, f, entries):
    tag_filter = compile_tag_filter(payload)
    return (entry for entry in entries \
            if match_tag_filter(tag_filter, getattr(entry, attribute)))



def filter_entries(entries, filters, attributedata):
    filtered_entries = entries
    filterfuncs = {'text': filter_text, 'number': filter_number, 'tags': filter_tags}
    for attribute, f in filters:
        fntext = attributedata[attribute]['filter']
        if fntext is None:
            raise AttributeError('Attribute can\'t be filtered on')
        if fntext not in ('text', 'tags', 'number'):
            raise KeyError('Unknown filter: {}'.format(fntext))
        fn = filterfuncs[fntext]
        filtered_entries = fn(attribute, f, filtered_entries)
        # filtered_entries = filter(partial(fn, attribute, f), filtered_entries)
    return filtered_entries

def sort_entries(entries, attribute, attributedata, reverse=False):
    if not attributedata[attribute]['sortable']:
        raise AttributeError('Attribute can\'t be sorted by')
    return sorted(entries, attrgetter(attribute), reverse)



# Decoratorstuff

def generate_entrylist(fn):
    def makedict(d):
        return {x:d.get(x, None) for x in ('filter', 'parser', 'sortable')}

    def entrywrapper(*args, **kwargs):
        attributes, entries = fn(*args, **kwargs)
        attributedata = {name:makedict(attr) for name, attr in attributes}
        Entry = namedtuple('Entry', next(zip(*attributes)))
        entrylist = (Entry(*args) for args in entries)
        return attributedata, tuple(entrylist)
    return entrywrapper

@generate_entrylist
def index_stories(path):
    """
    Find all files that match the filter, and return a sorted list
    of them with wordcount, paths and all data from the metadata file.
    """

    attributes = (
        ('title', {'filter': 'text', 'sortable': True}),
        ('tags', {'filter': 'tags'}),
        ('description', {'filter': 'text'}),
        ('length', {'filter': 'number', 'sortable': True}),
        ('file', {}),
        ('metadatafile', {}),
    )
    metafile = lambda dirpath, fname: join(dirpath, '.'+fname+'.metadata')
    files = ((read_json(metafile(dirpath, fname)),
             join(dirpath, fname), metafile(dirpath, fname))
             for dirpath, _, filenames in os.walk(path)
             for fname in filenames
             if os.path.exists(metafile(dirpath, fname)))


    entries = ((metadata['title'],
                frozenset(metadata['tags']),
                metadata['description'],
                len(re.findall(r'\S+', read_file(fname))),
                fname,
                metadatafile)
               for metadata, fname, metadatafile in files)

    return attributes, entries




if __name__ == '__main__':
    attributedata, entries = index_stories('/home/nycz/stories')
    print(*entries, sep='\n\n')