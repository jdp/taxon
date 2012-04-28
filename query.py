__all__ = ['Query', 'Tag', 'And', 'Or', 'Not', 'sexpr']


def sexpr(val):
    "Returns the query dict as an S-expression."
    if isinstance(val, dict):
        return sexpr(val.items()[0])
    elif isinstance(val, tuple):
        return "(" + ' '.join([val[0]] + [sexpr(x) for x in sorted(val[1])]) + ")"
    else:
        return str(val)


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
        return {self.op: [c.freeze() for c in self.children]}


class Tag(Query):
    def freeze(self):
        return {"tag": [self.expr]}


class And(Query):
    op = "and"

    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]


class Or(Query):
    op = "or"

    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]


class Not(Query):
    def __init__(self, expr):
        self.expr = Query.coerce(expr)

    def freeze(self):
        return {"not": [self.expr.freeze()]}
