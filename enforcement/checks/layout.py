#!/usr/bin/env python3
"""The layout — every path the enforcement layer names in a project, read from
one table, ``layout.json`` beside this file (enforcement/README.md task E5.1).

* ``defaults()`` is the shipped table.
* ``load(root)`` is a project's layout: the defaults, then the keys the project
  overrides under ``"layout"`` in ``<root>/<state_dir>/config.json`` (the
  config file of task E5.3; ``adopt.py --checks-dir`` is the one flag that
  fills a key, a founder may edit the rest), then any ``overrides`` given.
  ``state_dir`` is the anchor the hooks find the config by, so it comes from
  the defaults (or ``<prefix>STATE_DIR``) and a project file cannot move it.
* ``Layout.expand(text)`` fills ``{key}`` placeholders — the shape ``paths.json``'s
  governing classes, ``claude-settings.json`` and the linter seeds are written in
  (a seed excludes the layer's own folder, so a project's linter never lints the
  checks: ``{state_dir}``, or ``{state_dir_regex}`` where the tool wants a regex).
* ``Layout.to_sh()`` is the ``layout.sh`` the installer writes beside the
  platform file, which a ``sh`` hook sources instead of carrying literals.

Stdlib only; shipped into the project's checks directory with the scanner.
"""

from __future__ import annotations

import json
import os
import re
import shlex

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULTS_FILE = os.path.join(HERE, "layout.json")
CONFIG_FILE = "config.json"    # the project's config, in its state dir; its "layout" key overrides this table
SCRIPT_FILE = "layout.sh"      # the rendered table the sh hooks source, in its state dir
KEYS = ("checks_dir", "hooks_dir", "session_hook", "settings_file", "state_dir", "rules_document",
        "ai_rules_document", "context_file", "lock_name", "temp_prefix", "env_prefix")
DERIVED = ("session_hook_dir", "settings_local_file", "state_dir_regex")
PLACEHOLDER = re.compile(r"\{(" + "|".join(KEYS + DERIVED) + r")\}")


class Layout(dict):
    """The table with its derived names and the few renderings the layer needs."""

    @property
    def session_hook_dir(self):
        return os.path.dirname(self.expand(self["session_hook"]))

    @property
    def settings_local_file(self):
        base, extension = os.path.splitext(self.expand(self["settings_file"]))
        return f"{base}.local{extension}"

    @property
    def state_dir_regex(self):
        r"""The state dir escaped for a tool whose exclude is a regular expression (mypy's
        ``--exclude``, whose own help escapes the dot: ``--exclude '/setup\.py$'``)."""
        return re.escape(self.expand(self["state_dir"]))

    def value(self, key):
        if key in DERIVED:
            return getattr(self, key)
        return self.expand(self[key])

    def expand(self, text):
        """``{key}`` placeholders filled from the table; anything else is left as it is."""
        return PLACEHOLDER.sub(lambda match: self.value(match.group(1)), text)

    def state_file(self, name):
        return f"{self['state_dir']}/{name}"

    def env(self, name):
        """The environment variable's name: ``env("PLATFORM")`` is ``COAST_PLATFORM`` by default."""
        return self["env_prefix"] + name

    def env_value(self, name, default=None):
        return os.environ.get(self.env(name)) or default

    @property
    def jscpd_ignore(self):
        return ",".join(self.expand(glob) for glob in self.get("jscpd_ignore", []))

    def overrides(self):
        """The keys that differ from the shipped table — what a project's config carries."""
        shipped = defaults()
        return {key: self[key] for key in KEYS + ("jscpd_ignore",) if self.get(key) != shipped.get(key)}

    def to_sh(self):
        """The ``layout.sh`` a hook sources: one ``layout_<key>`` variable per key, every value expanded;
        the checks dir and the platform take the environment first (the tests point them elsewhere).
        The config's switches are not here: a hook evaluates ``config.py --sh`` from the checks dir, so
        an edit to the config counts on the next run without a re-install."""
        lines = ["# Written by adopt.py from the layout table (layout.json beside the checks). GOVERNING: do not",
                 "# edit; a project's own paths go under \"layout\" in config.json beside this file, then adopt.py again.",
                 f"layout_checks_dir=${{{self.env('CHECKS_DIR')}:-{shlex.quote(self.value('checks_dir'))}}}"]
        for key in KEYS:
            if key != "checks_dir":
                lines.append(f"layout_{key}={shlex.quote(self.value(key))}")
        for key in DERIVED:
            lines.append(f"layout_{key}={shlex.quote(self.value(key))}")
        lines.append(f"layout_platform=${{{self.env('PLATFORM')}:-}}")
        lines.append(f"layout_jscpd_ignore={shlex.quote(self.jscpd_ignore)}")
        return "\n".join(lines) + "\n"


def defaults():
    with open(DEFAULTS_FILE, encoding="utf-8") as handle:
        table = json.load(handle)
    return Layout((key, value) for key, value in table.items() if key != "_comment")


def state_dir_anchor(table=None):
    """Where a project's own config lives: the environment's ``<prefix>STATE_DIR``, else the default."""
    table = table or defaults()
    return table.env_value("STATE_DIR", table["state_dir"])


def project_layout_overrides(root=None, table=None):
    """The ``layout`` object of the project's config file, or {} (a missing or broken file is no override)."""
    table = table or defaults()
    config_file = os.path.join(root or ".", state_dir_anchor(table), CONFIG_FILE)
    if not os.path.isfile(config_file):
        return {}
    try:
        with open(config_file, encoding="utf-8") as handle:
            own = json.load(handle)
    except ValueError:
        return {}
    own = own.get("layout") if isinstance(own, dict) else None
    return own if isinstance(own, dict) else {}


def load(root=None, overrides=None):
    """A project's layout (see the module docstring). ``root`` defaults to the working directory."""
    table = defaults()
    table["state_dir"] = state_dir_anchor(table)
    for source in (project_layout_overrides(root, table), overrides or {}):
        table.update((key, value) for key, value in source.items()
                     if key in KEYS + ("jscpd_ignore",) and key != "state_dir" and value)
    return table


if __name__ == "__main__":
    import sys
    print(load(sys.argv[1] if len(sys.argv) > 1 else None).to_sh(), end="")
