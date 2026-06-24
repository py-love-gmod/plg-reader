# Список внутри подписки
x = list[list[int]]()

# Подписка внутри вызова
y = some_func(dict[str, int]())  # type: ignore # noqa: F821

# Цепочка: вызов -> подписка -> вызов
z = get_registry()["key"]()  # type: ignore # noqa: F821

# Подписка с оператором |
mixed = list[int | str]()
