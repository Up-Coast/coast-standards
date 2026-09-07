#!/usr/bin/env python3
"""claude-hook.py — the session layer's one entry point (enforcement task E2.1).

Every Claude Code hook in ``claude-settings.json`` runs this file with one
argument, the hook id::

    claude-hook.py <hook-id>        # the event's JSON arrives on stdin

It reads the event, decides, and exits: 0 lets the action through, 2 refuses
it with the reason on stderr. Design: ``enforcement/README.md`` §4.4 (the hook
table is the spec) and §7 decision 3. Stdlib only. No network. No model.

The hooks (each id is also a ``session:<id>`` reference a rule document can
name; ``verify_rules.py`` resolves it by finding the id in this file and in
``claude-settings.json``):

* ``governing-edit`` — PreToolUse on Edit|Write|MultiEdit|NotebookEdit.
  Refuses a path in the platform's GOVERNING class (``paths.json`` beside the
  scanner is the one table: ``Scripts/checks/**``, ``.githooks/**``,
  ``.github/**``, ``.coast/**``, the rules documents, the linter configs) and
  ``.claude/settings.json`` (this layer's own wiring, which no path class
  names). Agents never edit the files that define their own checks.
* ``chained-cd`` — PreToolUse on Bash. Refuses ``cd X && …``, ``cd X; …`` and
  a ``cd`` line followed by more commands. A bare ``cd`` alone passes.
* ``infra-command`` — PreToolUse on Bash. Refuses the infrastructure
  programs (fly, flyctl, wrangler, cloudflared, terraform, tofu, pulumi,
  doctl, aws, gcloud, az, nsupdate), ``gh repo delete``, ``gh secret …``,
  ``gh variable …``, ``gh ruleset …``, and a mutating ``gh api`` (``-X``
  DELETE|PUT|POST|PATCH, or ``-f``/``-F``/``--input``, which make gh POST) on
  a repo, ruleset, secret, variable, hook, key, environment, deployment or
  branch-protection endpoint. ``dig`` and ``nslookup`` only read DNS and
  pass; the DNS writer is ``nsupdate``. The sentence: "this changes
  infrastructure — ask Abbey in one line first".
* ``no-verify`` — PreToolUse on Bash. Refuses ``--no-verify`` in any git
  command, ``git commit -n`` (its short form) and ``-c core.hooksPath=…``.
* ``force-push`` — PreToolUse on Bash. Refuses ``git push`` with ``--force``,
  ``-f``, ``--force-with-lease``, ``--force-if-includes`` or a ``+refspec``.
* ``scan-at-commit`` — PreToolUse on Bash, only when the command runs
  ``git commit``. Runs ``check_rules.py --staged --platform <p>`` from the
  repo root; a red scan refuses the commit with the FAIL lines.
* ``scan-on-edit`` — PostToolUse on Edit|Write|MultiEdit. Runs
  ``check_rules.py --files <path>`` on the touched file. It cannot block
  (the edit already happened); it exits 2 with the findings on stderr
  because that is the only way the model sees them (see the doc quotes).
* ``unpushed-at-stop`` — Stop. Refuses to end the turn while
  ``git log @{upstream}..HEAD`` is non-empty or the working tree holds
  changes to product source, with "push before finishing".
  ``stop_hook_active: true`` → exit 0 (no loop); no upstream → exit 0 with a
  note.
* ``rules-at-start`` — SessionStart. Prints, as context: the platform and
  project type from ``.coast/platform``, the enforced/total number for the
  project's ``docs/domain-rules.md`` (else the corpus TOTAL line), the
  review-only rules in one list, and the ratchet counts from
  ``.coast/ratchet-baseline.json``. Always exits 0.

Where things are:

* The checks resolve relative to this file first (``../checks/`` — the
  standards repo's layout), then ``Scripts/checks/`` under the repo root
  (the installed layout ``adopt.py`` writes).
* The platform comes from ``.coast/platform`` (a one-line text file: the
  platform name, optionally followed by the project type letter — ``ios A``)
  or the ``COAST_PLATFORM`` environment variable.
* The repo root is ``git rev-parse --show-toplevel`` from the event's ``cwd``.

What the primary source says (Anthropic's Claude Code hooks reference,
https://code.claude.com/docs/en/hooks — the address
https://docs.anthropic.com/en/docs/claude-code/hooks redirects there; read
2026-09-04). Nothing below claims a behaviour that page does not state:

* Input: "Command hooks receive JSON data via stdin and communicate results
  through exit codes, stdout, and stderr." PreToolUse "hooks receive
  ``tool_name``, ``tool_input``, and ``tool_use_id``"; for Bash
  ``tool_input.command`` is "The shell command to execute"; "For the file
  tools ``Write``, ``Edit``, and ``Read``, ``tool_input.file_path`` is always
  absolute". PostToolUse input "includes both ``tool_input`` … and
  ``tool_response``". Stop "hooks receive ``stop_hook_active``,
  ``last_assistant_message``, ``background_tasks``, and ``session_crons``. The
  ``stop_hook_active`` field is ``true`` when Claude Code is already
  continuing as a result of a stop hook. Check this value or process the
  transcript to avoid blocking on a condition that will never resolve."
  SessionStart hooks "receive ``source`` and optionally ``model``".
* Settings schema: ``{"hooks": {"<Event>": [{"matcher": …, "hooks":
  [{"type": "command", "command": …}]}]}}``. Matcher: "``Bash`` matches only
  the Bash tool; ``Edit|Write`` and ``Edit, Write`` each match either tool
  exactly"; "``\"*\"``, ``\"\"``, or omitted — Match all". The ``if`` field:
  "Permission rule syntax to filter when this hook runs, such as
  ``\"Bash(git *)\"`` or ``\"Edit(*.ts)\"``. The hook command only runs if the
  tool call matches the pattern." and "``\"Bash(git *)\"`` runs when any
  subcommand of the Bash input matches ``git *``" — and the same page says
  the filter is best-effort prefix matching, so ``if: Bash(git commit *)``
  would never fire for ``git -C <dir> commit`` or ``git -c … commit``. The
  settings file therefore carries no ``if``: ``scan-at-commit`` reads the
  command itself and passes anything that is not a commit (2026-09-07).
  ``${CLAUDE_PROJECT_DIR}`` in a command is a documented path placeholder,
  also exported "as the environment variables ``CLAUDE_PROJECT_DIR`` …".
* Exit codes: "Exit code 2 is the way a hook signals 'stop, don't do this.'"
  Per event: PreToolUse — "Blocks the tool call"; Stop — "Prevents Claude
  from stopping, continues the conversation" and "A hook that blocks by
  exiting 2 routes the same way as ``reason``: Claude receives the stderr
  message as the explanation for why it should continue"; PostToolUse —
  "Shows stderr to Claude; the tool already ran". "The blocking message is
  the reason from your JSON's blocking decision when it makes one, and your
  stderr text otherwise." On PreToolUse, "Claude sees the stderr message as
  the denial reason." Exit 0: "Stderr from a hook that exits 0 goes to the
  debug log only, never the transcript, and Claude never sees it. … To
  surface a warning to Claude from a ``PostToolUse`` … hook, exit 2 instead
  so Claude sees the stderr even though the tool already ran." — which is
  why ``scan-on-edit`` exits 2 with findings. "Without valid JSON on stdout,
  Claude Code treats exit code 1 as a non-blocking error and proceeds".
* SessionStart: on exit 0 "Claude Code adds plain-text stdout as context that
  Claude can see and act on" (SessionStart is one of the named exceptions);
  for SessionStart an exit-2 stderr is rendered as a hook error notice and
  "Claude doesn't see it, and the session … proceeds" — so
  ``rules-at-start`` prints to stdout and exits 0.
* Stop loop cap: "Claude Code overrides the hook and ends the turn after 8
  consecutive blocks."
"""

