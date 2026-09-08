#!/usr/bin/env python3
"""The project's config — the one loader of ``<state_dir>/config.json``
(enforcement/README.md task E5.3), used by the scanner, the verifier, the
session hook, the installer and the git hooks (they evaluate ``config.py --sh``,
the switches rendered as shell variables, on every run).

The shape is ``config.default.json`` beside this file::

    {"version": 1,
     "owner": {"name": "", "product": "", "org": ""},
     "rules": {"off": [ids], "severity": {id: "block"|"ratchet"|"advisory"}, "retired_words": [...]},
     "seats": {"off": [names]},
     "session_hooks": {"off": [ids]},
     "linters": {"off": [names]},
     "ratchet_days": 90,
     "layout": {...overrides of layout.json's keys...}}

``load(root)`` merges the project's file over the defaults (a key the project
leaves out keeps its default; a list the project gives replaces the default
list) and validates it: a severity that would RAISE a signature is refused
with ``ConfigError`` and a sentence, because raising is the table's job.
``apply_to_signatures`` drops the signatures switched off, lowers the ones
whose severity the config lowered, and adds the retired words to the
``retired-wording`` signature. ``is_off(group, name)`` answers for a seat, a
linter or a session hook. The file is GOVERNING: the session hooks refuse an
agent editing it, so a switch is always a person's.

Stdlib only; shipped into the project's checks directory with the scanner.
"""

from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULTS_FILE = os.path.join(HERE, "config.default.json")
FILE_NAME = "config.json"
GROUPS = ("rules", "seats", "session_hooks", "linters")
SEVERITY_RANK = {"block": 2, "ratchet": 1, "advisory": 0}
SEATS = ("build", "tests", "lint", "format", "rules-scan", "doc-comments", "jscpd", "gh-ruleset")
RETIRED_WORDING_ID = "retired-wording"


class ConfigError(ValueError):
    """The config says something the layer refuses; the message is the sentence."""


def defaults():
    with open(DEFAULTS_FILE, encoding="utf-8") as handle:
        table = json.load(handle)
    table.pop("_comment", None)
    return table


def _merge(base, own):
    merged = dict(base)
    for key, value in own.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def config_path(root=None, state_dir=None):
    """Where the project's config lives; the state dir comes from the layout table unless given."""
    if state_dir is None:
        import layout as _layout
        state_dir = _layout.state_dir_anchor()
    return os.path.join(root or ".", state_dir, FILE_NAME)


def validate(table, source="config.json"):
    """The sentences the layer refuses the config with, as ConfigError; nothing on a sound file."""
    for name in GROUPS:
        group = table.get(name)
        if not isinstance(group, dict):
            raise ConfigError(f"{source}: '{name}' must be an object with an 'off' list")
        off = group.get("off", [])
        if not isinstance(off, list) or not all(isinstance(item, str) for item in off):
            raise ConfigError(f"{source}: '{name}.off' must be a list of names")
        group["off"] = off
    severity = table["rules"].get("severity") or {}
    if not isinstance(severity, dict):
        raise ConfigError(f"{source}: 'rules.severity' must be an object of id: block|ratchet|advisory")
    for signature_id, level in severity.items():
        if level not in SEVERITY_RANK:
            raise ConfigError(f"{source}: rules.severity.{signature_id} is '{level}' — one of block, ratchet, advisory")
    table["rules"]["severity"] = severity
    words = table["rules"].get("retired_words") or []
    if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
        raise ConfigError(f"{source}: 'rules.retired_words' must be a list of words")
    table["rules"]["retired_words"] = words
    days = table.get("ratchet_days", 90)
    if not isinstance(days, int) or isinstance(days, bool) or days < 1:
        raise ConfigError(f"{source}: 'ratchet_days' must be a whole number of days (the default is 90)")
    layout = table.get("layout")
    if layout is None:
        table["layout"] = {}
    elif not isinstance(layout, dict):
        raise ConfigError(f"{source}: 'layout' must be an object of layout keys")
    elif "state_dir" in layout:
        raise ConfigError(f"{source}: layout.state_dir cannot move — the hooks find this file by it")
    owner = table.get("owner")
    if not isinstance(owner, dict):
        raise ConfigError(f"{source}: 'owner' must be an object with name, product and org")
    for key in ("name", "product", "org"):
        owner.setdefault(key, "")
    return table


