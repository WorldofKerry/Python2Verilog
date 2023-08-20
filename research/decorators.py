import inspect
import logging

gen_funcs = {}


def my_dec(func):
    def generator_wrapper(*args, **kwargs):
        print(f"Called with {str(*args)} {str(**kwargs)}")

        gen_funcs[func] = {"func": func, "source": inspect.getsource(func)}

        def __generator(*args, **kwargs):
            """
            Required to executate function up until first yield
            """
            for result in func(*args, **kwargs):
                yield result

        return __generator(*args, **kwargs)

    def function_wrapper(*args, **kwargs):
        logging.error("Non-generator functions currently not supported")
        return func(*args, **kwargs)

    return generator_wrapper if inspect.isgeneratorfunction(func) else function_wrapper


@my_dec
def my_counter(n):
    i = 0
    while i < n:
        yield (i)
        i += 1


for value in my_counter(5):
    print(value)
inst = my_counter(10)
next(inst)

print(gen_funcs)
for key, value in gen_funcs.items():
    print(type(key), type(value))
