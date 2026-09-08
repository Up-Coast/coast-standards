#!/usr/bin/env python3
"""verify_rules.py — rule document ↔ battery parity (enforcement task E0.1).

Every rule in this repo's documents must name the check that holds it, and
that check must actually exist in the platform's gate battery. This script
is the test for that claim. It parses every rule, reads each rule's
``[… check: …]`` tag, resolves every reference against ``battery.json`` (the
manifest of what each platform's battery runs) and the files the manifest
points at, and prints the honest number per document:
"enforced by a check: N of M". Design: ``enforcement/README.md`` §4.1.

What counts as a rule (one convention for every document):

* a column-0 bullet that opens in bold, ``- **…**``. Its id is the leading
  ``PREFIX-n`` inside the bold when there is one (``- **L-1 — …**``,
  ``- **SEC-4** …``); otherwise the rule is anonymous and named by a slug of
  its bold title until E0.2 gives it an id. Indented lines that follow are
  the rule's text; a blank line or an unindented line ends it.
* a leaf section (a heading with no bullet rules and no child headings)
  whose body is prose — the numbered files state many rules that way
  (00 §2d, 10 "Run atomic commands"). The tag goes anywhere in the section's
  prose; the last ``[… check: …]`` bracket wins.
* Not rules: the document's H1, and any section titled "Sources".

The tag grammar — the last square bracket in the rule that contains
``check:``; references separated by commas, every one must resolve::

    [Coast D36; check: scan:ui-string-literal]
    [Swift practice; check: swiftlint:force_unwrapping, swiftlint:force_try]
    [SRP; check: advisory:type-size, review]

    scan:<id>       a scanner signature, severity block   (machine)
    ratchet:<id>    a scanner signature, severity ratchet (machine)
    advisory:<id>   a scanner signature that never fails  (advisory)
    <linter>:<rule> a rule the shipped linter config enables, e.g.
                    swiftlint:force_unwrapping, eslint:react-hooks/rules-of-hooks,
                    detekt:UnsafeCallOnNullableType, androidlint:HardcodedText,
                    tsc:strict, ruff:E501, mypy:strict      (machine)
    <linter>        the linter as a whole, e.g. prettier, ktlint (machine)
    tool:<name>     a tool the battery runs, e.g. tool:jscpd (machine)
    session:<id>    a Claude Code or git hook, e.g. session:chained-cd (machine)
    review          only a mind can judge it — a per-rule review row
    process         held by the pipeline or by a person, named as such
    context         this bullet explains a rule and is not one; not counted

How a reference resolves (all of it is files on disk — no network, no model):

* ``scan``/``ratchet``/``advisory``: the manifest's scanner script exists and
  the signatures file lists the id under EVERY platform the document applies
  to, with the same severity the tag claims.
* ``<linter>:<rule>``: every applicable platform's battery lists that linter,
  its config file exists, and the config names the rule enabled. The script
  reads the config formats it knows (SwiftLint YAML, detekt YAML, ESLint flat
  config, Android ``lint.xml``, ``tsconfig``, ``mypy.ini``, ``ruff.toml``) and
  falls back to a whole-word search. It does NOT know any linter's default
  rule set and does not pretend to: a config must name the rule a document
  cites, or the rule is not held.
* ``tool:<name>``: every applicable platform's manifest entry for the tool
  names a runner file that exists and mentions the tool.
* ``session:<id>``: the manifest's session-hook files mention the id.
* ``review``, ``process``, ``context``: always resolve.

Bins per rule: ``machine`` when every reference is a machine check; ``partly``
when a machine check and a review/process/advisory reference share the rule;
``advisory``; ``review``; ``process``. A rule with any gap — no tag, an unknown
reference, an unresolved reference — is ``open``. "Enforced by a check" counts
only the ``machine`` bin; the number is honest or it is nothing.

The project's config (``--config <file>``, default the project's own
``config.json`` in its state dir; task E5.4) can switch a check off, and the
verifier tells the truth about that: a rule whose every machine reference is
switched off is ``off``, not ``machine``; a rule with one of several references
off is ``partly``. The headline says how many: "enforced by a check 21 of 74
(3 switched off)". A signature id in ``rules.off``, a linter in
``linters.off``, a tool whose seat is in ``seats.off`` (``tool:jscpd`` and
``tool:gh-ruleset`` are their own seats, ``tool:warnings-as-errors`` is the
build seat) or a hook id in ``session_hooks.off`` is off.

Also a gap: a signature in the signatures file that no rule names.

Output: one summary line per document, then ``FAIL verify-rules
<path>:<line>:<id>: <words>`` per gap (the line format the battery, the hooks
and Coast parse), then the totals. Exit 1 on any gap.

Ratchet mode (this repo's own hook, decision 2 of the design):
``--baseline <file>`` reads ``{"id", "count", "deadline", …}`` and passes only
while the gap count EQUALS the baseline. A rise is a regression; a fall must
lower the baseline in the same commit (the message says the new number);
past the deadline any gap fails. Nothing here can raise the baseline.

Usage::

    verify_rules.py                          # the whole corpus, from the repo root
    verify_rules.py --summary                # per-document lines and totals only
    verify_rules.py --baseline enforcement/checks/verify-baseline.json
    verify_rules.py --document docs/domain-rules.md --platform ios   # one project's copy
    verify_rules.py --json                   # machine-readable, for Coast's Rules tab
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from check_rules import flatten_signatures  # noqa: E402 — the one reader of the signature file (E5.2)
import config as _config  # noqa: E402 — the one loader of a project's config (E5.3)

CHECK_NAME = "verify-rules"
SKIPPED_SECTION_TITLES = {"sources"}
MACHINE_KINDS = {"scan", "linter", "tool", "session"}
PLAIN_KINDS = {"review", "process", "context"}
SIGNATURE_SEVERITIES = {"scan": "block", "ratchet": "ratchet", "advisory": "advisory"}

ID_RE = re.compile(r"^- \*\*([A-Z][A-Z0-9]*-\d+)\b")
BOLD_BULLET_RE = re.compile(r"^- \*\*")
BOLD_TITLE_RE = re.compile(r"^- \*\*(.+?)\*\*")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BRACKET_RE = re.compile(r"\[([^\[\]]*)\]")
CHECK_RE = re.compile(r"\bcheck:\s*(.*)\Z", re.DOTALL)


# ---------------------------------------------------------------- parsing


@dataclass
class Rule:
    """One rule as the documents state it."""

    path: str
    line: int
    id: str
    title: str
    text: str
    kind: str  # "bullet" or "prose"
    refs: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    category: str = "open"

    @property
    def tag_text(self):
        """The reference list inside the rule's check tag, or None when untagged."""
        brackets = BRACKET_RE.findall(self.text)
        for inner in reversed(brackets):
            match = CHECK_RE.search(inner)
            if match:
                return match.group(1).strip()
        return None


