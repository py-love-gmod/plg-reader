def simple():
    pass


def with_args(a, b, c=10):
    return a + b + c


def with_annotations(x: int, y: str) -> int:
    return int(y) + x


# *args и **kwargs
def var_args(a, *args, **kwargs):
    print(a, args, kwargs)


class Empty:
    pass


class WithBases(int, float):
    pass


class WithBody:
    def method(self):
        return self.x  # type: ignore

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass


@decorator  # type: ignore  # noqa: F821
def decorated():
    pass


@decorator_with_args(1, 2)  # type: ignore  # noqa: F821
def decorated2():
    pass
