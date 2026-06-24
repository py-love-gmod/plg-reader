# Простые подписки
a: list[int] = []
b: dict[str, int] = {}
c: tuple[int, str, float] = (1, "a", 3.14)

# Вложенные подписки
d: dict[str, list[int]] = {"nums": [1, 2]}
e: list[dict[str, set[int]]] = []

# Union (если поддерживается)
f: int | str = 42
g: int | None = None
h: list[int | str] = [1, "a"]


# Аннотации в функциях
def process(data: list[dict[str, int]]) -> dict[str, int] | None:
    return None


# Переменные без значений
x: tuple[int, ...]
y: dict[str, list[int] | tuple[str, ...]]

# Каст в выражении
z = list[int]()