@dataclass
class Section:
    level: int
    title: str
    line: int
    bullet_rules: list = field(default_factory=list)
    prose: list = field(default_factory=list)  # (line number, line)
    has_children: bool = False


def slug(title):
    """A stable, parser-safe name for a rule that has no id yet."""
    words = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return words[:48].rstrip("-") or "untitled"


def _join(lines):
    return " ".join(line.strip() for line in lines).strip()


def parse_document(text, path):
    """Every rule in one document, in order."""
    sections = []
    section = None
    open_bullet = None  # (start line, [lines], section)

    def close_bullet():
        nonlocal open_bullet
        if open_bullet is None:
            return
        start, lines, owner = open_bullet
        joined = _join(lines)
        id_match = ID_RE.match(lines[0])
        title_match = BOLD_TITLE_RE.match(joined)
        title = title_match.group(1) if title_match else joined[4:60]
        rule_id = id_match.group(1) if id_match else slug(title)
        owner.bullet_rules.append(Rule(path, start, rule_id, title, joined, "bullet"))
        open_bullet = None

    for number, line in enumerate(text.splitlines(), 1):
        heading = HEADING_RE.match(line)
        if heading:
            close_bullet()
            level = len(heading.group(1))
            if section is not None and level > section.level:
                section.has_children = True
            section = Section(level, heading.group(2).strip(), number)
            sections.append(section)
            continue
        if section is None:
            continue
        if BOLD_BULLET_RE.match(line):
            close_bullet()
            open_bullet = (number, [line], section)
            continue
        if open_bullet is not None:
            if line.startswith((" ", "\t")) and line.strip():
                open_bullet[1].append(line)
                continue
            close_bullet()
        section.prose.append((number, line))
    close_bullet()

    rules = []
    for section in sections:
        if section.level == 1 or section.title.lower() in SKIPPED_SECTION_TITLES:
            continue
        if section.bullet_rules:
            rules.extend(section.bullet_rules)
        elif not section.has_children and any(line.strip() for _, line in section.prose):
            body = _join(line for _, line in section.prose)
            rules.append(Rule(path, section.line, slug(section.title), section.title, body, "prose"))
    return rules


