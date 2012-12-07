class Backend(object):
    def __init__(self):
        pass

    def tag_items(self, tag, *items):
        raise NotImplementedError

    def untag_items(self, tag, *items):
        raise NotImplementedError

    def remove_items(self, *items):
        raise NotImplementedError

    def all_tags(self):
        raise NotImplementedError

    def all_items(self):
        raise NotImplementedError

    def query(self, q):
        raise NotImplementedError

    def empty(self):
        raise NotImplementedError
