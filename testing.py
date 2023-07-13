# class TestSuper:
#     def __init_subclass__(cls, *args) -> None:
#         print("args", args)


# class TestChild(TestSuper):
#     pass
#     # def __init__(self, var):
#     #     self.var = var


# child = TestChild()


class A:
    def __init__(self, x):
        print("__init__ is called in A")
        self.x = x


class B:
    def __init__(self, *args, **kwargs):
        print("__init__ is called in B")
        super().__init__(*args, **kwargs)


class AB(B, A):
    def __init__(self, *args, **kwargs):
        print("__init__ is called in AB")
        super().__init__(*args, **kwargs)


ab = AB(123)
