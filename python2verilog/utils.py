def indentify(indent: int = 0, text: str = "") -> str:
    """
    Indents a string
    """
    return " " * 4 * indent + text


def buffer_indentify(indent: int = 0, buffers: list[str] = []) -> str:
    """
    Serializes a list of strings with indents
    Note: depreciated by Lines class
    TODO: remove uses and delete function
    """
    output = ""
    for buffer in buffers:
        output += indentify(indent, buffer)
    return output


class IStr(str):
    """
    String with with >> operator for indenting
    """

    def __rshift__(self, other: int) -> str:
        return indentify(other, self)


class Lines:
    """
    A list of str that can be serialized to string with provided indents
    """

    def __init__(self, buffers: list[str] = None) -> None:
        if buffers:
            for buffer in buffers:
                assert isinstance(buffer, str)
            self.buffers = buffers
        else:
            self.buffers = []

    def __add__(self, other: str) -> None:
        assert isinstance(other, str)
        self.buffers.append(other)
        return self

    def __str__(self) -> str:
        return self.toString()

    def __repr__(self) -> str:
        return self.toString()

    def toString(self, indent: int = 0) -> str:
        output = ""
        for buffer in self.buffers:
            output += indentify(indent, buffer) + "\n"
        return output

    def __len__(self) -> int:
        return len(self.buffers)

    def __getitem__(self, key: int) -> str:
        return self.buffers[key]

    def __setitem__(self, key: int, value: str) -> None:
        self.buffers[key] = value

    def __delitem__(self, key: int) -> None:
        del self.buffers[key]


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