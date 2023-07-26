from typing import Optional, Union


class Argument:
    """
    Custom argument class for pytest with unittest

    Note: replaces underscores with dash for the CLI

    Based on: https://stackoverflow.com/a/71786197

    Compatible with _pytest.config.argparsing.Argument

    """

    def __init__(
        self,
        name: str,
        default: Union[str, int, bool],
        help: Optional[str] = None,
        short: Optional[str] = None,
        action: Optional[str] = "store",
    ):
        assert isinstance(name, str)
        if help:
            assert isinstance(help, str)
        if short:
            assert isinstance(short, str)
            assert len(short) == 1

        self.short = short
        self.name = name
        self.value = default  # mutated
        self.help = help
        self.dashed_name = self.name.replace("_", "-")
        self.action = action

    def add_to_parser(self, parser):
        if self.short:
            parser.addoption(
                f"-{self.short}",
                f"--{self.dashed_name}",
                action=self.action,
                default=self.value,
                help=self.help,
            )
        else:
            parser.addoption(
                f"--{self.dashed_name}",
                action=self.action,
                default=self.value,
                help=self.help,
            )

    def __repr__(self):
        return f"{__class__} {self.name}: {self.value}"
