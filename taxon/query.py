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
    """
    Taxon is queried by ``dict`` objects that represent the syntax tree of the
    query. These dict queries can become unwieldy quickly, so the query DSL is
    provided as the main way to query Taxon.

    All subclasses of ``Query`` implement a ``freeze`` method which builds the
    dict representation of the query.
    """

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
        "Returns the ``Query`` representation of the expression."
        if isinstance(expr, Query):
            return expr
        elif isinstance(expr, basestring):
            return Tag(expr)
        else:
            raise TypeError("Expected %s or string, got %s" % (Query.__name__, expr))

    def freeze(self):
        "Returns the ``dict`` representation of the query expression."
        return {self.op: [c.freeze() for c in self.children]}


class Tag(Query):
    "Returns the items with the specified tag."
    def freeze(self):
        return {"tag": [self.expr]}


class And(Query):
    "Returns the items matched by all ``Query`` expressions."

    op = "and"

    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]


class Or(Query):
    "Returns the items matched by any or all of the ``Query`` expressions."

    op = "or"

    def __init__(self, *exprs):
        self.children = [Query.coerce(e) for e in exprs]


class Not(Query):
    "Returns the items **not** matched by any of the ``Query`` expressions."
    
    def __init__(self, expr):
        self.expr = Query.coerce(expr)

    def freeze(self):
        return {"not": [self.expr.freeze()]}
