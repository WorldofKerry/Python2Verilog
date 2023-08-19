import inspect

functions = {}


def verilogify(func):
    def generator_wrapper(*args, **kwargs):
        functions[func] = {"func": func, "source": inspect.getsource(func)}
        for result in func(*args, **kwargs):
            yield result

    return generator_wrapper


@verilogify
def my_counter(n):
    i = 0
    while i < n:
        yield (i)
        i += 1


for value in my_counter(5):
    print(value)

print(functions)