# ---------------------------------------------------------------- references


@dataclass
class Ref:
    """One parsed check reference from a rule's tag."""

    raw: str
    kind: str  # scan | linter | tool | session | review | process | context | unknown
    name: str = ""  # signature id, rule name, tool name, hook id, or linter kind
    linter: str = ""  # the linter kind for kind == "linter"
    severity: str = ""  # for kind == "scan": block | ratchet | advisory
    off: bool = False  # the project's config switched this check off (E5.4)


def parse_ref(raw, linter_kinds):
    raw = raw.strip()
    if raw in PLAIN_KINDS:
        return Ref(raw, raw)
    head, sep, rest = raw.partition(":")
    head, rest = head.strip(), rest.strip()
    if head in SIGNATURE_SEVERITIES and rest:
        return Ref(raw, "scan", rest, severity=SIGNATURE_SEVERITIES[head])
    if head == "tool" and rest:
        return Ref(raw, "tool", rest)
    if head == "session" and rest:
        return Ref(raw, "session", rest)
    if head in linter_kinds and (not sep or rest):
        return Ref(raw, "linter", rest, linter=head)
    return Ref(raw, "unknown", raw)


# ---------------------------------------------------------------- linter configs


def _yaml_top_level_blocks(text):
    """Top-level keys of a simple YAML file with the list items and child keys under each."""
    blocks = {}
    current = None
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        top = re.match(r"^([A-Za-z_][\w./-]*):\s*(.*)$", stripped)
        if top:
            current = top.group(1)
            blocks[current] = {"value": top.group(2), "items": [], "keys": []}
            continue
        if current is None:
            continue
        item = re.match(r"^\s*-\s*([\w./-]+)", stripped)
        if item:
            blocks[current]["items"].append(item.group(1))
            continue
        child = re.match(r"^\s+([\w./-]+):", stripped)
        if child:
            blocks[current]["keys"].append(child.group(1))
    return blocks


SWIFTLINT_SETTING_KEYS = {
    "disabled_rules", "opt_in_rules", "only_rules", "analyzer_rules", "included", "excluded",
    "reporter", "strict", "lenient", "warning_threshold", "cache_path", "allow_zero_lintable_files",
    "baseline", "write_baseline", "check_for_updates", "custom_rules", "child_config", "parent_config",
    "remote_config_timeout", "remote_config_timeout_if_cached", "indentation",
}


def swiftlint_enables(text, rule):
    blocks = _yaml_top_level_blocks(text)
    if rule in blocks.get("disabled_rules", {}).get("items", []):
        return False
    if blocks.get("only_rules", {}).get("items"):
        return rule in blocks["only_rules"]["items"]
    for key in ("opt_in_rules", "analyzer_rules"):
        if rule in blocks.get(key, {}).get("items", []):
            return True
    if rule in blocks and rule not in SWIFTLINT_SETTING_KEYS:
        return blocks[rule]["value"].strip() != "false"
    return False


def detekt_enables(text, rule):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)" + re.escape(rule) + r":\s*$", line.split("#", 1)[0].rstrip())
        if not match:
            continue
        indent = len(match.group(1))
        for later in lines[index + 1:]:
            body = later.split("#", 1)[0].rstrip()
            if not body.strip():
                continue
            if len(body) - len(body.lstrip()) <= indent:
                break
            active = re.match(r"^\s*active:\s*(true|false)", body)
            if active:
                return active.group(1) == "true"
        return False
    return False


def eslint_enables(text, rule):
    pattern = re.compile(r"(?<![\w/@-])(?:['\"])?" + re.escape(rule) + r"(?:['\"])?\s*:\s*(\[\s*)?(['\"]?)(\w+)\2")
    found = False
    for match in pattern.finditer(text):
        found = True
        if match.group(3) in ("off", "0"):
            return False
    return found


