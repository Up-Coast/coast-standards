#!/usr/bin/env python3
"""check_doc_comments.py — the ``doc-comments`` check (DOC-1 / STYLE-4, enforcement task E1.5).

Every public declaration carries a doc comment, or the generated API reference
has nothing to render. This is Coast's own check (``DocsGeneration.docCommentCheck``
and the scanners under it) ported to Python so that ONE implementation runs in
the editor hook, the pre-commit hook, the pre-push battery, CI and Coast's own
build loop — the Swift implementation is retired once the parity run on Coast's
own tree (recorded in enforcement/README.md, E1.5) agrees.

What it reads, per language, exactly as Coast's scanners do:

* **Swift** — over sanitized source (ordinary comments and string contents
  removed, ``///`` and ``/** */`` doc comments kept): top-level types with
  their direct members, top-level functions and properties. A declaration
  is public when it says ``public``/``open``, when it is a member of a public
  protocol or of a ``public extension``, or when it is a case of a public
  enum. Members of a public type are scanned; members of an internal type
  are not. Extensions fold into their type when the type is declared in the
  same module (``Sources/<Target>/**`` or ``Modules/<M>/Sources/**``); an
  extension of a type from elsewhere is scanned through its members. Enum
  cases, associated types and extensions themselves need no doc.
* **Kotlin / Java** — Kotlin's default visibility is public; Java's is
  package-private, so a Java declaration is public only when it says so;
  members of a non-public container are not public; a Java interface's
  members are implicitly public. Members of nested types, declarations
  inside function bodies and property accessors are not read (the scanner's
  stated limit). No folding.
* **TypeScript / JavaScript** — over JavaScript-sanitized source (``'…'``,
  ``"…"`` and template strings emptied, ``${…}`` interpolations still read):
  exported top-level declarations (``export [default] [abstract] class |
  interface | type | enum | function | const | let | var``) and, inside an
  exported class or interface, its members that are not
  ``private``/``protected``/``#name``/``constructor``. A doc is a ``/** */``
  block directly above; decorators (multi-line ones too) and ``//`` comments
  may sit between, a blank line may not.
* **Python** — read with the stdlib ``ast`` module: module-level
  ``def``/``class`` whose name does not start with ``_`` (inside ``if``,
  ``try`` and ``with`` blocks too), and inside a public class its public
  methods, ``__init__`` (PEP 257) and nested public classes. A doc is a
  docstring as the first statement. An ``@overload`` signature and a
  property's setter or deleter need none. Functions nested in a function
  body are not read.

Usage::

    check_doc_comments.py --platform <p> [--files a b …] [--all]

``--files``: report the undocumented declarations in those files (the module
they belong to is read whole so Swift extensions fold correctly). ``--all``:
every product-source file under the current directory. Output: one
``FAIL doc-comments <path>:<line>:doc-comments: <Type.member (kind)> is public and has no doc comment [DOC-1]``
per offender, ``PASS doc-comments`` otherwise; exit 1 on any offender.
Stdlib only.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys

CHECK = "doc-comments"
HEAVY_DIRECTORIES = {".git", ".gradle", "node_modules", ".build", "intermediates", "Pods", ".idea",
                     "DerivedData", "caches", "tmp", ".venv", "__pycache__", "build", "dist"}
TYPE_LIKE = {"class", "struct", "enum", "actor", "protocol", "extension", "interface", "object", "namespace"}


class Declaration:
    __slots__ = ("kind", "name", "doc", "is_public", "members", "line", "file")

    def __init__(self, kind, name, doc="", is_public=False, line=0):
        self.kind = kind
        self.name = name
        self.doc = doc
        self.is_public = is_public
        self.members = []
        self.line = line
        self.file = None

    @property
    def is_type_like(self):
        return self.kind in TYPE_LIKE


# ---------------------------------------------------------------- the sanitizer (DocsGeneration.sanitize)


def sanitize(source, char_literals=False):
    """Ordinary comments and string contents removed; ``///`` lines and ``/** */`` blocks kept;
    every newline kept so line numbers survive (Coast's drops the newlines inside a
    multi-line string, which changes no declaration)."""
    chars = source
    n = len(chars)
    out = []
    i = 0

    def pound_run(position):
        count = 0
        while position + count < n and chars[position + count] == "#":
            count += 1
        return count

    while i < n:
        c = chars[i]
        if c == "/" and i + 1 < n and chars[i + 1] == "/":
            is_doc = i + 2 < n and chars[i + 2] == "/" and not (i + 3 < n and chars[i + 3] == "/")
            while i < n and chars[i] != "\n":
                if is_doc:
                    out.append(chars[i])
                i += 1
            continue
        if c == "/" and i + 1 < n and chars[i + 1] == "*":
            is_doc = (i + 2 < n and chars[i + 2] == "*" and not (i + 3 < n and chars[i + 3] == "*")
                      and not (i + 2 < n and chars[i + 2] == "/"))
            depth = 0
            while i < n:
                if chars[i] == "/" and i + 1 < n and chars[i + 1] == "*":
                    depth += 1
                    if is_doc:
                        out.append("/*")
                    i += 2
                    continue
                if chars[i] == "*" and i + 1 < n and chars[i + 1] == "/":
                    depth -= 1
                    if is_doc:
                        out.append("*/")
                    i += 2
                    if depth == 0:
                        break
                    continue
                if is_doc or chars[i] == "\n":
                    out.append(chars[i])
                i += 1
            if not is_doc:
                out.append(" ")
            continue
        if char_literals and c == "'":
            end = i + 1
            while end < n and chars[end] != "'" and chars[end] != "\n":
                end += 2 if chars[end] == "\\" else 1
            out.append("' '")
            i = min(end + 1, n)
            continue
        pounds = pound_run(i) if c == "#" else 0
        quote_at = i + pounds
        if quote_at < n and chars[quote_at] == '"' and (c == '"' or pounds > 0):
            triple = quote_at + 2 < n and chars[quote_at + 1] == '"' and chars[quote_at + 2] == '"'
            out.append('"')
            i = quote_at + (3 if triple else 1)
            interpolation = 0
            while i < n:
                s = chars[i]
                if interpolation > 0:
                    if s == "(":
                        interpolation += 1
                    if s == ")":
                        interpolation -= 1
                    i += 1
                    continue
                if s == "\\" and pound_run(i + 1) >= pounds:
                    escaped = i + 1 + pounds
                    if escaped < n and chars[escaped] == "(":
                        interpolation = 1
                        i = escaped + 1
                        continue
                    i = escaped + 1
                    continue
                if s == '"':
                    if triple:
                        if i + 2 < n and chars[i + 1] == '"' and chars[i + 2] == '"' and pound_run(i + 3) >= pounds:
                            i += 3 + pounds
                            break
                    elif pound_run(i + 1) >= pounds:
                        i += 1 + pounds
                        break
                if s == "\n":
                    out.append("\n")
                i += 1
            out.append('"')
            continue
        out.append(c)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------- the shared core (DeclarationScanning)


class ContainerStack:
    """The containers currently open, outermost first, each with the brace depth at which
    it opened and a per-language flag."""

    def __init__(self):
        self.open = []  # [declaration, depth_at_open, flag]
        self.top_level = []
        self.depth = 0

    @property
    def is_empty(self):
        return not self.open

    @property
    def last(self):
        return self.open[-1] if self.open else None

    @property
    def at_declaration_level(self):
        return self.depth == len(self.open)

    def push(self, declaration, depth_at_open, flag):
        self.open.append([declaration, depth_at_open, flag])

    def set_flag(self, flag):
        if self.open:
            self.open[-1][2] = flag

    def append(self, declaration):
        if not self.open:
            self.top_level.append(declaration)
        else:
            self.open[-1][0].members.append(declaration)

    def apply_braces(self, text):
        for character in text:
            if character == "{":
                self.depth += 1
            if character == "}":
                self.depth = max(0, self.depth - 1)
                self.close(self.depth)

    def close(self, new_depth):
        while self.open and new_depth <= self.open[-1][1]:
            declaration = self.open.pop()[0]
            self.append(declaration)

    def finish(self):
        self.close(0)
        return self.top_level


def block_doc_comment(lines, start):
    collected = []
    index = start
    while index < len(lines):
        text = lines[index].strip(" \t")
        closes = "*/" in text
        if text.startswith("/**"):
            text = text[3:]
        end = text.find("*/")
        if end >= 0:
            text = text[:end]
        text = text.strip(" \t")
        if text.startswith("*"):
            text = text[1:].strip(" \t")
        if text:
            collected.append(text)
        index += 1
        if closes:
            break
    return collected, index


def paren_balance(text):
    return text.count("(") - text.count(")")


def joined_declaration(lines, start):
    text = lines[start]
    nxt = start + 1
    while nxt < len(lines):
        trimmed = text.strip(" \t")
        next_trimmed = lines[nxt].strip(" \t")
        continues = (paren_balance(text) > 0 or trimmed.endswith(",") or trimmed.endswith(":")
                     or (trimmed.endswith("=") and not trimmed.endswith("==")) or trimmed.endswith("(")
                     or ("{" not in text and next_trimmed.startswith("{")))
        if not continues:
            break
        text += " " + next_trimmed
        nxt += 1
    return text, nxt


def leading_identifier(text):
    name = []
    for character in text:
        if character.isalnum() or character in "_`":
            name.append(character)
        else:
            break
    return "".join(name).replace("`", "")


def stripping_leading_annotations(line):
    text = line.strip(" \t")
    while text.startswith("@"):
        index = 1
        while index < len(text) and (text[index].isalnum() or text[index] in "_.:"):
            index += 1
        if index < len(text) and text[index] == "(":
            depth = 0
            while index < len(text):
                if text[index] == "(":
                    depth += 1
                if text[index] == ")":
                    depth -= 1
                    if depth == 0:
                        index += 1
                        break
                index += 1
        text = text[index:].lstrip()
    return text


def collapse(text):
    return " ".join(text.split())


# ---------------------------------------------------------------- Swift (DocsGeneration.declarations(inSwiftSource:))

SWIFT_KEYWORDS = {"class", "struct", "enum", "actor", "protocol", "extension", "func", "init", "subscript",
                  "var", "let", "case", "typealias", "associatedtype"}
SWIFT_MODIFIERS = {"public", "open", "internal", "fileprivate", "private", "package", "static", "final",
                   "override", "required", "convenience", "lazy", "weak", "unowned", "indirect", "mutating",
                   "nonmutating", "dynamic", "optional", "nonisolated", "isolated", "distributed", "borrowing",
                   "consuming", "prefix", "postfix", "infix", "async", "reasync"}


def swift_token_prefix(line):
    tokens = []
    current = ""
    for character in line:
        if character.isalnum() or character in "_@":
            current += character
        elif character in "()":
            current += character
        else:
            if current:
                tokens.append(current)
                current = ""
            if not character.isspace():
                tokens.append(character)
        if len(tokens) > 12:
            break
    if current:
        tokens.append(current)
    out = []
    for token in tokens:
        paren = token.find("(")
        if paren > 0:
            out.append(token[:paren])
            out.append(token[paren:])
        else:
            out.append(token)
    return out


def swift_signature_text(text):
    parens = 0
    for offset, character in enumerate(text):
        if character in "([":
            parens += 1
        if character in ")]":
            parens -= 1
        if character == "{" and parens == 0:
            return text[:offset]
    return text


def swift_name(kind, after_keyword):
    if kind == "init":
        return "init"
    if kind == "subscript":
        return "subscript"
    name = []
    for character in after_keyword:
        if character.isalnum() or character in "_`.":
            name.append(character)
        else:
            break
    return "".join(name).replace("`", "")


def swift_case_names(signature):
    at = signature.find("case ")
    if at < 0:
        return []
    names = []
    current = ""
    depth = 0
    for character in signature[at + 5:]:
        if character == "(":
            depth += 1
        if character == ")":
            depth -= 1
        if character == "," and depth == 0:
            names.append(current)
            current = ""
            continue
        current += character
    names.append(current)
    cleaned = []
    for entry in names:
        name = leading_identifier(entry.strip(" \t"))
        if name:
            cleaned.append(name)
    return cleaned


def swift_parse_declaration(lines, start):
    tokens = [t for t in swift_token_prefix(lines[start]) if not t.startswith("(")]
    declared_public = False
    keyword = None
    after_keyword = ""
    for position, token in enumerate(tokens):
        if token.startswith("@"):
            continue
        if token in SWIFT_MODIFIERS:
            if token in ("public", "open"):
                declared_public = True
            continue
        if token in SWIFT_KEYWORDS:
            keyword = token
            after_keyword = " ".join(tokens[position + 1:])
            break
        return None
    if keyword is None:
        return None
    text = lines[start]
    next_index = start + 1
    while paren_balance(text) > 0 and next_index < len(lines):
        text += " " + lines[next_index].strip(" \t")
        next_index += 1
    signature = collapse(swift_signature_text(text))
    name = swift_name(keyword, after_keyword)
    if not name:
        return None
    names = [name]
    if keyword == "case":
        listed = swift_case_names(signature)
        if len(listed) > 1:
            names = listed
    declarations = [Declaration(keyword, each, "", declared_public, start + 1) for each in names]
    return declarations, declared_public, next_index


def swift_inline_body_members(consumed, container):
    body_start = consumed.find("{")
    if body_start < 0:
        return []
    depth = 0
    body = []
    for character in consumed[body_start + 1:]:
        if character == "{":
            depth += 1
        if character == "}":
            if depth == 0:
                break
            depth -= 1
        body.append(character)
    members = swift_declarations_of_lines("".join(body).replace(";", "\n").split("\n"), container.line - 1)
    if container.kind == "enum" and container.is_public:
        for member in members:
            if member.kind == "case":
                member.is_public = True
    return members


def swift_declarations(source):
    return swift_declarations_of_lines(sanitize(source).split("\n"), 0)


def swift_declarations_of_lines(lines, line_offset):
    containers = ContainerStack()
    pending_doc = []
    index = 0
    while index < len(lines):
        line = lines[index]
        trimmed = line.strip(" \t")
        if not trimmed:
            pending_doc = []
            index += 1
            continue
        if trimmed.startswith("///") and not trimmed.startswith("////"):
            pending_doc.append(trimmed[3:].strip(" \t"))
            index += 1
            continue
        if trimmed.startswith("/**"):
            doc_lines, index = block_doc_comment(lines, index)
            pending_doc.extend(doc_lines)
            continue
        parsed = swift_parse_declaration(lines, index) if containers.at_declaration_level else None
        if parsed is not None:
            declarations, declared_public, next_index = parsed
            doc = "\n".join(pending_doc).strip()
            pending_doc = []
            implicitly_public = containers.last[2] if containers.last else False
            consumed = "\n".join(lines[index:next_index])
            depth_before = containers.depth
            new_depth = depth_before
            for character in consumed:
                if character == "{":
                    new_depth += 1
                if character == "}":
                    new_depth = max(0, new_depth - 1)
            for position, declaration in enumerate(declarations):
                declaration.doc = doc
                declaration.line = index + 1 + line_offset
                if implicitly_public:
                    declaration.is_public = True
                if declaration.is_type_like and new_depth > depth_before and position == 0:
                    members_public = ((declaration.kind == "protocol" and declaration.is_public)
                                      or (declaration.kind == "extension" and declared_public))
                    containers.push(declaration, depth_before, members_public)
                    continue
                if declaration.is_type_like and new_depth == depth_before:
                    declaration.members = swift_inline_body_members(consumed, declaration)
                if declaration.kind == "case" and containers.last and containers.last[0].kind == "enum" \
                        and containers.last[0].is_public:
                    declaration.is_public = True
                containers.append(declaration)
            containers.apply_braces("{" * max(0, new_depth - depth_before))
            if new_depth < depth_before:
                containers.apply_braces("}" * (depth_before - new_depth))
            index = next_index
            continue
        if not trimmed.startswith("@"):
            pending_doc = []
        containers.apply_braces(line)
        index += 1
    return containers.finish()


def fold(declarations):
    """Extensions merged into the type they extend when it is declared in the same module;
    an extension of a type from elsewhere stays, listed through its members."""
    result = []
    index_by_name = {}
    external = []
    for declaration in declarations:
        if declaration.kind == "extension":
            continue
        if declaration.is_type_like and declaration.name not in index_by_name:
            index_by_name[declaration.name] = len(result)
        result.append(declaration)
    for declaration in declarations:
        if declaration.kind != "extension":
            continue
        if declaration.name in index_by_name:
            result[index_by_name[declaration.name]].members.extend(declaration.members)
        elif declaration.members:
            external.append(declaration)
    return result + external


# ---------------------------------------------------------------- Kotlin / Java (KotlinJavaDeclarations)

KOTLIN_MODIFIERS = {"public", "private", "internal", "protected", "open", "abstract", "final", "sealed", "data",
                    "inner", "annotation", "value", "override", "suspend", "inline", "noinline", "crossinline",
                    "operator", "infix", "lateinit", "const", "tailrec", "external", "expect", "actual", "vararg",
                    "companion", "enum"}
KOTLIN_KEYWORDS = {"class": "class", "interface": "interface", "object": "object", "fun": "func", "val": "let",
                   "var": "var", "typealias": "typealias", "constructor": "init"}
KOTLIN_RESERVED = KOTLIN_MODIFIERS | set(KOTLIN_KEYWORDS) | {"init", "return", "if", "when", "for", "while", "get", "set"}
JAVA_MODIFIERS = {"public", "private", "protected", "static", "final", "abstract", "default", "synchronized",
                  "native", "transient", "volatile", "strictfp", "sealed", "non-sealed"}
JAVA_TYPE_KEYWORDS = {"class": "class", "interface": "interface", "enum": "enum", "record": "struct",
                      "@interface": "interface"}
JAVA_RESERVED = JAVA_MODIFIERS | set(JAVA_TYPE_KEYWORDS) | {"return", "if", "for", "while", "switch", "throw",
                                                            "try", "else", "do", "new", "this", "super"}


def declaration_head(text):
    parens = 0
    angle = 0
    previous = " "
    for offset, character in enumerate(text):
        if character in "([":
            parens += 1
        elif character in ")]":
            parens -= 1
        elif character == "<":
            angle += 1
        elif character == ">":
            if previous != "-" and angle > 0:
                angle -= 1
        elif character == "{" and parens == 0:
            return text[:offset]
        elif (character == "=" and parens == 0 and angle == 0 and previous not in "=!<>"
              and (offset + 1 >= len(text) or text[offset + 1] != "=")):
            return text[:offset]
        previous = character
    return text


def function_name(head):
    open_at = head.find("(")
    if open_at <= 0:
        return ""
    name = []
    index = open_at - 1
    while index >= 0:
        character = head[index]
        if character.isalnum() or character in "_`":
            name.insert(0, character)
        else:
            break
        index -= 1
    return "".join(name).replace("`", "")


class KotlinJavaScanner:
    def __init__(self, lines, language, container=None, line_offset=0):
        self.lines = lines
        self.language = language
        self.line_offset = line_offset
        self.containers = ContainerStack()
        self.pending_doc = []
        if container is not None:
            self.containers.push(container, -1, container.kind == "enum")
            self.containers.apply_braces("{")

    @property
    def reserved(self):
        return KOTLIN_RESERVED if self.language == "kotlin" else JAVA_RESERVED

    def run(self):
        lines = self.lines
        index = 0
        while index < len(lines):
            trimmed = lines[index].strip(" \t")
            if not trimmed:
                self.pending_doc = []
                index += 1
                continue
            if trimmed.startswith("/**"):
                doc_lines, index = block_doc_comment(lines, index)
                self.pending_doc.extend(doc_lines)
                continue
            if trimmed.startswith("///"):
                self.pending_doc.append(trimmed[3:].strip(" \t"))
                index += 1
                continue
            if self.containers.is_empty and (trimmed.startswith("package ") or trimmed.startswith("import ")):
                index += 1
                continue
            line = trimmed if trimmed.startswith("@interface") else stripping_leading_annotations(trimmed)
            if not line:
                self.containers.apply_braces(lines[index])
                index += 1
                continue
            entry = self.enum_entry(line) if self.containers.at_declaration_level else None
            if entry is not None:
                doc = "\n".join(self.pending_doc).strip()
                self.pending_doc = []
                declaration = Declaration("case", entry, doc, self.containers.last[0].is_public if self.containers.last else False,
                                          index + 1 + self.line_offset)
                self.containers.append(declaration)
                if ";" in line:
                    self.containers.set_flag(False)
                self.containers.apply_braces(lines[index])
                index += 1
                continue
            parsed = self.parse_declaration(line, index) if self.containers.at_declaration_level else None
            if parsed is not None:
                declaration, text, next_index = parsed
                declaration.doc = "\n".join(self.pending_doc).strip()
                declaration.line = index + 1 + self.line_offset
                self.pending_doc = []
                depth_before = self.containers.depth
                self.containers.set_flag(False)
                self.containers.apply_braces(text)
                if declaration.is_type_like and self.containers.depth > depth_before:
                    self.containers.push(declaration, depth_before, declaration.kind == "enum")
                else:
                    if declaration.is_type_like:
                        body = self.inline_body(text)
                        if body is not None:
                            declaration.members = self.inline_members(body, declaration)
                    self.containers.append(declaration)
                index = next_index
                continue
            if self.containers.at_declaration_level and ";" in line:
                self.containers.set_flag(False)
            self.pending_doc = []
            self.containers.apply_braces(lines[index])
            index += 1
        return self.containers.finish()

    @staticmethod
    def inline_body(text):
        parens = 0
        depth = 0
        body = []
        opened = False
        for character in text:
            if not opened:
                if character == "(":
                    parens += 1
                elif character == ")":
                    parens -= 1
                elif character == "{" and parens == 0:
                    opened = True
                continue
            if character == "{":
                depth += 1
            if character == "}":
                if depth == 0:
                    return "".join(body)
                depth -= 1
            body.append(character)
        return None

    def inline_members(self, body, container):
        text = []
        parens = 0
        for character in body:
            if character == "(":
                parens += 1
            elif character == ")":
                parens -= 1
            if character == ";" or (character == "," and container.kind == "enum" and parens == 0):
                text.append("\n")
            else:
                text.append(character)
        scanner = KotlinJavaScanner("".join(text).split("\n"), self.language, container, container.line - 1)
        scanner.run()
        return scanner.containers.last[0].members if scanner.containers.last else []

    def enum_entry(self, line):
        container = self.containers.last
        if container is None or not container[2]:
            return None
        name = leading_identifier(line)
        if not name or not (name[0].isalpha() or name[0] == "_") or name in self.reserved:
            return None
        rest = line[len(name):].strip(" \t")
        if rest and rest[0] not in ",;({":
            return None
        return name

    def joined(self, line, start):
        patched = list(self.lines)
        patched[start] = line
        return joined_declaration(patched, start)

    def parse_declaration(self, line, start):
        return self.parse_kotlin(line, start) if self.language == "kotlin" else self.parse_java(line, start)

    def parse_kotlin(self, line, start):
        tokens = line.split()
        is_public = True
        keyword = None
        modifiers = []
        after_keyword = []
        for position, token in enumerate(tokens):
            if token in KOTLIN_MODIFIERS:
                if token in ("private", "internal", "protected"):
                    is_public = False
                modifiers.append(token)
                continue
            word = leading_identifier(token)
            if word in KOTLIN_KEYWORDS and (token == word or token.startswith(word + "(")):
                keyword = word
                after_keyword = list(tokens[position + 1:])
                if token != word:
                    after_keyword.insert(0, token[len(word):])
                break
            return None
        if keyword is None:
            return None
        kind = KOTLIN_KEYWORDS[keyword]
        if keyword == "class" and "enum" in modifiers:
            kind = "enum"
        if keyword == "class" and "annotation" in modifiers:
            kind = "interface"
        text, nxt = self.joined(line, start)
        head = collapse(declaration_head(text))
        if kind == "init":
            name = "constructor"
        elif kind == "object" and "companion" in modifiers and (not after_keyword or not leading_identifier(after_keyword[0])):
            name = "Companion"
        elif kind == "func":
            name = function_name(head)
        else:
            name = leading_identifier(after_keyword[0] if after_keyword else "")
        if not name:
            return None
        if self.containers.last and not self.containers.last[0].is_public:
            is_public = False
        return Declaration(kind, name, "", is_public), text, nxt

    def parse_java(self, line, start):
        tokens = line.split()
        is_public = False
        is_final = False
        rest = []
        type_kind = None
        for position, token in enumerate(tokens):
            if token in JAVA_MODIFIERS:
                if token == "public":
                    is_public = True
                if token == "final":
                    is_final = True
                continue
            if token in JAVA_TYPE_KEYWORDS:
                type_kind = JAVA_TYPE_KEYWORDS[token]
                rest = list(tokens[position + 1:])
            else:
                rest = list(tokens[position:])
            break
        container = self.containers.last[0] if self.containers.last else None
        if container is not None:
            if container.kind == "interface":
                is_public = True
            if not container.is_public:
                is_public = False
        text, nxt = self.joined(line, start)
        head = collapse(declaration_head(text))
        if type_kind is not None:
            name = leading_identifier(rest[0] if rest else "")
            if not name:
                return None
            return Declaration(type_kind, name, "", is_public), text, nxt
        if container is None or not rest:
            return None
        first = rest[0]
        if not (first[0].isalpha() or first[0] in "_<") or first in self.reserved:
            return None
        if "(" in head:
            name = function_name(head)
            if not name:
                return None
            kind = "init" if name == container.name else "func"
            return Declaration(kind, name, "", is_public), text, nxt
        if not (head.endswith(";") or ";" in text):
            return None
        field_head = head.split("=")[0]
        words = field_head.strip(" ;").split()
        if len(words) < 2:
            return None
        name = words[-1]
        if not (name[0].isalpha() or name[0] == "_"):
            return None
        return Declaration("let" if is_final else "var", name, "", is_public), text, nxt


def kotlin_java_declarations(source, language):
    return KotlinJavaScanner(sanitize(source, char_literals=True).split("\n"), language).run()


# ---------------------------------------------------------------- TypeScript / JavaScript

TS_EXPORT = re.compile(r"^\s*export\s+(?:default\s+)?(?:declare\s+)?(?:abstract\s+)?(class|interface|type|enum|function|async function|const|let|var|namespace)\s+([A-Za-z_$][\w$]*)")
TS_EXPORT_ANON = re.compile(r"^\s*export\s+default\s+(?:async\s+)?(function|class)\b")
TS_MEMBER = re.compile(r"^\s*(?:(?:public|static|readonly|async|override|abstract|get|set|declare)\s+)*([A-Za-z_$][\w$]*)\s*(?:\(|:|=|<|\?)")
TS_SKIP_MEMBER = re.compile(r"^\s*(private|protected|#|constructor\b|static\s*\{|if\b|for\b|while\b|return\b|switch\b|case\b|default:|super\b|this\b)")
JS_IDENTIFIER_CHARS = "_$"


def sanitize_js(source):
    """The JavaScript-aware sanitizer: ordinary comments removed (a ``//`` comment keeps its
    two slashes so its line is not blank), ``/** */`` blocks kept, the contents of ``'…'``,
    ``"…"`` and ```…``` strings removed. A template's ``${…}`` interpolations are read as
    code, so braces inside them still count and a template nested in one is read too. A
    quote directly after an identifier character (``Don't`` in JSX text) opens no string.
    Every newline kept so line numbers survive. Regex literals are not read: a ``/…/`` holding
    a quote is this sanitizer's one blind spot."""
    n = len(source)
    out = []
    i = 0
    frames = []  # ["tpl"] inside a template; ["code", depth] inside a ${ } interpolation

    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if frames and frames[-1][0] == "tpl":
            if c == "\\":
                i += 2
                continue
            if c == "`":
                frames.pop()
                out.append("`")
                i += 1
                continue
            if c == "$" and nxt == "{":
                frames.append(["code", 0])
                out.append("${")
                i += 2
                continue
            if c == "\n":
                out.append("\n")
            i += 1
            continue
        if c == "/" and nxt == "/":
            out.append("//")
            i += 2
            while i < n and source[i] != "\n":
                i += 1
            continue
        if c == "/" and nxt == "*":
            is_doc = i + 2 < n and source[i + 2] == "*" and not (i + 3 < n and source[i + 3] in "*/")
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
            chunk = source[i:end]
            out.append(chunk if is_doc else " " + "\n" * chunk.count("\n"))
            i = end
            continue
        if c in "'\"" and not (i > 0 and (source[i - 1].isalnum() or source[i - 1] in JS_IDENTIFIER_CHARS)):
            out.append(c)
            i += 1
            while i < n and source[i] != c and source[i] != "\n":
                i += 2 if source[i] == "\\" else 1
            if i < n and source[i] == c:
                i += 1
            out.append(c)
            continue
        if c == "`":
            frames.append(["tpl"])
            out.append("`")
            i += 1
            continue
        if frames:
            if c == "{":
                frames[-1][1] += 1
            elif c == "}":
                if frames[-1][1] == 0:
                    frames.pop()
                    out.append("}")
                    i += 1
                    continue
                frames[-1][1] -= 1
        out.append(c)
        i += 1
    return "".join(out)


def bracket_balance(text):
    return sum(text.count(o) - text.count(c) for o, c in ("()", "{}", "[]"))


def joined_decorator(lines, start):
    """The decorator starting at ``lines[start]`` joined until its brackets balance:
    ``@Component({`` … ``})`` is one unit. Returns (text, next_index)."""
    text = lines[start]
    nxt = start + 1
    while bracket_balance(text) > 0 and nxt < len(lines):
        text += " " + lines[nxt].strip(" \t")
        nxt += 1
    return text, nxt


def ts_declarations(source):
    """Exported top-level declarations and the non-private members of exported classes
    and interfaces. A doc is a ``/** */`` directly above: decorators and ``//`` comments
    may sit between, a blank line may not."""
    lines = sanitize_js(source).split("\n")
    out = []
    pending = False
    depth = 0
    container = None
    container_depth = 0

    def count_braces(text):
        nonlocal depth, container
        for character in text:
            if character == "{":
                depth += 1
            if character == "}":
                depth -= 1
                if container is not None and depth < container_depth:
                    container = None

    index = 0
    while index < len(lines):
        line = lines[index]
        trimmed = line.strip(" \t")
        next_index = index + 1
        if trimmed.startswith("/**"):
            _, index = block_doc_comment(lines, index)
            pending = True
            continue
        if not trimmed:
            pending = False
            index += 1
            continue
        if trimmed == "//":
            index += 1
            continue
        if trimmed.startswith("@"):
            text, next_index = joined_decorator(lines, index)
            line = stripping_leading_annotations(text)
            count_braces(text[:len(text) - len(line)])
            if not line:
                index = next_index
                continue
        if container is not None and depth == container_depth and not TS_SKIP_MEMBER.match(line):
            match = TS_MEMBER.match(line)
            if match and match.group(1) not in ("import", "export", "return", "const", "let", "var", "new", "throw"):
                member = Declaration("func" if "(" in line.split("=")[0] else "var", match.group(1), "doc" if pending else "",
                                     True, index + 1)
                container.members.append(member)
        match = TS_EXPORT.match(line) if depth == 0 else None
        if match:
            kind = match.group(1).replace("async ", "")
            declaration = Declaration(kind, match.group(2), "doc" if pending else "", True, index + 1)
            out.append(declaration)
            if kind in ("class", "interface", "namespace") and "{" in line:
                container = declaration
                container_depth = depth + 1
        elif depth == 0 and TS_EXPORT_ANON.match(line):
            out.append(Declaration(TS_EXPORT_ANON.match(line).group(1), "default", "doc" if pending else "", True, index + 1))
        pending = False
        count_braces(line)
        index = next_index
    return out


# ---------------------------------------------------------------- Python (the stdlib ast module)

PY_IMPLIED_DOC = {"overload", "setter", "deleter"}  # an @overload signature, a property's setter or deleter
PY_TRANSPARENT = tuple(getattr(ast, name) for name in ("If", "Try", "TryStar", "With", "AsyncWith") if hasattr(ast, name))


def python_public(name):
    return not name.startswith("_") or name == "__init__"


def python_decorator_names(node):
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, ast.Attribute):
            yield target.attr


