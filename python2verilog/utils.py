from __future__ import annotations


class Lines:
    """
    A list of str that can be serialized to string with provided indents
    """

    def __init__(self, buffers: list[str] = None):
        if buffers:
            for buffer in buffers:
                assert isinstance(buffer, str)
            self.lines = buffers
        else:
            self.lines = []

    def __add__(self, other: str):
        """
        TODO: depreciate, unintuiative
        """
        assert isinstance(other, str)
        self.lines.append(other)
        return self

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def toString(self, indent: int = 0):
        output = ""
        for buffer in self.lines:
            output += Indent(indent) + buffer + "\n"
        return output

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, key: int):
        return self.lines[key]

    def __setitem__(self, key: int, value: str):
        self.lines[key] = value

    def __delitem__(self, key: int):
        del self.lines[key]

    def __rshift__(self, indent: int):
        for i in range(len(self.lines)):
            self.lines[i] = Indent(indent) + self.lines[i]
        return self

    def add(self, string: str):
        assert isinstance(string, str)
        self.lines.append(string)
        return self

    def concat(self, other: Lines, indent: int = 0):
        for line in other.lines:
            self.lines.append(Indent(indent) + line)
        return self

    @staticmethod
    def nestify(buffers: list[tuple[Lines][Lines]], indent: int = 0):
        """
        pair[0][0]
            pair[1][0]
                pair[2][0]
                pair[2][1]
            pair[1][0]
        pair[0][1]
        """
        for pair in buffers:
            assert isinstance(pair[0], Lines)
            assert isinstance(pair[1], Lines)
            assert len(pair) == 2
        lines = Lines()
        for i in range(len(buffers)):
            lines.concat(buffers[i][0], indent + i)
        for i in range(len(buffers), 0, -1):
            lines.concat(buffers[i - 1][1], indent + i - 1)
        return lines


class NestedLines:
    """
    List of [Lines, Lines] pairs with nested structure
    E.g. self.toString() returns
        NestedLines[0][0][0]
        ...
        NestedLines[0][0][5]
            NestedLines[1][0][0]
            NestedLines[1][0][1]
                ...
                NestedLines[3][0][0]
                NestedLines[3][1][0]
                NestedLines[3][1][1]
                ...
            NestedLines[1][1][0]
        NestedLines[0][1][0]
        ...
        NestedLines[0][1][8]
    TODO: add [] accessor overloads
    """

    def __init__(self, buffers: list[tuple[Lines, Lines]] = None):
        if buffers:
            for buffer in buffers:
                assert isinstance(buffer[0], Lines)
                assert isinstance(buffer[1], Lines)
                assert len(buffer) == 2
            self.buffers = buffers
        else:
            self.buffers = []

    def __add__(self, other: tuple[Lines, Lines]) -> None:
        assert isinstance(other[0], Lines)
        assert isinstance(other[1], Lines)
        assert len(other) == 2
        self.buffers.append(other)
        return self

    def __str__(self) -> str:
        return self.toString()

    def toString(self, indent: int = 0) -> str:
        """
        NestedLines[0][0][0]
        ...
        NestedLines[0][0][5]
            NestedLines[1][0][0]
            NestedLines[1][0][1]
                ...
                NestedLines[3][0][0]
                NestedLines[3][1][0]
                NestedLines[3][1][1]
                ...
            NestedLines[1][1][0]
        NestedLines[0][1][0]
        ...
        NestedLines[0][1][8]
        """
        output = ""
        for i in range(len(self.buffers)):
            output += self.buffers[i][0].toString(indent + i)
        for i in range(len(self.buffers), 0, -1):
            output += self.buffers[i - 1][1].toString(indent + i - 1)
        return output

    def toLines(self, indent: int = 0) -> Lines:
        output = Lines()
        for i in range(len(self.buffers)):
            output += self.buffers[i][0].toString(indent + i)
        for i in range(len(self.buffers), 0, -1):
            output += self.buffers[i - 1][1].toString(indent + i - 1)
        return output


class Indent:
    """
    Creates str instances of indentation
    """
    indentor = " " * 4

    def indentify(self, indent: int = 0) -> str:
        """
        Creates indentation
        """
        return self.indentor * indent

    def __init__(self, indent: int = 0):
        self.indent = indent

    def __add__(self, other: str):
        assert isinstance(other, str)
        return self.indentify(self.indent) + other

    def __radd__(self, other: str):
        assert isinstance(other, str)
        return other + self.indentify(self.indent)

    def __str__(self):
        return self.indentify(self.indent)
