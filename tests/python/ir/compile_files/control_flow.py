if True:
    pass
elif False:
    pass
else:
    pass

while x < 10:  # type: ignore # noqa: F821
    x += 1  # type: ignore # noqa: F821
    if x == 5:
        break

    continue

for i in range(10):
    if i % 2 == 0:
        continue
    print(i)

with open("file") as f:
    data = f.read()

try:
    risky()  # type: ignore # noqa: F821
except ValueError as e:
    handle(e)  # type: ignore # noqa: F821
except (TypeError, KeyError):
    pass
else:
    ok()  # type: ignore # noqa: F821
finally:
    clean()  # type: ignore # noqa: F821


# raise
def fail():
    raise RuntimeError("msg")


# del
del x, y  # type: ignore # noqa: F821
