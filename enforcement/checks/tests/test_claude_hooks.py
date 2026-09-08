"""Tests for claude-hook.py and claude-settings.json (enforcement task E2.1).

Every hook is fed the stdin JSON Anthropic documents for its event
(https://code.claude.com/docs/en/hooks — quoted in claude-hook.py) through a
real subprocess inside a throwaway git repository with a bare "origin" under
the same tempdir, never a real remote. Each test asserts the exit code (0
passes, 2 refuses) and the sentence on stderr. The last class proves the
settings file parses and names every hook id the rule documents demand.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
HOOKS_DIR = os.path.join(REPO_ROOT, "enforcement", "hooks")
HOOK = os.path.join(HOOKS_DIR, "claude-hook.py")
SETTINGS = os.path.join(HOOKS_DIR, "claude-settings.json")
IOS_RULES = os.path.join(REPO_ROOT, "rules", "platform", "domain-rules-ios.md")
sys.path.insert(0, CHECKS_DIR)

import verify_rules as vr  # noqa: E402

# The ids verify_rules demands that belong to the commit-msg git hook (E2.2, another owner), not to this file.
COMMIT_MSG_HOOK_IDS = {"attribution-trailer"}

LITERAL_VIEW = 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("Save your changes now") } }\n'
CLEAN_VIEW = 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("home.title") } }\n'


def sh(cwd, *args):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=git_env())
    if result.returncode != 0:
        raise RuntimeError(f"{args} failed:\n{result.stderr}")
    return result.stdout.strip()


# A git hook hands its children GIT_DIR and GIT_INDEX_FILE (always, in a linked worktree); a fixture
# that inherited them would run its git commands against THIS repository. Every subprocess here gets
# an environment without them and without COAST_PLATFORM (the fixture's .coast/platform must decide).
GIT_REDIRECT_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                          "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_NAMESPACE", "COAST_PLATFORM")


def git_env():
    env = {key: value for key, value in os.environ.items() if key not in GIT_REDIRECT_VARIABLES}
    env.update(GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@x")
    return env


class Repo:
    """A throwaway iOS-shaped repository with a bare origin beside it, pushed and clean."""

    def __init__(self, platform="ios", with_origin=True):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "work")
        self.origin = os.path.join(self.dir.name, "origin.git")
        os.makedirs(self.path)
        sh(self.path, "git", "init", "-q", "-b", "main")
        if platform:
            self.write(".coast/platform", f"{platform} A\n")
        self.write("Package.swift", "// swift-tools-version:6.0\n")
        self.write("Sources/App/App.swift", "import SwiftUI\n@main struct App {}\n")
        self.commit("start")
        if with_origin:
            sh(self.dir.name, "git", "init", "-q", "--bare", "-b", "main", self.origin)
            sh(self.path, "git", "remote", "add", "origin", self.origin)
            sh(self.path, "git", "push", "-q", "-u", "origin", "main")

    def write(self, relative, content):
        full = os.path.join(self.path, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content)
        return full

    def stage(self, relative, content):
        self.write(relative, content)
        sh(self.path, "git", "add", relative)

    def commit(self, message):
        sh(self.path, "git", "add", "-A")
        sh(self.path, "git", "commit", "-q", "-m", message)

    def push(self):
        sh(self.path, "git", "push", "-q", "origin", "main")

    def hook(self, hook_id, event, hook=HOOK):
        payload = {"session_id": "test", "transcript_path": "/dev/null", "cwd": self.path, "permission_mode": "default"}
        payload.update(event)
        return subprocess.run([sys.executable, hook, hook_id], input=json.dumps(payload), cwd=self.path,
                              capture_output=True, text=True, env=git_env())

    def pre_tool(self, hook_id, tool_name, **tool_input):
        return self.hook(hook_id, {"hook_event_name": "PreToolUse", "tool_name": tool_name,
                                   "tool_input": tool_input, "tool_use_id": "toolu_test"})

    def bash(self, hook_id, command):
        return self.pre_tool(hook_id, "Bash", command=command, description="test")

    def cleanup(self):
        self.dir.cleanup()


class HookCase(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def assertRefused(self, result, *sentences):
        self.assertEqual(result.returncode, 2, f"expected a refusal, got exit {result.returncode}:\n{result.stdout}\n{result.stderr}")
        for sentence in sentences:
            self.assertIn(sentence, result.stderr)

    def assertPassed(self, result):
        self.assertEqual(result.returncode, 0, f"expected a pass, got exit {result.returncode}:\n{result.stdout}\n{result.stderr}")


class BashCase(HookCase):
    """The Bash refusals read only the command, so one repo serves the whole class."""

    @classmethod
    def setUpClass(cls):
        cls.shared = Repo()

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.repo = self.shared


# ---------------------------------------------------------------- governing-edit


class GoverningEdit(HookCase):
    def edit(self, relative, tool="Edit"):
        path = os.path.join(self.repo.path, relative)
        field = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return self.repo.pre_tool("governing-edit", tool, **{field: path, "old_string": "a", "new_string": "b"})

    def test_git_hook_is_refused(self):
        self.assertRefused(self.edit(".githooks/pre-push"), ".githooks/pre-push", "governing file",
                           "never edit the files that define their own checks")

    def test_product_source_passes(self):
        self.assertPassed(self.edit("Sources/App/HomeView.swift"))
        self.assertPassed(self.edit("Sources/App/HomeView.swift", tool="Write"))

    def test_every_governing_class_is_refused(self):
        for relative in (".claude/settings.json", ".claude/settings.local.json", "Scripts/checks/check_rules.py",
                         "Scripts/hooks/claude-hook.py",
                         "docs/domain-rules.md", "docs/ai-features-rules.md", ".swiftlint.yml", ".swift-format",
                         ".github/workflows/ci.yml", ".coast/ratchet-baseline.json", ".coast/platform"):
            with self.subTest(path=relative):
                self.assertRefused(self.edit(relative), relative)

    def test_notebook_edit_reads_notebook_path(self):
        self.assertRefused(self.edit("Scripts/checks/notes.ipynb", tool="NotebookEdit"), "Scripts/checks/notes.ipynb")

    def test_path_outside_the_repo_passes(self):
        outside = os.path.join(self.repo.dir.name, "elsewhere", ".githooks", "pre-push")
        result = self.repo.pre_tool("governing-edit", "Edit", file_path=outside, old_string="a", new_string="b")
        self.assertPassed(result)

    def test_unknown_platform_still_refuses_every_platforms_governing_paths(self):
        os.remove(os.path.join(self.repo.path, ".coast", "platform"))
        self.assertRefused(self.edit("detekt.yml"), "detekt.yml")
        self.assertRefused(self.edit("eslint.config.mjs"), "eslint.config.mjs")
        self.assertPassed(self.edit("Sources/App/HomeView.swift"))


# ---------------------------------------------------------------- the Bash refusals


class ChainedCd(BashCase):
    def test_and_chain_is_refused(self):
        self.assertRefused(self.repo.bash("chained-cd", "cd /tmp/x && ls"), "chained-cd", "atomic command")

    def test_semicolon_chain_is_refused(self):
        self.assertRefused(self.repo.bash("chained-cd", "cd /tmp/x; git status"), "chained-cd")

    def test_cd_line_followed_by_more_is_refused(self):
        self.assertRefused(self.repo.bash("chained-cd", "cd /tmp/x\nswift test"), "chained-cd")

    def test_subshell_chain_is_refused(self):
        self.assertRefused(self.repo.bash("chained-cd", "(cd /tmp/x && make)"), "chained-cd")

    def test_bare_cd_and_absolute_paths_pass(self):
        self.assertPassed(self.repo.bash("chained-cd", "cd /tmp/x"))
        self.assertPassed(self.repo.bash("chained-cd", "git -C /tmp/x status && ls /tmp/x"))
        self.assertPassed(self.repo.bash("chained-cd", "ls && cd /tmp/x"))
        self.assertPassed(self.repo.bash("chained-cd", 'echo "cd /tmp/x && make"'))
        self.assertPassed(self.repo.bash("chained-cd", "git commit -m 'cd into the new folder; then build'"))

    def test_the_other_spellings_of_a_chain_are_refused(self):
        # E2.8: `if cd X; then`, `pushd`, `builtin cd`, a `cd` inside `sh -c`, `cd X || exit` all passed before.
        for command in ("if cd /tmp/x; then make; fi", "pushd /tmp/x && make", "builtin cd /tmp/x && make",
                        "command cd /tmp/x; make", 'sh -c "cd /tmp/x && make"', "cd /tmp/x || exit 1; make",
                        "cd /tmp/x \\\n  && make", "{ cd /tmp/x; make; }", "$(cd /tmp/x && pwd)"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("chained-cd", command), "chained-cd")


class InfraCommand(BashCase):
    def test_infrastructure_programs_are_refused(self):
        for command in ("fly deploy", "flyctl volumes destroy vol_1", "wrangler deploy", "terraform apply",
                        "pulumi up", "doctl compute droplet delete 1", "aws s3 rb s3://bucket", "gcloud run deploy",
                        "az group delete", "nsupdate -k key.private", "sudo terraform destroy",
                        "npm test && fly deploy"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("infra-command", command),
                                   "this changes infrastructure — ask the owner in one line first")

    def test_gh_infrastructure_verbs_are_refused(self):
        for command in ("gh repo delete Up-Coast/coast --yes", "gh secret set ANTHROPIC_API_KEY", "gh ruleset list",
                        "gh api -X DELETE repos/o/r/rulesets/1", "gh api --method PUT repos/o/r/actions/secrets/KEY",
                        "gh api -X PATCH repos/o/r -f default_branch=main", "gh api repos/o/r/hooks -f url=https://x",
                        "gh api -X POST user/repos -f name=new"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("infra-command", command), "ask the owner in one line first")

    def test_reads_and_ordinary_work_pass(self):
        for command in ("git status", "gh pr create --title x", "gh api repos/o/r", "gh api repos/o/r/rulesets",
                        "gh api -X POST repos/o/r/issues -f title=bug", "gh repo create Up-Coast/new --private",
                        "dig example.com", "nslookup example.com", "echo fly", "awsome-tool run",
                        'echo "fly deploy is refused"', "git commit -m 'terraform apply notes'"):
            with self.subTest(command=command):
                self.assertPassed(self.repo.bash("infra-command", command))

    def test_read_only_forms_of_the_infrastructure_programs_pass(self):
        # E2.8: the sentence says read-only checks are fine; the hook now agrees.
        for command in ("fly status", "fly status -a my-app", "fly -a my-app logs", "flyctl machines list",
                        "fly apps list", "fly releases", "fly secrets list", "fly scale show", "fly checks list",
                        "fly config show", "fly auth whoami", "fly version", "fly --version",
                        "aws s3 ls", "aws s3 ls s3://bucket/", "aws sts get-caller-identity",
                        "aws ec2 describe-instances --region us-east-1", "aws logs tail /aws/lambda/fn",
                        "terraform plan", "terraform plan -destroy -out=plan.out", "terraform show", "terraform validate",
                        "terraform output -json", "terraform state list", "terraform workspace list", "tofu plan",
                        "pulumi preview", "pulumi stack ls", "pulumi whoami", "gcloud run services list",
                        "gcloud config list", "gcloud auth list", "az group list", "az account show",
                        "doctl compute droplet list", "doctl account get", "wrangler whoami",
                        "wrangler deployments list", "wrangler kv namespace list", "wrangler tail",
                        "cloudflared tunnel list", "cloudflared tunnel info x", "cloudflared --version",
                        "npm test && fly status"):
            with self.subTest(command=command):
                self.assertPassed(self.repo.bash("infra-command", command))

    def test_a_read_only_word_beside_a_mutating_verb_does_not_excuse_it(self):
        for command in ("fly apps destroy status", "terraform state rm module.x", "aws s3 cp file s3://bucket/list",
                        "fly scale count 2", "fly secrets set KEY=1", "gcloud run services delete x",
                        "wrangler versions upload", "wrangler kv key put k v", "pulumi config set k v",
                        "terraform workspace new prod", "nsupdate -v", "fly machine run image", "cloudflared tunnel run x"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("infra-command", command), "ask the owner in one line first")


class BashBypasses(BashCase):
    """E2.8: every route around the Bash rules that passed before. Each is refused by the hook it evades."""

    def test_force_push_bypasses_are_refused(self):
        for command in ('sh -c "git push --force"', "bash -lc 'git push -f origin main'", "zsh -c 'git push --force'",
                        "git push origin main \\\n  --force", "A=1 B=2 git push -f", "env -i git push --force",
                        "env A=1 B=2 git push -f", "xargs git push -f", "echo main | xargs -n1 git push -f origin",
                        "timeout 30 git push --force", "nice -n 10 git push -f", "sudo -u me git push -f",
                        "{ git push --force; }", "(git push --force)", "$(git push --force)", "`git push --force`",
                        'echo "$(git push --force)"', "eval 'git push --force'", "command git push -f",
                        "builtin cd /tmp/x || git push -f", "if true; then git push -f; fi",
                        "for b in main; do git push -f origin $b; done", "sleep 1 & git push -f",
                        "true |& git push -f", "find . -name x -exec git push -f {} \\;",
                        'sh -c "sh -c \'git push --force\'"'):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("force-push", command), "force-push")

    def test_no_verify_bypasses_are_refused(self):
        for command in ('sh -c "git commit -m x --no-verify"', "A=1 B=2 git commit -n -m x", "env -i git commit --no-verify -m x",
                        "git commit -m x \\\n  --no-verify", "$(git commit --no-verify -m x)",
                        "{ git commit -n -m x; }", "xargs git commit --no-verify -m"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("no-verify", command), "no-verify")

    def test_infra_bypasses_are_refused(self):
        for command in ('sh -c "fly deploy"', "bash -c 'terraform apply -auto-approve'", "A=1 B=2 fly deploy",
                        "env -i fly deploy", "env FLY_API_TOKEN=x fly deploy", "xargs fly deploy",
                        "{ fly deploy; }", "(fly deploy)", "$(fly deploy)", "`fly deploy`", "npx wrangler deploy",
                        "pnpm dlx wrangler deploy", "bunx wrangler deploy", "yarn dlx wrangler deploy",
                        "npm exec wrangler deploy", "npx -y wrangler@3 deploy", "npx -p wrangler wrangler deploy",
                        "timeout 300 fly deploy", "nohup fly deploy", "sudo -u deploy fly deploy",
                        "fly \\\n  deploy", "eval fly deploy", "if true; then fly deploy; fi",
                        "while true; do terraform apply; done", "find . -exec aws s3 rb s3://b \\;",
                        "true & fly deploy", "true |& fly deploy", "/usr/local/bin/fly deploy"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("infra-command", command), "ask the owner in one line first")

    def test_a_commit_inside_a_wrapper_is_still_scanned(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        repo.stage("Sources/App/HomeView.swift", LITERAL_VIEW)
        for command in ('sh -c "git commit -m x"', "A=1 git commit -m x", "$(git commit -m x)"):
            with self.subTest(command=command):
                self.assertRefused(repo.bash("scan-at-commit", command), "the scanner refuses this commit")


class NoVerify(BashCase):
    def test_no_verify_anywhere_in_a_git_command_is_refused(self):
        for command in ("git commit --no-verify -m x", "git push --no-verify origin main",
                        "git add -A && git commit -m x --no-verify", "git commit -n -m x", "git commit -anm x",
                        "git -c core.hooksPath=/dev/null commit -m x",
                        # the same switch by other routes: git's keys are case-insensitive, long options
                        # take any unique prefix, and `git config` can point the hooks elsewhere or unset them
                        "git -c core.hookspath=/dev/null commit -m x", "git commit --no-verif -m x",
                        "git config core.hooksPath /dev/null", "git config --unset core.hookspath"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("no-verify", command), "no-verify", "the hooks are the gate")

    def test_ordinary_git_passes(self):
        for command in ("git commit -m x", "git push origin main", "git log -n 5", "echo --no-verify"):
            with self.subTest(command=command):
                self.assertPassed(self.repo.bash("no-verify", command))


class ForcePush(BashCase):
    def test_every_force_spelling_is_refused(self):
        for command in ("git push --force", "git push -f origin main", "git push --force-with-lease origin main",
                        "git push --force-with-lease=main:abc", "git push --force-if-includes", "git push -fu origin main",
                        "git push origin +main", "git -C /tmp/x push --force"):
            with self.subTest(command=command):
                self.assertRefused(self.repo.bash("force-push", command), "force-push", "rewrites history")

    def test_ordinary_push_passes(self):
        for command in ("git push", "git push -u origin main", "git push origin main:main", "git fetch --force"):
            with self.subTest(command=command):
                self.assertPassed(self.repo.bash("force-push", command))


# ---------------------------------------------------------------- the scanner hooks


class ScanAtCommit(HookCase):
    def test_a_planted_literal_in_a_staged_view_blocks_the_commit(self):
        self.repo.stage("Sources/App/HomeView.swift", LITERAL_VIEW)
        result = self.repo.bash("scan-at-commit", 'git commit -m "add home"')
        self.assertRefused(result, "ui-string-literal", "Sources/App/HomeView.swift", "the scanner refuses this commit")

    def test_a_clean_staged_view_passes(self):
        self.repo.stage("Sources/App/HomeView.swift", CLEAN_VIEW)
        self.assertPassed(self.repo.bash("scan-at-commit", 'git commit -m "add home"'))

    def test_a_commit_pointed_at_another_repository_is_not_scanned_here(self):
        # The planted literal is staged HERE; a `git -C <elsewhere> commit` is that repository's business.
        self.repo.stage("Sources/App/HomeView.swift", LITERAL_VIEW)
        elsewhere = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, elsewhere, True)
        subprocess.run(["git", "init", "-q", elsewhere], check=True)
        self.assertPassed(self.repo.bash("scan-at-commit", f'git -C {elsewhere} commit -m "over there"'))
        result = self.repo.bash("scan-at-commit", 'git commit -m "here"')
        self.assertEqual(result.returncode, 2, "the same planted literal still refuses a commit in this repository")

    def test_a_command_that_is_not_a_commit_is_not_scanned(self):
        self.repo.stage("Sources/App/HomeView.swift", LITERAL_VIEW)
        self.assertPassed(self.repo.bash("scan-at-commit", "git status"))
        self.assertPassed(self.repo.bash("scan-at-commit", "git commitment-check"))

    def test_unknown_platform_passes_with_a_note(self):
        os.remove(os.path.join(self.repo.path, ".coast", "platform"))
        self.repo.stage("Sources/App/HomeView.swift", LITERAL_VIEW)
        result = self.repo.bash("scan-at-commit", "git commit -m x")
        self.assertPassed(result)
        self.assertIn("platform is not known", result.stderr)


class ScanOnEdit(HookCase):
    def post_edit(self, relative):
        path = os.path.join(self.repo.path, relative)
        return self.repo.hook("scan-on-edit", {"hook_event_name": "PostToolUse", "tool_name": "Write",
                                               "tool_input": {"file_path": path, "content": "..."},
                                               "tool_response": {"filePath": path, "success": True},
                                               "tool_use_id": "toolu_test"})

    def test_findings_reach_stderr_with_exit_2(self):
        self.repo.write("Sources/App/HomeView.swift", LITERAL_VIEW)
        result = self.post_edit("Sources/App/HomeView.swift")
        self.assertRefused(result, "ui-string-literal", "scan-on-edit", "nothing was blocked")

    def test_a_clean_file_passes(self):
        self.repo.write("Sources/App/HomeView.swift", CLEAN_VIEW)
        self.assertPassed(self.post_edit("Sources/App/HomeView.swift"))

    def test_a_path_outside_the_repo_or_missing_passes(self):
        outside = os.path.join(self.repo.dir.name, "HomeView.swift")
        with open(outside, "w", encoding="utf-8") as handle:
            handle.write(LITERAL_VIEW)
        result = self.repo.hook("scan-on-edit", {"hook_event_name": "PostToolUse", "tool_name": "Write",
                                                 "tool_input": {"file_path": outside}, "tool_response": {}})
        self.assertPassed(result)
        self.assertPassed(self.post_edit("Sources/App/Missing.swift"))

    def test_installed_layout_resolves_the_checks_under_scripts(self):
        """The hook copied into a project (no ../checks beside it) finds Scripts/checks/."""
        installed = os.path.join(self.repo.path, "Scripts", "hooks", "claude-hook.py")
        os.makedirs(os.path.dirname(installed))
        shutil.copy(HOOK, installed)
        shutil.copytree(CHECKS_DIR, os.path.join(self.repo.path, "Scripts", "checks"),
                        ignore=shutil.ignore_patterns("tests", "__pycache__"))
        self.repo.write("Sources/App/HomeView.swift", LITERAL_VIEW)
        path = os.path.join(self.repo.path, "Sources/App/HomeView.swift")
        result = self.repo.hook("scan-on-edit", {"hook_event_name": "PostToolUse", "tool_name": "Write",
                                                 "tool_input": {"file_path": path}, "tool_response": {}}, hook=installed)
        self.assertRefused(result, "ui-string-literal")


# ---------------------------------------------------------------- unpushed-at-stop


class UnpushedAtStop(HookCase):
    def stop(self, active=False):
        return self.repo.hook("unpushed-at-stop", {"hook_event_name": "Stop", "stop_hook_active": active,
                                                   "last_assistant_message": "done", "background_tasks": [],
                                                   "session_crons": []})

    def test_pushed_and_clean_passes(self):
        self.assertPassed(self.stop())

    def test_an_unpushed_commit_blocks_until_it_is_pushed(self):
        self.repo.write("Sources/App/HomeView.swift", CLEAN_VIEW)
        self.repo.commit("home")
        self.assertRefused(self.stop(), "push before finishing", "1 commit(s) are not on origin/main")
        self.repo.push()
        self.assertPassed(self.stop())

    def test_stop_hook_active_never_blocks(self):
        self.repo.write("Sources/App/HomeView.swift", CLEAN_VIEW)
        self.repo.commit("home")
        self.assertPassed(self.stop(active=True))

    def test_dirty_product_source_blocks_and_docs_only_changes_do_not(self):
        self.repo.write("docs/notes.md", "notes\n")
        self.assertPassed(self.stop())
        self.repo.write("Sources/App/HomeView.swift", CLEAN_VIEW)
        self.assertRefused(self.stop(), "push before finishing", "uncommitted changes to product source: Sources/App/HomeView.swift")

    def test_no_upstream_passes_with_a_note(self):
        repo = Repo(with_origin=False)
        self.addCleanup(repo.cleanup)
        result = repo.hook("unpushed-at-stop", {"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no upstream", result.stdout)


# ---------------------------------------------------------------- rules-at-start


class RulesAtStart(HookCase):
    def start(self):
        return self.repo.hook("rules-at-start", {"hook_event_name": "SessionStart", "source": "startup"})

    def test_prints_the_projects_number_review_list_and_ratchets(self):
        shutil.copy(IOS_RULES, self.repo.write("docs/domain-rules.md", ""))
        self.repo.write(".coast/ratchet-baseline.json", json.dumps({"baselines": [
            {"id": "inline-comment", "count": 12, "deadline": "2026-12-01"}]}))
        result = self.start()
        self.assertPassed(result)
        self.assertIn("platform: ios · project type A", result.stdout)
        self.assertRegex(result.stdout, r"rules enforced by a check: \d+ of \d+ \(this project's docs/domain-rules.md\)")
        self.assertIn("review-only rules (", result.stdout)
        self.assertIn("inline-comment 12 (deadline 2026-12-01)", result.stdout)
        self.assertIn("session hooks that will refuse", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_without_a_rules_document_it_falls_back_to_the_corpus_total(self):
        result = self.start()
        self.assertPassed(result)
        self.assertIn("(the whole rules corpus", result.stdout)
        self.assertIn("ratchet baselines: none", result.stdout)

    def test_unknown_platform_is_said_plainly(self):
        os.remove(os.path.join(self.repo.path, ".coast", "platform"))
        result = self.start()
        self.assertPassed(result)
        self.assertIn("platform: unknown", result.stdout)


# ---------------------------------------------------------------- the settings file and the ids


class SettingsFile(unittest.TestCase):
    def test_settings_parse_and_use_the_documented_schema(self):
        with open(SETTINGS, encoding="utf-8") as handle:
            settings = json.load(handle)
        self.assertEqual(set(settings), {"_comment", "disableAllHooks", "permissions", "hooks"})
        events = settings["hooks"]
        self.assertEqual(set(events), {"PreToolUse", "PostToolUse", "Stop", "SessionStart"})
        for event, groups in events.items():
            for group in groups:
                for entry in group["hooks"]:
                    self.assertEqual(entry["type"], "command")
                    self.assertIn("claude-hook.py", entry["command"])
                    self.assertTrue(set(entry) <= {"type", "command", "if", "timeout", "statusMessage"}, entry)

    def test_the_permission_layer_uses_the_documented_syntax(self):
        """E2.8. The permissions page: a Bash rule is `Bash(<text>)` where `*` matches any text; an Edit deny
        rule is `Edit(<path>)`; `disableAllHooks: false` in the project file overrides a user `true`."""
        with open(SETTINGS, encoding="utf-8") as handle:
            settings = json.load(handle)
        self.assertIs(settings["disableAllHooks"], False)
        self.assertEqual(set(settings["permissions"]), {"deny"}, "the template denies; allow and ask are the founder's")
        deny = settings["permissions"]["deny"]
        self.assertEqual(len(deny), len(set(deny)), "no rule twice")
        for rule in deny:
            with self.subTest(rule=rule):
                self.assertRegex(rule, r"^(Bash|Edit)\([^()]+\)$")
                self.assertNotRegex(rule, r"^Bash\([a-z]+( \*)?\)$", "a whole program is never denied: read-only forms stay open")
                self.assertNotIn(":*", rule, "the space form `Bash(x *)`, which the permission dialog itself writes")
                self.assertFalse(rule.startswith("Bash(*"), "the `*` never stands in for the program")
        for expected in ("Bash(git push --force*)", "Bash(git push * -f)", "Bash(git * --no-verify)", "Bash(fly deploy*)",
                         "Bash(terraform apply*)", "Bash(aws s3 rb*)", "Bash(gh repo delete*)", "Bash(nsupdate*)",
                         "Edit(./.claude/settings.json)", "Edit(./.claude/settings.local.json)", "Edit(./Scripts/checks/**)"):
            self.assertIn(expected, deny)
        for program in ("fly", "flyctl", "wrangler", "cloudflared", "terraform", "tofu", "pulumi", "doctl", "aws", "gcloud", "az"):
            self.assertTrue(any(rule.startswith(f"Bash({program} ") for rule in deny), f"{program} has a deny rule")

    def test_settings_name_every_hook_id_the_rules_demand_and_the_hook_implements(self):
        with open(SETTINGS, encoding="utf-8") as handle:
            settings = json.load(handle)
        with open(HOOK, encoding="utf-8") as handle:
            hook_text = handle.read()
        wired = {entry["command"].rsplit(" ", 1)[-1] for groups in settings["hooks"].values()
                 for group in groups for entry in group["hooks"]}
        report = vr.run(REPO_ROOT, os.path.join(CHECKS_DIR, "battery.json"), None, None)
        demanded = {check.split(":", 1)[1] for doc in report["documents"] for rule in doc["rules"]
                    for check in rule["checks"] if check.startswith("session:")}
        self.assertTrue(demanded, "the corpus names no session hook — the test would prove nothing")
        for hook_id in demanded - COMMIT_MSG_HOOK_IDS:
            with self.subTest(hook_id=hook_id):
                self.assertIn(hook_id, wired)
                self.assertIn(f'"{hook_id}"', hook_text)
        with open(SETTINGS, encoding="utf-8") as handle:
            settings_text = handle.read()
        for hook_id in COMMIT_MSG_HOOK_IDS:
            self.assertNotIn(hook_id, settings_text, "a commit-msg id must not resolve against this file")
        usage = subprocess.run([sys.executable, HOOK], capture_output=True, text=True).stderr
        implemented = set(usage.split("one of: ")[1].strip().split(", "))
        self.assertEqual(implemented, {"governing-edit", "chained-cd", "infra-command", "no-verify", "force-push",
                                       "scan-at-commit", "scan-on-edit", "unpushed-at-stop", "rules-at-start"})
        self.assertEqual(wired, implemented)

if __name__ == "__main__":
    unittest.main()
