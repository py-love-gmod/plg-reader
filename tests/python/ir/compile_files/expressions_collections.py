x = 42
y = 3.14
s = "hello"
b1 = True
b2 = False
n = None

# имена и атрибуты
a = x.y.z # type: ignore
b = arr[0]  # type: ignore # noqa: F821

# вызовы
c = len([])
d = int("10")

# бинарные операции
e = a + b * c - d / x
f = a // b % c**d
g = a == b
h = a != b
i = a < b > c
j = a and b or c
k = a in b
l = a not in c  # noqa: E741
m = a is b
n1 = a is not b

# унарные
o = -a
p = not b

# тернарный
q = a if b else c

# коллекции
lst = [1, 2, 3]
tup = (1, 2, 3)
st = {1, 2, 3}
dct = {"a": 1, "b": 2}
nest = [[1, 2], (3, 4), {5, 6}]
