from typing import overload


class Draft:  # a trailing comment on the class line
    def save(self):  # a trailing comment on the def line
        pass

    def render(self):
        def helper():
            pass
        return helper()

    @property
    def title(self):
        return ""

    def _cache(self):
        pass


def publish(draft):  # a trailing comment
    return draft


@overload
def parse(value: int) -> int: ...
@overload
def parse(value: str) -> str: ...
def parse(value):
    return value


class _Hidden:
    def shown(self):
        pass