def androidlint_enables(text, rule):
    for match in re.finditer(r"<issue\b[^>]*>", text):
        tag = match.group(0)
        if re.search(r'\bid\s*=\s*"' + re.escape(rule) + r'"', tag):
            severity = re.search(r'\bseverity\s*=\s*"(\w+)"', tag)
            return severity is None or severity.group(1).lower() != "ignore"
    return False


def tsc_enables(text, flag):
    try:
        options = json.loads(re.sub(r"//[^\n]*", "", text)).get("compilerOptions", {})
    except (json.JSONDecodeError, AttributeError):
        return False
    return options.get(flag) is True


def mypy_enables(text, flag):
    return re.search(r"^\s*" + re.escape(flag) + r"\s*=\s*[Tt]rue\s*$", text, re.MULTILINE) is not None


def ruff_enables(text, code):
    def list_of(key):
        match = re.search(r"^\s*(?:extend-)?" + key + r"\s*=\s*\[([^\]]*)\]", text, re.MULTILINE)
        return re.findall(r"[\"']([\w-]+)[\"']", match.group(1)) if match else []

    ignored = list_of("ignore")
    if code in ignored:
        return False
    selected = list_of("select")
    return code in selected or "ALL" in selected or any(code.startswith(prefix) for prefix in selected if prefix.isalpha())


def generic_enables(text, rule):
    return re.search(r"(?<![\w/-])" + re.escape(rule) + r"(?![\w/-])", text) is not None


CONFIG_READERS = {
    "swiftlint": swiftlint_enables,
    "detekt": detekt_enables,
    "eslint": eslint_enables,
    "androidlint": androidlint_enables,
    "tsc": tsc_enables,
    "mypy": mypy_enables,
    "ruff": ruff_enables,
}


def config_enables(linter, text, rule):
    """Does this linter's config, as shipped, name the rule enabled?"""
    return CONFIG_READERS.get(linter, generic_enables)(text, rule)


# ---------------------------------------------------------------- the battery