import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM_FILE = ".coast/platform"
RATCHET_BASELINE_FILE = ".coast/ratchet-baseline.json"
RULES_DOCUMENT = "docs/domain-rules.md"
ALWAYS_GOVERNING = (".claude/settings.json",)
NOT_PRODUCT_SOURCE = {"git", "governing", "plans", "generated", "docs", "design_bundle"}
INFRA_PROGRAMS = {"fly", "flyctl", "wrangler", "cloudflared", "terraform", "tofu", "pulumi",
                  "doctl", "aws", "gcloud", "az", "nsupdate"}
INFRA_SENTENCE = "this changes infrastructure — ask Abbey in one line first"
GH_MUTATING_METHODS = {"DELETE", "PUT", "POST", "PATCH"}
GH_INFRA_ENDPOINT = re.compile(r"rulesets|secrets|/hooks|/variables|/protection|/keys|/environments|/deployments")
GH_RESOURCE_ENDPOINT = re.compile(r"^/?(repos/[^/]+/[^/]+/?|user/repos/?|orgs/[^/]+/repos/?)$")
COMMAND_WRAPPERS = {"sudo", "env", "time", "nohup", "command", "exec", "nice"}
SEGMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\n)\s*")
CHAINED_CD = re.compile(r"(?:^|[;&|(]\s*|\n\s*)cd(?:\s+[^\n;&|]*)?\s*(?:&&|;|\|\|)")
CD_THEN_MORE = re.compile(r"(?:^|\n)\s*cd\b[^\n]*\n\s*\S")
PASS, BLOCK = 0, 2


