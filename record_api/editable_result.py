
class EditableResult(tuple):
    def __init__(self, result):
        super(EditableResult, self).__init__()
        self._keys = result.keys()
        for key in result.keys():
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
        return value
