
class Matrix():
    def __init__(self, default_item, data=None, offset=0):
        self.default_item = default_item
        self.offset = offset
        if data:
            self.data = [x.copy() for x in data]
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
        return self.data[y-self.offset][x-self.offset]

    def __setitem__(self, key, value):
        x, y = key
        self.data[y-self.offset][x-self.offset] = value

    def clear(self):
        self.data = [[self.default_item()]]

    def flip_orientation(self):
        self.data = list(map(list, zip(*self.data)))

    def has_coord(self, x, y):
        return x-self.offset in range(self.count_cols()) and y-self.offset in range(self.count_rows())

    def count_rows(self):
        return len(self.data)

    def count_cols(self):
        return len(self.data[0])

    def add_row(self, pos=-1):
        data = [self.default_item() for _ in range(self.count_cols())]
        if pos == -1:
            self.data.append(data)
        else:
            self.data.insert(pos-self.offset, data)

    def add_col(self, pos=-1):
        for n in range(self.count_rows()):
            if pos == -1:
                self.data[n].append(self.default_item())
            else:
                self.data[n].insert(pos-self.offset, self.default_item())

    def remove_row(self, pos):
        del self.data[pos-self.offset]

    def remove_col(self, pos):
        for n in range(self.count_rows()):
            del self.data[n][pos-self.offset]

    def move_row(self, oldpos, newpos):
        row = self.data.pop(oldpos-self.offset)
        self.data.insert(newpos-self.offset, row)

    def move_col(self, oldpos, newpos):
        for n in range(len(self.data)):
            x = self.data[n].pop(oldpos-self.offset)
            self.data[n].insert(newpos-self.offset, x)

    def copy_row(self, oldpos, newpos):
        row = self.data[oldpos-self.offset].copy()
        self.data.insert(newpos-self.offset, row)

    def copy_col(self, oldpos, newpos):
        col = self.col(oldpos)
        for n in range(len(self.data)):
            self.data[n].insert(newpos-self.offset, col[n])

    def row(self, pos):
        return self.data[pos-self.offset]

    def col(self, pos):
        return [x[pos-self.offset] for x in self.data]