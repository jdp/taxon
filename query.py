__all__ = ['Query', 'Tag', 'And', 'Or', 'Not']


class Query(object):
    def __init__(self, expr):
        self.expr = expr
        self.children = []

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __invert__(self):
        return Not(self)

    @classmethod
    def coerce(self, expr):
        if isinstance(expr, basestring):
            return Tag(expr)
        else:
            return expr

    def freeze(self):
        return [c.freeze() for c in self.children]


class Tag(Query):
    def freeze(self):
        return {"tag": [self.expr]}


class And(Query):
    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]

    def freeze(self):
        return {"and": [c.freeze() for c in self.children]}


class Or(Query):
    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]

    def freeze(self):
        return {"or": [c.freeze() for c in self.children]}


class Not(Query):
    def __init__(self, expr):
        self.expr = Query.coerce(expr)

    def freeze(self):
        return {"not": [self.expr.freeze()]}
