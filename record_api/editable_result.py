class EditableResult(tuple):
    def __init__(self, result):
        super(EditableResult, self).__init__()
        self._keys = list(result.keys())
        for key in self._keys:
            if isinstance(result, dict):
                setattr(self, key, result[key])
            else:
                setattr(self, key, getattr(result, key))
        self.startIndex = 0

    def __iter__(self):
        self.startIndex = 0
        return self

    def __next__(self):
        if self.startIndex < 0 or self.startIndex >= len(self._keys):
            raise StopIteration
        value = self._keys[self.startIndex]
        self.startIndex += 1
        return getattr(self, value)

    def set(self, key, value):
        if key not in self._keys:
            self._keys.append(key)

        setattr(self, key, value)
