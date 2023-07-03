def indentify(indent: int = 0, text: str = "") -> str:
    return " " * 4 * indent + text


def buffer_indentify(indent: int = 0, buffers: list[str] = []) -> str:
    output = ""
    for buffer in buffers:
        output += indentify(indent, buffer)
    return output


class StringBuffer:
    def __init__(self, buffers: list[str] = None) -> None:
        if buffers:
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

        

class ListBuffer:
    def __init__(self, buffers: list[tuple[StringBuffer, StringBuffer]] = None):
        if buffers: 
            for buffer in buffers:
                assert isinstance(buffer[0], StringBuffer)
                assert isinstance(buffer[1], StringBuffer)
                assert len(buffer) == 2
            self.buffers = buffers
        else: 
            self.buffers = []

    def __add__(self, other: tuple[StringBuffer, StringBuffer]) -> None:
        assert isinstance(other[0], StringBuffer)
        assert isinstance(other[1], StringBuffer)
        assert len(other) == 2
        self.buffers.append(other)
        return self

    def __str__(self) -> str:
        return self.toString()

    def toString(self, indent: int = 0) -> str:
        """
        StringBuffer0A
            StringBuffer1A
                ...
            StringBuffer1B
        StringBuffer0B
        """
        output = ""
        for i in range(len(self.buffers)):
            output += self.buffers[i][0].toString(indent + i)
        for i in range(len(self.buffers), 0, -1):
            output += self.buffers[i - 1][1].toString(indent + i - 1)
        return output
