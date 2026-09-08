from typing import TYPE_CHECKING, overload


class Draft:  # a trailing comment on the class line
    """One unsaved note."""

    def __init__(self):  # a trailing comment on the def line
        """Start empty."""
        self._title = ""

    def save(self):
        """Write the draft to disk."""

    def render(self):
        """Render the draft; the helper inside is not public."""
        def helper():
            pass
        return helper()

    @property
    def title(self):
        """The note's title."""
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    def _cache(self):
        pass

    class Meta:
        """Settings for the draft."""

        def keys(self):
            """The setting names."""
            return []


def publish(draft):  # a trailing comment
    """Send the draft."""
    return draft


@overload
def parse(value: int) -> int: ...
@overload
def parse(value: str) -> str: ...
def parse(value):
    """Parse a value of either kind."""
    return value


if TYPE_CHECKING:
    def stub():
        """Only for the type checker."""


class _Hidden:
    def shown(self):
        pass
