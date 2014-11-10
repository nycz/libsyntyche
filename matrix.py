
class Matrix():
    def __init__(self, default_item, data=None):
        self.default_item = default_item
        if data:
            self.data = data
        else:
            self.data = [[self.default_item()]]

    def __str__(self):
        return '\n'.join(repr(row) for row in self.data)
        # return '\n'.join('\t|\t'.join(repr(x) for x in row) for row in self.data)

    def __contains__(self, key):
        for row in self.data:
            if key in row:
                return True
        return False

    def __getitem__(self, key):
        x, y = key
        return self.data[y][x]

    def __setitem__(self, key, value):
        x, y = key
        # if not value:
        #     self.data[y][x] = default_item()
        #     return
        # text, (w, h) = value
        # assert isinstance(text, str) and isinstance(w, int) and isinstance(h, int)
        self.data[y][x] = value


    def clear(self):
        self.data = [[self.default_item()]]

    def flip_orientation(self):
        self.data = list(map(list, zip(*self.data)))

    def count_rows(self):
        return len(self.data)

    def count_cols(self):
        return len(self.data[0])

    def add_row(self, pos=-1):
        data = [self.default_item() for _ in range(self.count_cols())]
        if pos == -1:
            self.data.append(data)
        else:
            self.data.insert(pos, data)

    def add_col(self, pos=-1):
        for n in range(self.count_rows()):
            if pos == -1:
                self.data[n].append(self.default_item())
            else:
                self.data[n].insert(pos, self.default_item())

    def remove_row(self, pos):
        del self.data[pos]

    def remove_col(self, pos):
        for n in range(len(self.data)):
            del self.data[n][pos]

    def move_row(self, oldpos, newpos):
        row = self.data.pop(oldpos)
        self.data.insert(newpos, row)

    def move_col(self, oldpos, newpos):
        for n in range(len(self.data)):
            self.data[n].insert(newpos, oldpos)

    def copy_row(self, oldpos, newpos):
        row = self.data[oldpos].copy()
        self.data.insert(newpos, row)

    def copy_col(self, oldpos, newpos):
        for n in range(len(self.data)):
            if newpos == -1:
                self.data[n].append(self.data[n][oldpos])
            else:
                self.data[n].insert(newpos, self.data[n][oldpos])

    def row(self, pos):
        return self.data[pos]

    def col(self, pos):
        return [x[pos] for x in self.data]