def load(root=None, path=None):
    """The project's config merged over the defaults and validated. ``path`` names the file
    outright (the verifier's ``--config``); otherwise it is ``<root>/<state_dir>/config.json``.
    A missing file is the defaults; a broken one is refused."""
    table = defaults()
    file_path = path or config_path(root)
    if os.path.isfile(file_path):
        try:
            with open(file_path, encoding="utf-8") as handle:
                own = json.load(handle)
        except ValueError as error:
            raise ConfigError(f"{file_path} is not JSON ({error}) — fix it or delete it and run adopt.py again")
        if not isinstance(own, dict):
            raise ConfigError(f"{file_path} must hold one JSON object")
        own.pop("_comment", None)
        table = _merge(table, own)
    return validate(table, file_path)


def is_off(table, group, name):
    """True when the config switches ``name`` off in ``group`` (rules, seats, linters, session_hooks)."""
    return name in ((table.get(group) or {}).get("off") or [])


def off_rules(table):
    return set(table["rules"]["off"])


def effective_severity(table, signature):
    """The signature's severity under the config: the table's, or the lower one the config asks for.
    A config that asks for a HIGHER one is refused — the table raises, the config only lowers."""
    wanted = table["rules"]["severity"].get(signature["id"])
    own = signature.get("severity", "block")
    if wanted is None:
        return own
    if SEVERITY_RANK[wanted] > SEVERITY_RANK.get(own, 2):
        raise ConfigError(f"rules.severity.{signature['id']} asks for '{wanted}' above the table's '{own}' — a config "
                          "may only lower a severity (block, ratchet, advisory); raising one is the signature table's job")
    return wanted


def apply_to_signatures(table, signatures):
    """One platform's signature list under the config: the ``off`` ids dropped, the lowered severities
    applied, the retired words added to the retired-wording pattern. The table's own lists are untouched."""
    off = off_rules(table)
    words = table["rules"]["retired_words"]
    out = []
    for signature in signatures:
        if signature.get("id") in off or signature.get("group") in off:
            continue
        adjusted = dict(signature)
        adjusted["severity"] = effective_severity(table, signature)
        if signature.get("id") == RETIRED_WORDING_ID and words and adjusted.get("pattern"):
            # the table's pattern opens with a global flag group ("(?i)…"), which Python only accepts at the
            # very start: the flags move to the front of the joined pattern and the rest is grouped
            flags = re.match(r"\(\?[aiLmsux]+\)", adjusted["pattern"])
            head, rest = (flags.group(0), adjusted["pattern"][flags.end():]) if flags else ("(?i)", adjusted["pattern"])
            extra = "|".join(r"\b" + re.escape(word) + r"\b" for word in words)
            adjusted["pattern"] = f"{head}(?:{rest})|(?:{extra})"
        out.append(adjusted)
    return out


def to_sh(table):
    """The switches a ``sh`` hook honours, one line each: ``config_seats_off``, ``config_linters_off``,
    ``config_session_hooks_off`` as space-separated word lists. A hook evaluates ``config.py --sh`` so
    an edit to the file counts on the next run, with no re-install."""
    import shlex
    lines = []
    for group, variable in (("seats", "seats_off"), ("linters", "linters_off"), ("session_hooks", "session_hooks_off")):
        names = (table.get(group) or {}).get("off") or []
        lines.append(f"config_{variable}={shlex.quote(' '.join(names))}")
    return "\n".join(lines) + "\n"


def dump(table):
    """The file as adopt.py writes it: the defaults' key order, two-space indent, a trailing newline."""
    ordered = {key: table[key] for key in defaults() if key in table}
    ordered.update({key: value for key, value in table.items() if key not in ordered})
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    import sys
    try:
        if "--sh" in sys.argv:
            print(to_sh(load()), end="")
        else:
            print(dump(load(sys.argv[1] if len(sys.argv) > 1 else None)), end="")
    except ConfigError as error:
        print(f"FAIL config {error}", file=sys.stderr)
        sys.exit(1)