class Battery:
    """The manifest of what each platform's battery runs, and the files it points at."""

    def __init__(self, manifest, root):
        self.manifest = manifest
        self.root = root
        self.platforms = manifest.get("platforms", {})
        self.linter_kinds = {kind for entry in self.platforms.values() for kind in entry.get("linters", {})}
        self._text_cache = {}
        document = self._load_json(manifest.get("signatures_file"))
        self.signatures = None if document is None else flatten_signatures(document)  # {platform: [signature]}

    def _path(self, relative):
        return os.path.join(self.root, relative) if relative else None

    def exists(self, relative):
        return bool(relative) and os.path.isfile(self._path(relative))

    def text(self, relative):
        if relative not in self._text_cache:
            with open(self._path(relative), encoding="utf-8") as handle:
                self._text_cache[relative] = handle.read()
        return self._text_cache[relative]

    def _load_json(self, relative):
        if not self.exists(relative):
            return None
        return json.loads(self.text(relative))

    def platform_names(self, declared):
        """The platforms a document applies to; a bare name is one platform, not its letters."""
        if declared in (None, "all"):
            return list(self.platforms)
        return [declared] if isinstance(declared, str) else list(declared)

    def unknown_platforms(self, platforms):
        return [platform for platform in platforms if platform not in self.platforms]

    def signature_table(self, platform):
        """{id: severity} for one platform's signature list, or None when there is no table."""
        if self.signatures is None:
            return None
        entries = self.signatures.get(platform)
        if entries is None:
            return None
        table = {entry["id"]: entry.get("severity", "block") for entry in entries}
        for entry in entries:  # a group name stands for every signature it holds (e.g. native-pattern)
            group = entry.get("group")
            if group and group not in table:
                table[group] = entry.get("severity", "block")
        return table

    def session_texts(self):
        texts = []
        for relative in self.manifest.get("session_hook_files", []):
            if self.exists(relative):
                texts.append(self.text(relative))
        return texts

    # -- resolution: each returns a list of gap sentences (empty = resolved)

    def resolve(self, ref, platforms):
        if ref.kind in PLAIN_KINDS:
            return []
        if ref.kind == "unknown":
            kinds = ", ".join(sorted(self.linter_kinds | {"scan", "ratchet", "advisory", "tool", "session"} | PLAIN_KINDS))
            return [f"unknown check '{ref.raw}' (expected one of: {kinds})"]
        resolver = {"scan": self._resolve_scan, "linter": self._resolve_linter,
                    "tool": self._resolve_tool, "session": self._resolve_session}[ref.kind]
        return resolver(ref, platforms)

    def _resolve_scan(self, ref, platforms):
        gaps = []
        scanner = self.manifest.get("scanner")
        if not self.exists(scanner):
            gaps.append(f"{ref.raw}: the scanner {scanner or '(none named in the battery)'} does not exist")
        if self.signatures is None:
            gaps.append(f"{ref.raw}: the signatures file {self.manifest.get('signatures_file') or '(none named)'} does not exist")
            return gaps
        for platform in platforms:
            table = self.signature_table(platform)
            if table is None:
                gaps.append(f"{ref.raw}: the signatures file has no {platform} table")
            elif ref.name not in table:
                gaps.append(f"{ref.raw}: no signature '{ref.name}' in the {platform} table")
            elif table[ref.name] != ref.severity:
                gaps.append(f"{ref.raw}: signature '{ref.name}' is {table[ref.name]} in the {platform} table, the rule says {ref.severity}")
        return gaps

    def _resolve_linter(self, ref, platforms):
        gaps = []
        for platform in platforms:
            linters = self.platforms.get(platform, {}).get("linters", {})
            if ref.linter not in linters:
                gaps.append(f"{ref.raw}: the {platform} battery runs no {ref.linter}")
                continue
            config = linters[ref.linter].get("config")
            if not self.exists(config):
                gaps.append(f"{ref.raw}: the {platform} {ref.linter} config {config or '(none named)'} does not exist")
                continue
            if ref.name and not config_enables(ref.linter, self.text(config), ref.name):
                gaps.append(f"{ref.raw}: {config} does not enable {ref.name}")
        return gaps

    def _resolve_tool(self, ref, platforms):
        gaps = []
        for platform in platforms:
            tools = self.platforms.get(platform, {}).get("tools", {})
            if isinstance(tools, list):
                tools = {name: {} for name in tools}
            if ref.name not in tools:
                gaps.append(f"{ref.raw}: the {platform} battery runs no tool '{ref.name}'")
                continue
            runner = tools[ref.name].get("runner")
            if not self.exists(runner):
                gaps.append(f"{ref.raw}: the {platform} runner for {ref.name}, {runner or '(none named)'}, does not exist")
            elif not generic_enables(self.text(runner), ref.name):
                gaps.append(f"{ref.raw}: {runner} never mentions {ref.name}")
        return gaps

    def _resolve_session(self, ref, platforms):
        texts = self.session_texts()
        if not texts:
            named = ", ".join(self.manifest.get("session_hook_files", [])) or "(none named in the battery)"
            return [f"{ref.raw}: no session hook file exists ({named})"]
        if not any(generic_enables(text, ref.name) for text in texts):
            return [f"{ref.raw}: no session hook file names '{ref.name}'"]
        return []

    def unnamed_signatures(self, named_by_platform):
        """(platform, id) pairs in the signatures file that no applicable rule names."""
        if not self.signatures:
            return []
        unnamed = []
        for platform, entries in self.signatures.items():
            named = named_by_platform.get(platform, set())
            for entry in entries:
                if entry["id"] not in named and entry.get("group") not in named:
                    unnamed.append((platform, entry["id"]))
        return unnamed


# ---------------------------------------------------------------- verification


TOOL_SEATS = {"warnings-as-errors": "build"}   # a tool whose pre-push seat has another name


def ref_is_off(ref, config):
    """Whether the project's config switches this reference off (E5.4)."""
    if ref.kind == "scan":
        return ref.name in config["rules"]["off"]
    if ref.kind == "linter":
        return _config.is_off(config, "linters", ref.linter)
    if ref.kind == "tool":
        return _config.is_off(config, "seats", TOOL_SEATS.get(ref.name, ref.name))
    if ref.kind == "session":
        return _config.is_off(config, "session_hooks", ref.name)
    return False