# ---------------------------------------------------------------- plumbing


def read_event():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError:
        event = {}
    return event if isinstance(event, dict) else {}


def run(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)


def repo_root(event):
    cwd = event.get("cwd") or os.getcwd()
    if not os.path.isdir(cwd):
        return None
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    return result.stdout.strip() or None if result.returncode == 0 else None


def checks_dir(root):
    for candidate in (os.path.join(HERE, "..", "checks"), os.path.join(root or "", "Scripts", "checks")):
        if os.path.isfile(os.path.join(candidate, "check_rules.py")):
            return os.path.normpath(candidate)
    return None


def platform_of(root):
    """(platform, project type) from .coast/platform, else COAST_PLATFORM; either may be None."""
    if root:
        try:
            with open(os.path.join(root, PLATFORM_FILE), encoding="utf-8") as handle:
                words = handle.readline().split()
            if words:
                return words[0], (words[1] if len(words) > 1 else None)
        except OSError:
            pass
    return os.environ.get("COAST_PLATFORM") or None, None


def scanner_module(checks):
    if checks not in sys.path:
        sys.path.insert(0, checks)
    import check_rules  # noqa: E402  (the scanner beside these hooks; one PathClasses for everyone)
    return check_rules


def path_classes(checks, platform):
    """[PathClasses] — the platform's table (with the project's override) or, platform unknown, every table."""
    scanner = scanner_module(checks)
    with open(os.path.join(checks, "paths.json"), encoding="utf-8") as handle:
        tables = json.load(handle)["platforms"]
    if platform in tables:
        return [scanner.load_tables(platform, None)[1]]
    return [scanner.PathClasses(table) for table in tables.values()]


def relative_to_root(path, root):
    """The repo-relative path with forward slashes, or None when the path is outside the repo."""
    if not path or not root:
        return None
    path = path.replace("\\", "/")
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(root))
    return None if rel == ".." or rel.startswith("../") else rel.replace(os.sep, "/")


def edited_path(event):
    tool_input = event.get("tool_input") or {}
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def command_of(event):
    return (event.get("tool_input") or {}).get("command") or ""


def segments(command):
    return [part for part in SEGMENT_SPLIT.split(command) if part.strip()]


