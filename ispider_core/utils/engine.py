class EngineSelector:
    def __init__(self, engines):
        self.engines = engines

    def next(self, current=None):
        if current is None:
            return self.engines[0] if self.engines else None
        try:
            index = self.engines.index(current)
            return self.engines[index + 1] if index + 1 < len(self.engines) else None
        except ValueError:
            # current not in the list
            return None

    def next_cyclic(self, current=None):
        if not self.engines:
            return None
        if current is None:
            return self.engines[0]
        try:
            index = self.engines.index(current)
            return self.engines[(index + 1) % len(self.engines)]
        except ValueError:
            # current not in the list
            return self.engines[0]