def categorize(rule):
    kinds = {ref.kind for ref in rule.refs}
    if rule.gaps:
        return "open"
    if "context" in kinds:
        return "context"
    live = [ref for ref in rule.refs if not ref.off]
    switched_off = any(ref.off for ref in rule.refs)
    advisory = any(ref.kind == "scan" and ref.severity == "advisory" for ref in live)
    machine = any(ref.kind in MACHINE_KINDS and not (ref.kind == "scan" and ref.severity == "advisory") for ref in live)
    soft = advisory or bool(kinds & {"review", "process"})
    if machine and not soft and not switched_off:
        return "machine"
    if machine:
        return "partly"
    if switched_off:
        return "off"   # every machine reference is switched off: no check holds this rule any more
    if advisory:
        return "advisory"
    if "review" in kinds:
        return "review"
    return "process"


BINS = ("machine", "partly", "advisory", "review", "process", "off", "open")


def verify_document(path, text, platforms, battery, config=None):
    config = config or _config.defaults()
    rules = parse_document(text, path)
    for rule in rules:
        tag = rule.tag_text
        if tag is None:
            rule.gaps.append("no check tag")
        elif not tag.strip():
            rule.gaps.append("empty check tag")
        else:
            rule.refs = [parse_ref(part, battery.linter_kinds) for part in tag.split(",") if part.strip()]
            if any(ref.kind == "context" for ref in rule.refs) and len(rule.refs) > 1:
                rule.gaps.append("'context' cannot share a tag with a check")
            for ref in rule.refs:
                rule.gaps.extend(battery.resolve(ref, platforms))
                ref.off = ref_is_off(ref, config)
        rule.category = categorize(rule)
    return rules


def counts_for(rules):
    counted = [rule for rule in rules if rule.category != "context"]
    counts = {bin_name: sum(1 for rule in counted if rule.category == bin_name) for bin_name in BINS}
    counts["total"] = len(counted)
    counts["context"] = len(rules) - len(counted)
    return counts


