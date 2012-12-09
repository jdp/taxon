import operator
try:
    from collections import Counter
except ImportError:
    from ._counter import Counter

from .backend import Backend
from ..query import Query


class MemoryBackend(Backend):
    def __init__(self):
        self.empty()

    def tag_items(self, tag, *items):
        if tag not in self.tags:
            self.tags[tag] = 0
            self.tagged[tag] = set()
        new_items = set(items) - self.tagged[tag]
        if len(new_items) == 0:
            return []
        self.tags[tag] += len(new_items)
        self.tagged[tag].update(set(new_items))
        self.items += Counter(new_items)
        return list(new_items)

    def untag_items(self, tag, *items):
        old_items = set(items) & self.tagged[tag]
        if len(old_items) == 0:
            return []
        self.tags[tag] -= len(old_items)
        self.tagged[tag] -= set(old_items)
        self.items -= Counter(old_items)
        return list(old_items)

    def remove_items(self, *items):
        removed = []
        for item in set(items):
            if item not in self.items:
                continue
            for tag in self.all_tags():
                if item not in self.tagged[tag]:
                    continue
                self.tagged[tag] -= set([item])
                self.tags[tag] -= 1
                self.items[item] -= 1
            removed.append(item)
        return removed

    def all_tags(self):
        return [tag[0] for tag in self.tags.items() if tag[1] > 0]

    def all_items(self):
        return [item[0] for item in self.items.items() if item[1] > 0]

    def query(self, q):
        if isinstance(q, Query):
            fn, args = q.freeze()
            return self._raw_query(fn, args)
        elif isinstance(q, tuple):
            fn, args = q
            return self._raw_query(fn, args)
        else:
            raise ValueError

    def _raw_query(self, fn, args):
        if fn == 'tag':
            if len(args) == 1:
                return None, self.tagged.get(args[0], [])
            else:
                groups = [self.tagged.get(tag, []) for tag in args]
                return None, reduce(operator.add, groups)
        elif fn == 'and':
            results = [set(items) for _, items in [self._raw_query(*a) for a in args]]
            return None, reduce(operator.__and__, results)
        elif fn == 'or':
            results = [set(items) for _, items in [self._raw_query(*a) for a in args]]
            return None, reduce(operator.__or__, results)
        elif fn == 'not':
            results = [set(items) for _, items in [self._raw_query(*a) for a in args]]
            results.insert(0, set(self.all_items()))
            return None, reduce(operator.sub, results)
        else:
            raise ValueError

    def empty(self):
        self.tagged = dict()
        self.items = Counter()
        self.tags = Counter()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"%s()" % (self.__class__.__name__)
