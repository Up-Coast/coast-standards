#!/usr/bin/env python3
"""Read a JSON file that is allowed comments and trailing commas — tsconfig.json,
.eslintrc.json and the rest of the JSONC family.

Written because the push gate stripped comments with the regex ``//.*|/\\*.*?\\*/``,
which does not know what a string is. It is not one project's problem: the alias
``"@/*"`` is the conventional TypeScript path mapping, so the check was wrong on most
TypeScript repositories. one adopting web project's tsconfig maps ``"@/*"`` to
``["./src/*"]``, the regex read ``/*`` inside that path as a comment opener, ate the rest
of the file, and the gate refused the push saying ``compilerOptions.strict is not true``
when it was true on line 7. A scanner that tracks string state cannot make that mistake.

Usage:  python3 jsonc.py <file> [dotted.key]
        exit 0 and print the value, or exit 1 when the file will not parse or the key
        is missing. Import ``load(path)`` for the parsed object.
"""

import json
import sys


def strip(text):
    """The same document with comments and trailing commas removed, strings untouched."""
    out = []
    index = 0
    end = len(text)
    in_string = False
    escaped = False
    while index < end:
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < end and text[index + 1] == "/":
            while index < end and text[index] != "\n":
                index += 1
            continue
        if char == "/" and index + 1 < end and text[index + 1] == "*":
            index += 2
            while index + 1 < end and not (text[index] == "*" and text[index + 1] == "/"):
                index += 1
            index += 2
            continue
        if char == ",":
            look = index + 1
            while look < end and text[look] in " \t\r\n":
                look += 1
            if look < end and text[look] in "}]":
                index += 1
                continue
        out.append(char)
        index += 1
    return "".join(out)


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.loads(strip(handle.read()))


def main(argv):
    if not argv:
        print("usage: jsonc.py <file> [dotted.key]")
        return 2
    try:
        data = load(argv[0])
    except (OSError, ValueError) as problem:
        print(f"jsonc.py: {argv[0]} will not parse: {problem}")
        return 1
    if len(argv) < 2:
        print(json.dumps(data))
        return 0
    for step in argv[1].split("."):
        if not isinstance(data, dict) or step not in data:
            return 1
        data = data[step]
    print(json.dumps(data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