def python_members(body):
    out = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            documented = bool((ast.get_docstring(node) or "").strip())
            implied = bool(set(python_decorator_names(node)) & PY_IMPLIED_DOC)
            kind = "class" if isinstance(node, ast.ClassDef) else "func"
            declaration = Declaration(kind, node.name, "doc" if documented or implied else "", python_public(node.name), node.lineno)
            if kind == "class":
                declaration.members = python_members(node.body)
            out.append(declaration)
        elif isinstance(node, PY_TRANSPARENT):
            for field in ("body", "orelse", "finalbody"):
                out.extend(python_members(getattr(node, field, None) or []))
            for handler in getattr(node, "handlers", None) or []:
                out.extend(python_members(handler.body))
    return out


def python_declarations(source):
    """Module-level ``def``/``class`` (inside ``if``/``try``/``with`` too) whose name does not
    start with ``_``, and inside a public class its public methods, ``__init__`` and nested
    public classes. A doc is a docstring as the first statement; an ``@overload`` signature and
    a property's ``@x.setter``/``@x.deleter`` carry their doc on the implementation and the
    getter. Functions nested in a function body are not read. A file Python cannot parse
    reports nothing: that is the interpreter's refusal, not this check's."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    return python_members(tree.body)


# ---------------------------------------------------------------- the verdict (DocsGeneration.collectUndocumented)


def collect_undocumented(declaration, path, out, language):
    here = f"{path}.{declaration.name}" if path else declaration.name
    doc_required = declaration.kind not in ("case", "associatedtype", "extension")
    if declaration.is_public and doc_required and not declaration.doc:
        out.append((declaration.line, declaration.file, f"{here} ({declaration.kind})"))
    if not (declaration.is_public or declaration.kind == "extension"):
        return
    for member in declaration.members:
        if language in ("kotlin", "java", "typescript", "python") and not member.is_public:
            continue
        collect_undocumented(member, here, out, language)


LANGUAGES = {".swift": "swift", ".kt": "kotlin", ".java": "java", ".ts": "typescript", ".tsx": "typescript",
             ".js": "typescript", ".jsx": "typescript", ".py": "python"}
PLATFORM_LANGUAGES = {"ios": {"swift"}, "macos": {"swift"}, "android": {"kotlin", "java"},
                      "react-native": {"typescript"}, "web": {"typescript"}, "python": {"python"}}


def platform_for(path):
    """The platform whose scanners read this file when the caller named none — by language."""
    return {"swift": "ios", "kotlin": "android", "java": "android", "typescript": "web", "python": "python"}.get(language_of(path) or "", "ios")


def language_of(path):
    name = os.path.basename(path)
    for extension, language in LANGUAGES.items():
        if name.endswith(extension):
            if language == "typescript" and (name.endswith(".d.ts") or any(part in name for part in (".test.", ".spec.", ".stories."))):
                return None
            return language
    return None


def is_product_source(path):
    parts = path.split("/")
    if any(part in HEAVY_DIRECTORIES for part in parts[:-1]):
        return False
    lowered = [part.lower() for part in parts]
    if any(part in ("tests", "test", "__tests__", "__mocks__", "androidtest", "e2e", "spec") for part in lowered[:-1]):
        return False
    name = parts[-1]
    if name == "Package.swift" or name.startswith("Package@swift"):
        return False  # a manifest, not product source
    return not (name.endswith("Tests.swift") or name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py")


def swift_module_of(path):
    """(root, recursive) — the module a Swift file belongs to under the SwiftPM layouts Coast
    walks, read whole; otherwise the file's own directory, that directory only (so an
    extension of a type in the same folder still folds, and nothing below is swallowed)."""
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "Sources":
        return "Sources/" + parts[1], True
    if len(parts) >= 4 and parts[0] == "Modules" and parts[2] == "Sources":
        return "Modules/" + parts[1] + "/Sources", True
    return os.path.dirname(path) or ".", False


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def stamp(declaration, path):
    declaration.file = path
    for member in declaration.members:
        stamp(member, path)


def undocumented(files, platform, texts=None):
    """[(path, line, entry)] for the files given (the caller chose them — the path classes
    decide what is product source), the Swift ones read with the rest of their module so
    extensions fold the way Coast's module scan folds them. ``texts`` supplies a file's
    content in place of the disk copy (an editor buffer, a staged version, a plant)."""
    texts = texts or {}
    languages = PLATFORM_LANGUAGES.get(platform, set(LANGUAGES.values()))
    wanted = {os.path.normpath(f) for f in files}
    results = []
    swift_modules = {}

    def text_of(path):
        return texts[path] if path in texts else read(path)

    for path in sorted(wanted):
        language = language_of(path)
        if language is None or language not in languages or (path not in texts and not os.path.isfile(path)):
            continue
        if language == "swift":
            swift_modules.setdefault(swift_module_of(path), set()).add(path)
            continue
        if language in ("kotlin", "java"):
            declarations = kotlin_java_declarations(text_of(path), language)
        elif language == "typescript":
            declarations = ts_declarations(text_of(path))
        else:
            declarations = python_declarations(text_of(path))
        found = []
        for declaration in declarations:
            stamp(declaration, path)
            collect_undocumented(declaration, "", found, language)
        results.extend((path, line, entry) for line, _, entry in found)
    for (module, recursive), own in swift_modules.items():
        module_files = set(own)
        if os.path.isdir(module):
            for root, dirs, names in os.walk(module):
                dirs[:] = [d for d in dirs if d not in HEAVY_DIRECTORIES] if recursive else []
                for name in names:
                    candidate = os.path.normpath(os.path.join(root, name))
                    if name.endswith(".swift") and is_product_source(candidate):
                        module_files.add(candidate)
        declarations = []
        for path in sorted(module_files):
            for declaration in swift_declarations(text_of(path)):
                stamp(declaration, path)
                declarations.append(declaration)
        found = []
        for declaration in fold(declarations):
            collect_undocumented(declaration, "", found, "swift")
        results.extend((file, line, entry) for line, file, entry in found if file in wanted)
    return sorted(results)


def tree_files():
    files = []
    for root, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in HEAVY_DIRECTORIES and not d.startswith(".")]
        for name in names:
            path = os.path.normpath(os.path.join(root, name))
            if language_of(path) and is_product_source(path):
                files.append(path)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Every public declaration carries a doc comment.")
    parser.add_argument("--platform", default=os.environ.get("COAST_PLATFORM") or None)
    parser.add_argument("--files", nargs="+")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--rule", default="DOC-1", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if bool(args.files) == bool(args.all):
        parser.print_usage()
        print("check_doc_comments.py: give exactly one of --files … or --all")
        return 2
    files = [f for f in args.files if is_product_source(f)] if args.files else tree_files()
    rule = "STYLE-4" if args.platform == "python" else args.rule
    offenders = undocumented(files, args.platform)
    for path, line, entry in offenders:
        print(f"FAIL {CHECK} {path}:{line}:{CHECK}: {entry} is public and has no doc comment [{rule}]")
    if offenders:
        print(f"FAIL {CHECK}: {len(offenders)} public declaration(s) missing a doc comment — the generated API reference has nothing to render for them")
        return 1
    print(f"PASS {CHECK} — every public declaration carries a doc comment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
