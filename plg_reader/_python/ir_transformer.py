from __future__ import annotations

from .ir_builder_dt import IRNode


class IRTransformer:
    """
    Базовый класс для преобразования IR-дерева.

    При обходе:
    - Для каждого узла вызывается метод visit_<ClassName>(node).
    - Если такого метода нет, срабатывает generic_visit, который рекурсивно обрабатывает все дочерние поля (списки, словари, одиночные узлы).
    - Узлы модифицируются на месте (in-place), если метод не возвращает явно другой объект.
    - Метод visit_... может вернуть тот же узел (возможно, изменённый), новый узел другого типа или None.
        - Возврат None внутри списка (body, orelse, handlers и т.п.) удаляет элемент из этого списка.
        - Возврат None для одиночного поля (value, target и т.п.) вызывает ошибку.
    """

    def visit(self, node: IRNode | None) -> IRNode | None:
        if node is None:
            return None

        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: IRNode) -> IRNode | None:
        """Обход всех полей узла и замена дочерних IRNode."""
        for field_name in node.__dataclass_fields__:
            if field_name == "pos":
                continue

            value = getattr(node, field_name)

            if isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, IRNode):
                        new_item = self.visit(item)
                        if new_item is not None:
                            new_list.append(new_item)

                    else:
                        new_list.append(item)

                setattr(node, field_name, new_list)

            elif isinstance(value, dict):
                new_dict = {}
                for k, v in value.items():
                    if isinstance(v, IRNode):
                        new_v = self.visit(v)
                        if new_v is not None:
                            new_dict[k] = new_v

                    else:
                        new_dict[k] = v

                setattr(node, field_name, new_dict)

            elif isinstance(value, IRNode):
                new_value = self.visit(value)
                if new_value is None:
                    raise ValueError(
                        f"Поле '{field_name}' узла {type(node).__name__} "
                        f"не может быть удалено (возврат None)"
                    )

                setattr(node, field_name, new_value)

        return node
