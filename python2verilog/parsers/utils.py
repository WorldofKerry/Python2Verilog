from __future__ import annotations


class Lines:
    """
    A list of str that can be serialized to string with provided indents
    """

    @staticmethod
    def assert_no_newline(input: any):
        assert str(input).find("\n") == -1, "Lines should not contain \\n"

    def __init__(self, input: list[str] | str = None):
        if input is None:
            self.lines = []
        elif isinstance(input, str):
            self.assert_no_newline(input)
            self.lines = [input]
        elif isinstance(input, list):
            for line in input:
                assert isinstance(line, str), "Input must be a list of strings"
                self.assert_no_newline(line)
            self.lines = input
        else:
            assert False, "Invalid input type: " + str(type(input))

    def __add__(self, other: str):
        return self.add(other)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, key: int):
        return self.lines[key]

    def __setitem__(self, key: int, value: str):
        self.lines[key] = value

    def __delitem__(self, key: int):
        del self.lines[key]

    def __rshift__(self, indent: int):
        indent(indent)

    def indent(self, indent: int):
        self.lines = [Indent(indent) + line for line in self.lines]
        return self

    def toString(self, indent: int = 0):
        output = ""
        for buffer in self.lines:
            output += Indent(indent) + buffer + "\n"
        return output

    def add(self, other: str):
        assert isinstance(other, str)
        self.assert_no_newline(other)
        self.lines.append(other)
        return self

    def concat(self, other: Lines, indent: int = 0):
        assert isinstance(other, Lines)
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
        assert type(indent) == int
        for pair in buffers:
            assert isinstance(pair[0], Lines), f"{type(pair[0])} {pair[0]}"
            assert isinstance(pair[1], Lines), f"{type(pair[1])} {pair[1]}"
            assert len(pair) == 2
        lines = Lines()
        for i in range(len(buffers)):
            lines.concat(buffers[i][0], indent + i)
        for i in range(len(buffers), 0, -1):
            lines.concat(buffers[i - 1][1], indent + i - 1)
        return lines


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