def number_label():
    """The headline's wording, from vocabulary.json beside this file (one place, so a rename is one edit)."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocabulary.json"), encoding="utf-8") as handle:
            return json.load(handle)["number"]["label"]
    except (OSError, ValueError, KeyError):
        return "enforced by a check"


def summary_line(label, counts):
    off = f" ({counts['off']} switched off)" if counts.get("off") else ""
    return (f"{label}: {number_label()} {counts['machine']} of {counts['total']}{off} · partly {counts['partly']}"
            f" · advisory {counts['advisory']} · reviewer {counts['review']} · process {counts['process']}"
            f" · open {counts['open']}")


def run(root, manifest_path, documents_override=None, platforms_override=None, config=None):
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    battery = Battery(manifest, root)
    config = config or _config.defaults()
    if documents_override:
        declared = platforms_override or "all"
        documents = [{"path": path, "platforms": declared} for path in documents_override]
    else:
        documents = manifest.get("documents", [])

    report = {"documents": [], "gaps": [], "totals": {}}
    named_by_platform = {}
    all_rules = []
    for entry in documents:
        path = entry["path"]
        platforms = battery.platform_names(entry.get("platforms", entry.get("platform", "all")))
        full = path if os.path.isabs(path) else os.path.join(root, path)
        for platform in battery.unknown_platforms(platforms):
            report["gaps"].append({"path": path, "line": 0, "id": "-",
                                   "words": f"the document names platform '{platform}', which the battery does not know"})
        if not os.path.isfile(full):
            report["gaps"].append({"path": path, "line": 0, "id": "-", "words": "document does not exist"})
            continue
        with open(full, encoding="utf-8") as handle:
            rules = verify_document(path, handle.read(), platforms, battery, config)
        for rule in rules:
            for ref in rule.refs:
                if ref.kind == "scan":
                    for platform in platforms:
                        named_by_platform.setdefault(platform, set()).add(ref.name)
            for words in rule.gaps:
                report["gaps"].append({"path": path, "line": rule.line, "id": rule.id, "words": words})
        counts = counts_for(rules)
        report["documents"].append({
            "path": path, "platforms": platforms, "counts": counts,
            "rules": [{"id": r.id, "line": r.line, "title": r.title, "kind": r.kind, "category": r.category,
                       "checks": [ref.raw for ref in r.refs], "off": [ref.raw for ref in r.refs if ref.off],
                       "gaps": r.gaps} for r in rules],
        })
        all_rules.extend(rules)
    # A signature no rule names is a gap of the CORPUS: only the whole manifest can say it.
    # One project's document names the checks its platform holds, not every signature in
    # the table (a single iOS document left 198 false gaps and exit 1 before this guard).
    if not documents_override:
        for platform, signature_id in battery.unnamed_signatures(named_by_platform):
            report["gaps"].append({"path": manifest.get("signatures_file", ""), "line": 0, "id": signature_id,
                                   "words": f"signature '{signature_id}' in the {platform} table is named by no rule"})
    report["totals"] = counts_for(all_rules)
    report["gap_count"] = len(report["gaps"])
    return report


def fail_line(gap):
    return f"FAIL {CHECK_NAME} {gap['path']}:{gap['line']}:{gap['id']}: {gap['words']}"


def ratchet_verdict(report, baseline, today):
    """(ok, sentence) for the gap count against a committed baseline."""
    count = baseline.get("count")
    deadline = baseline.get("deadline")
    gaps = report["gap_count"]
    if not isinstance(count, int) or not isinstance(deadline, str):
        return False, "the baseline file needs an integer 'count' and a 'deadline' (YYYY-MM-DD)"
    try:
        deadline_date = _dt.date.fromisoformat(deadline)
    except ValueError:
        return False, f"the baseline deadline '{deadline}' is not a date (YYYY-MM-DD)"
    if gaps > count:
        return False, f"the gap count rose from {count} to {gaps} — a rule lost its check, or a new rule has none"
    if gaps < count:
        return False, f"the gap count fell from {count} to {gaps} — lower the baseline to {gaps} in the same commit"
    if today > deadline_date and gaps > 0:
        return False, f"the baseline deadline {deadline} has passed with {gaps} gaps still open — the check is now blocking"
    days_left = (deadline_date - today).days
    return True, f"{gaps} gaps, equal to the baseline; {days_left} days until the deadline {deadline}"


def main(argv=None):
    default_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description="Rule document ↔ battery parity.")
    parser.add_argument("--root", default=default_root, help="repo root the manifest's paths are relative to")
    parser.add_argument("--battery", default=None, help="the battery manifest (default enforcement/checks/battery.json under --root)")
    parser.add_argument("--document", action="append", help="verify this document instead of the manifest's list (repeatable)")
    parser.add_argument("--platform", action="append", help="platform(s) a --document applies to (repeatable; default all)")
    parser.add_argument("--baseline", help="ratchet mode: pass only while the gap count equals this file's count")
    parser.add_argument("--config", help="the project's config.json, whose switches make a rule 'off' (default: the "
                                         "state dir's config.json under the working directory when one exists, else the shipped defaults)")
    parser.add_argument("--summary", action="store_true", help="print the per-document lines and totals only")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    manifest_path = args.battery or os.path.join(args.root, "enforcement", "checks", "battery.json")
    if not os.path.isfile(manifest_path):
        print(f"FAIL {CHECK_NAME} {manifest_path}:0:-: the battery manifest does not exist")
        return 1
    try:
        config = _config.load(path=args.config) if args.config else _config.load()
    except _config.ConfigError as error:
        print(f"FAIL {CHECK_NAME} {args.config or _config.config_path()}:0:config: {error}")
        return 1
    report = run(args.root, manifest_path, args.document, args.platform, config)

    if not args.json:
        for document in report["documents"]:
            print(summary_line(f"{document['path']} [{', '.join(document['platforms'])}]", document["counts"]))
        if not args.summary:
            for gap in report["gaps"]:
                print(fail_line(gap))
        print(summary_line("TOTAL", report["totals"]))

    gaps = report["gap_count"]
    if args.baseline:
        with open(args.baseline, encoding="utf-8") as handle:
            baseline = json.load(handle)
        today = _dt.date.fromisoformat(args.today) if args.today else _dt.date.today()
        ok, sentence = ratchet_verdict(report, baseline, today)
        verdict = f"{'OK' if ok else 'FAIL'} {CHECK_NAME} baseline: {sentence}"
    elif gaps:
        ok, verdict = False, f"FAIL {CHECK_NAME}: {gaps} gaps — every rule names its check and every check runs, or this fails"
    else:
        ok, verdict = True, f"OK {CHECK_NAME}: every rule names its check and every check runs"
    report["verdict"] = verdict
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(verdict)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
