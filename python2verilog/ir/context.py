"""Context for Intermediate Representation"""


class Context:
    """
    Context needed by the Intermediate Representation
    E.g. variables, I/O, parameters, localparam
    """

    def __init__(
        self,
        name: str,
        global_vars: dict[str, str],
        input_vars: list[str],
        output_vars: list[str],
    ):
        self.name = name
        self.global_vars = global_vars
        self.input_vars = input_vars
        self.output_vars = output_vars
        # TODO: add strings for name of valid, done, clock, etc.

    def is_declared(self, name: str):
        """
        Checks if a variable has been already declared or not
        """
        return name in set([*self.global_vars, *self.input_vars, *self.output_vars])