def words(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def program_and_args(tokens):
    """The program actually run (basename, wrappers and VAR=value skipped) and its arguments."""
    index = 0
    while index < len(tokens):
        token = tokens[index].lstrip("(")
        if "=" in token and not token.startswith("-") and index == 0 or token in COMMAND_WRAPPERS or token == "":
            index += 1
            continue
        return os.path.basename(token), tokens[index + 1:]
    return "", []


def git_subcommand(args):
    """The git subcommand and everything after it, skipping git's own options (-C dir, -c key=value, --flag)."""
    index = 0
    while index < len(args):
        token = args[index]
        if token in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token, args[index + 1:]
    return "", []


def refuse(*lines):
    sys.stderr.write("\n".join(lines).rstrip() + "\n")
    return BLOCK


def scanner_lines(output):
    return [line for line in output.splitlines() if line and not line.startswith("{")]


# ---------------------------------------------------------------- the hooks


def governing_edit(event):
    path = edited_path(event)
    root = repo_root(event)
    rel = relative_to_root(path, root)
    if rel is None:
        return PASS
    governed = rel in ALWAYS_GOVERNING
    checks = checks_dir(root)
    if not governed and checks:
        os.chdir(root)
        platform, _ = platform_of(root)
        governed = any(classes.classify(rel) == "governing" for classes in path_classes(checks, platform))
    if not governed:
        return PASS
    return refuse(f"governing-edit: {rel} defines the checks (a governing file). Agents never edit the files "
                  "that define their own checks — say what needs to change and ask Abbey to change it.")


def chained_cd(event):
    command = command_of(event)
    if not (CHAINED_CD.search(command) or CD_THEN_MORE.search(command)):
        return PASS
    return refuse("chained-cd: a `cd X && …` chain is not an atomic command. Run one command with absolute "
                  "paths instead (`git -C <dir> …`, `make -C <dir>`, or the full path); a bare `cd` alone is fine.")


def gh_is_infrastructure(args):
    sub, rest = (args[0], args[1:]) if args else ("", [])
    if sub == "repo" and rest[:1] == ["delete"]:
        return True
    if sub in ("secret", "variable", "ruleset"):
        return True
    if sub != "api":
        return False
    method, mutating, endpoint = "GET", False, ""
    index = 0
    while index < len(rest):
        token = rest[index]
        if token in ("-X", "--method"):
            method = rest[index + 1].upper() if index + 1 < len(rest) else method
            index += 2
            continue
        if token.startswith("-X") or token.startswith("--method="):
            method = token.split("=", 1)[-1] if "=" in token else token[2:]
            method = method.upper()
        elif token in ("-f", "-F", "--field", "--raw-field", "--input") or token.startswith(("--field=", "--raw-field=", "--input=")):
            mutating = True
            if "=" not in token:
                index += 1
        elif token.startswith("-"):
            pass
        elif not endpoint:
            endpoint = token
        index += 1
    mutating = mutating or method in GH_MUTATING_METHODS
    return mutating and bool(GH_INFRA_ENDPOINT.search(endpoint) or GH_RESOURCE_ENDPOINT.match(endpoint))


def infra_command(event):
    for segment in segments(command_of(event)):
        program, args = program_and_args(words(segment))
        if program in INFRA_PROGRAMS or (program == "gh" and gh_is_infrastructure(args)):
            return refuse(f"infra-command: `{segment.strip()}` — {INFRA_SENTENCE}. Read-only checks (status, "
                          "logs, health) are fine; creating, changing or destroying anything is not without her word.")
    return PASS


def no_verify(event):
    for segment in segments(command_of(event)):
        program, args = program_and_args(words(segment))
        if program != "git":
            continue
        sub, rest = git_subcommand(args)
        bypass = any(token.startswith("--no-verif") for token in args)   # git accepts any unique prefix
        bypass = bypass or any(token.lower().startswith("core.hookspath=") for token in args)   # keys are case-insensitive
        if sub == "config" and any(token.lower() == "core.hookspath" or token.lower().startswith("core.hookspath=") for token in rest):
            bypass = True   # pointing the hooks path elsewhere (or unsetting it) is the same switch by another route
        if sub == "commit":
            bypass = bypass or any(re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", token) for token in rest)
        if bypass:
            return refuse("no-verify: the hooks are the gate. Fix what they report and run the command again "
                          "without --no-verify (git commit -n is the same switch).")
    return PASS


def force_push(event):
    for segment in segments(command_of(event)):
        program, args = program_and_args(words(segment))
        if program != "git":
            continue
        sub, rest = git_subcommand(args)
        if sub != "push":
            continue
        for token in rest:
            forced = (token in ("--force", "-f", "--force-if-includes") or token.startswith("--force-with-lease")
                      or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", token) or (token.startswith("+") and len(token) > 1))
            if forced:
                return refuse("force-push: a force push rewrites history the remote already shares. Push a new "
                              "commit instead; if a branch truly needs rewriting, ask Abbey in one line first.")
    return PASS


def git_commit_directories(command):
    """One entry per `git commit` in the command: the directory git was pointed at with -C, else None."""
    found = []
    for segment in segments(command):
        program, args = program_and_args(words(segment))
        if program != "git" or git_subcommand(args)[0] != "commit":
            continue
        directory = None
        for index, token in enumerate(args[:-1]):
            if token == "-C":
                directory = os.path.join(directory, args[index + 1]) if directory else args[index + 1]
        found.append(directory)
    return found


def runs_git_commit(command):
    return bool(git_commit_directories(command))


def scan_at_commit(event):
    directories = git_commit_directories(command_of(event))
    if not directories:
        return PASS
    # A commit pointed at another repository (`git -C <dir> commit`) is that repository's business:
    # its own installed checks scan it, and a repository with none is not scanned by ours.
    root = repo_root(event)
    target = directories[-1]
    checks = checks_dir(root)
    if target:
        base = event.get("cwd") or os.getcwd()
        try:
            pointed = run(["git", "rev-parse", "--show-toplevel"], cwd=os.path.join(base, os.path.expanduser(target)))
        except OSError:
            return PASS   # the directory does not exist; git will say so itself
        pointed_root = pointed.stdout.strip() if pointed.returncode == 0 else None
        if pointed_root and os.path.realpath(pointed_root) != os.path.realpath(root or ""):
            root = pointed_root
            checks = os.path.join(root, "Scripts", "checks")
            if not os.path.isfile(os.path.join(checks, "check_rules.py")):
                return PASS
    if not root or not checks:
        return PASS
    platform, _ = platform_of(root)
    if not platform:
        sys.stderr.write("scan-at-commit: the platform is not known (.coast/platform missing, COAST_PLATFORM unset) "
                         "— the staged diff was not scanned.\n")
        return PASS
    result = run([sys.executable, os.path.join(checks, "check_rules.py"), "--staged", "--platform", platform], cwd=root)
    if result.returncode == 0:
        return PASS
    return refuse(*scanner_lines(result.stdout), result.stderr.strip(),
                  "scan-at-commit: the scanner refuses this commit — fix the lines above, stage the fix, and commit again.")


def scan_on_edit(event):
    root = repo_root(event)
    checks = checks_dir(root)
    rel = relative_to_root(edited_path(event), root)
    if rel is None or not checks or not os.path.isfile(os.path.join(root, rel)):
        return PASS
    platform, _ = platform_of(root)
    if not platform:
        return PASS
    result = run([sys.executable, os.path.join(checks, "check_rules.py"), "--files", rel, "--platform", platform], cwd=root)
    if result.returncode == 0:
        return PASS
    return refuse(*scanner_lines(result.stdout), result.stderr.strip(),
                  f"scan-on-edit: the scanner found these after the edit to {rel} — fix them before committing "
                  "(the edit itself already happened; nothing was blocked).")


def status_paths(root):
    paths = []
    for line in run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root).stdout.splitlines():
        if len(line) > 3:
            paths.append(line[3:].split(" -> ")[-1].strip().strip('"'))
    return paths


def unpushed_at_stop(event):
    if event.get("stop_hook_active"):
        return PASS
    root = repo_root(event)
    if not root:
        return PASS
    upstream = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=root)
    if upstream.returncode != 0:
        print("unpushed-at-stop: this branch has no upstream, so nothing can be compared — set one with "
              "`git push -u origin <branch>` when the work is ready to leave this machine.")
        return PASS
    ahead = run(["git", "log", "--oneline", "@{upstream}..HEAD"], cwd=root)
    ahead_lines = [line for line in ahead.stdout.splitlines() if line.strip()] if ahead.returncode == 0 else []
    changed = status_paths(root)
    checks = checks_dir(root)
    platform, _ = platform_of(root)
    if checks and changed:
        os.chdir(root)
        tables = path_classes(checks, platform)
        changed = [p for p in changed if any(classes.classify(p) not in NOT_PRODUCT_SOURCE for classes in tables)]
    if not ahead_lines and not changed:
        return PASS
    lines = ["unpushed-at-stop: push before finishing."]
    if ahead_lines:
        lines.append(f"{len(ahead_lines)} commit(s) are not on {upstream.stdout.strip()}: " + "; ".join(ahead_lines[:5]))
    if changed:
        lines.append("uncommitted changes to product source: " + ", ".join(changed[:10]))
    lines.append("Commit what is finished, push it (every commit gets pushed in the same session), then finish.")
    return refuse(*lines)


def rules_number_from_claude_md(root):
    """The number adopt.py wrote into the CLAUDE.md block (the verifier itself stays in the standards repo)."""
    try:
        with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return "rules held by a machine: unknown (no CLAUDE.md block — run adopt.py)"
    match = re.search(r"Rules held by a machine: (\d+) of (\d+)\*\*\s+in that document\s*\((.*?)\)", text, re.DOTALL)
    if not match:
        return "rules held by a machine: unknown (no CLAUDE.md block — run adopt.py)"
    detail = " ".join(match.group(3).split())
    return f"rules held by a machine: {match.group(1)} of {match.group(2)} in docs/domain-rules.md ({detail}) — as of the last adopt.py run"


def rules_number(root, checks, platform):
    """(lines for the context, review-only titles) from verify_rules.py, or a plain sentence when it cannot run."""
    verifier = os.path.join(checks, "verify_rules.py")
    if not os.path.isfile(verifier):
        return [rules_number_from_claude_md(root)], []
    battery = os.path.join(checks, "battery.json")
    args = [sys.executable, verifier, "--root", os.path.dirname(os.path.dirname(checks)), "--json"]
    if os.path.isfile(battery):
        args += ["--battery", battery]
    document = os.path.join(root, RULES_DOCUMENT)
    scope = "this project's docs/domain-rules.md"
    if os.path.isfile(document) and platform:
        args += ["--document", document, "--platform", platform]
    else:
        scope = "the whole rules corpus (this project has no docs/domain-rules.md yet)"
    result = run(args, cwd=root)
    try:
        report = json.loads(result.stdout)
        totals = report["totals"]
    except (ValueError, KeyError, TypeError):
        first = (result.stderr or result.stdout).strip().splitlines()
        return [f"rules held by a machine: unavailable ({first[0] if first else 'verify_rules.py printed nothing'})"], []
    if not totals.get("total"):
        return ["rules held by a machine: unavailable (no rule document was found to count)"], []
    review = [rule["title"] for doc in report["documents"] for rule in doc["rules"] if rule["category"] == "review"]
    line = (f"rules held by a machine: {totals['machine']} of {totals['total']} ({scope}) · partly {totals['partly']} "
            f"· advisory {totals['advisory']} · reviewer-judged {totals['review']} · process {totals['process']} "
            f"· open {totals['open']}")
    return [line], review


def ratchet_line(root):
    try:
        with open(os.path.join(root, RATCHET_BASELINE_FILE), encoding="utf-8") as handle:
            baselines = json.load(handle).get("baselines", [])
    except (OSError, ValueError):
        return f"ratchet baselines: none ({RATCHET_BASELINE_FILE} is absent) — every ratchet signature counts from 0"
    if not baselines:
        return "ratchet baselines: none listed — every ratchet signature counts from 0"
    parts = [f"{b.get('id')} {b.get('count')} (deadline {b.get('deadline')})" for b in baselines]
    return "ratchet baselines (the count may only fall; past the deadline the check blocks): " + "; ".join(parts)


def rules_at_start(event):
    root = repo_root(event) or event.get("cwd") or os.getcwd()
    checks = checks_dir(root)
    platform, project_type = platform_of(root)
    lines = ["Up Coast rules — what this session is held to:"]
    if platform:
        lines.append(f"platform: {platform}" + (f" · project type {project_type}" if project_type else "")
                     + f" (from {PLATFORM_FILE})")
    else:
        lines.append(f"platform: unknown — {PLATFORM_FILE} is missing and COAST_PLATFORM is unset; the scanner hooks "
                     "cannot run until one names the platform")
    if checks:
        number, review = rules_number(root, checks, platform)
        lines += number
        if review:
            lines.append(f"review-only rules ({len(review)}, a reviewer judges these — no machine holds them): "
                         + "; ".join(review))
    else:
        lines.append("rules held by a machine: unknown (no check_rules.py beside this hook or under Scripts/checks)")
    lines.append(ratchet_line(root))
    lines.append("session hooks that will refuse: edits to governing files, chained cd, infrastructure commands, "
                 "--no-verify, force pushes, a red scan at commit, and ending a turn with unpushed commits.")
    print("\n".join(lines))
    return PASS


HOOKS = {
    "governing-edit": governing_edit,
    "chained-cd": chained_cd,
    "infra-command": infra_command,
    "no-verify": no_verify,
    "force-push": force_push,
    "scan-at-commit": scan_at_commit,
    "scan-on-edit": scan_on_edit,
    "unpushed-at-stop": unpushed_at_stop,
    "rules-at-start": rules_at_start,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in HOOKS:
        sys.stderr.write("usage: claude-hook.py <hook-id>   one of: " + ", ".join(HOOKS) + "\n")
        return 1
    return HOOKS[argv[0]](read_event())


if __name__ == "__main__":
    sys.exit(main())
