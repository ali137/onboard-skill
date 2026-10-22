import json
import os
import subprocess
import sys

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(HARNESS, "snapshot.py")


def write(path, text, mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w" if isinstance(text, str) else "wb").write(text)
    if mode:
        os.chmod(path, mode)


def make_project(home):
    src = os.path.join(home, "projects", "demo.proj")
    forms = [src, "~/projects/demo.proj", "$HOME/projects/demo.proj", "${HOME}/projects/demo.proj"]
    write(f"{src}/CLAUDE.md", "Rules. Work in " + forms[1] + "/repo only.\n")
    write(f"{src}/PHASES.md", "| 1 | a | active |\nSee " + forms[2] + "/sessions and " + forms[3] + ".\n")
    write(f"{src}/.credentials.env", "PASSWORD=never-copied\n", 0o600)
    write(f"{src}/.gitignore", ".credentials.env\n")
    write(f"{src}/.mcp.json", '{"mcpServers": {}}')
    write(f"{src}/notes.txt", "not a root md file\n")
    write(f"{src}/sessions/PHASE-01.md", "prompt\n")
    write(f"{src}/prompts/INDEX.md", "prompts\n")
    write(f"{src}/.claude/settings.json",
          json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"command": forms[0] + "/.claude/hooks/h.sh"}]}]}}))
    write(f"{src}/.claude/hooks/h.sh", "#!/bin/sh\nproj=" + forms[0] + "\n", 0o755)
    write(f"{src}/.claude/skills/x/icon.png", b"\x89PNG\0\0binary")
    write(f"{src}/.claude/skills/x/.git/HEAD", "ref\n")
    write(f"{src}/design/a/NOTES.md", "the bare name demo.proj is fine in prose\n")
    write(f"{src}/design/a/render.py", "print(1)\n")
    write(f"{src}/repo/code.py", "x = 1\n")
    write(f"{src}/output/site.html", "<p>\n")
    os.symlink(f"{src}/CLAUDE.md", f"{src}/sessions/link.md")
    return src


def run(home, *args):
    env = dict(os.environ, HOME=home)
    return subprocess.run([sys.executable, "-I", SNAPSHOT, *args], env=env,
                          capture_output=True, text=True)


def all_files(root):
    return sorted(os.path.relpath(os.path.join(d, f), root)
                  for d, _, fs in os.walk(root) for f in fs)


def test_snapshot_rules(tmp_path):
    home = str(tmp_path / "home")
    src = make_project(home)
    before = {f: open(os.path.join(src, f), "rb").read() for f in all_files(src)}
    dest = str(tmp_path / "lab" / "snapshots" / "demo-2026-01-01")

    r = run(home, "--src", src, "--dest", dest)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "root *.md files: 2" in r.stdout

    assert all_files(dest) == [".claude/hooks/h.sh", ".claude/settings.json", ".gitignore",
                               ".mcp.json", "CLAUDE.md", "PHASES.md", "design/a/NOTES.md",
                               "prompts/INDEX.md", "sessions/PHASE-01.md"]
    text = "".join(open(os.path.join(dest, f)).read() for f in all_files(dest))
    for form in ["/projects/demo.proj"]:
        assert form not in text
    assert dest + "/repo only" in text and dest + "/sessions" in text
    assert "the bare name demo.proj is fine" in text
    assert os.access(os.path.join(dest, ".claude/hooks/h.sh"), os.X_OK)
    for d, dirs, fs in os.walk(dest):
        for n in [d] + [os.path.join(d, f) for f in fs]:
            assert os.stat(n).st_mode & 0o222 == 0, n

    m = json.load(open(dest + ".manifest.json"))
    assert m["skipped"]["secret"] == [".credentials.env"]
    assert m["skipped"]["image"] == [".claude/skills/x/icon.png"]
    assert m["skipped"]["symlink"] == ["sessions/link.md"]
    assert m["paths_rewritten"] == 5

    # the source is unchanged
    assert {f: open(os.path.join(src, f), "rb").read() for f in all_files(src)} == before
    assert run(home, "--src", src, "--verify", dest).returncode == 0


def test_refuses_existing_or_inner_dest(tmp_path):
    home = str(tmp_path / "home")
    src = make_project(home)
    assert run(home, "--src", src, "--dest", f"{src}/snap").returncode != 0
    assert not os.path.exists(f"{src}/snap")
    os.makedirs(tmp_path / "exists")
    assert run(home, "--src", src, "--dest", str(tmp_path / "exists")).returncode != 0


def test_verify_catches_leftovers(tmp_path):
    home = str(tmp_path / "home")
    src = make_project(home)
    bad = tmp_path / "bad"
    write(str(bad / "a.md"), "cd ${HOME}/projects/demo.proj\n")
    write(str(bad / ".credentials.env"), "x\n")
    r = run(home, "--src", src, "--verify", str(bad))
    assert r.returncode == 1
    assert "path to the source (${HOME}/projects/demo.proj): a.md" in r.stdout
    assert "secret file name: .credentials.env" in r.stdout
    assert "writable: a.md" in r.stdout


def test_review_cases(tmp_path):
    """Quoted $HOME form, a hard link to a secret, a FIFO, a missing .claude."""
    home = str(tmp_path / "home")
    src = make_project(home)
    write(f"{src}/.claude/hooks/q.sh", 'cd "$HOME"/projects/demo.proj && cd "${HOME}"/projects/demo.proj\n')
    os.link(f"{src}/.credentials.env", f"{src}/sessions/notes.md")
    os.mkfifo(f"{src}/sessions/pipe")
    dest = str(tmp_path / "snap")
    r = run(home, "--src", src, "--dest", dest)
    assert r.returncode == 0, r.stdout + r.stderr
    assert open(f"{dest}/.claude/hooks/q.sh").read() == f"cd {dest} && cd {dest}\n"
    m = json.load(open(dest + ".manifest.json"))
    assert m["skipped"]["hardlink to a secret"] == ["sessions/notes.md"]
    assert m["skipped"]["not a regular file"] == ["sessions/pipe"]
    assert not os.path.exists(f"{dest}/sessions/notes.md")

    os.rename(f"{src}/.claude", f"{src}/claude-moved")
    r = run(home, "--src", src, "--dest", str(tmp_path / "snap2"))
    assert r.returncode == 1 and "folder not copied (missing): .claude" in r.stdout


def test_catch_all_tail(tmp_path):
    """A form the rewrite does not know still fails the check."""
    home = str(tmp_path / "home")
    src = make_project(home)
    bad = tmp_path / "bad"
    write(str(bad / "a.md"), "see ~someone/projects/demo.proj/x\n")
    os.chmod(bad / "a.md", 0o444)
    os.chmod(bad, 0o555)
    r = run(home, "--src", src, "--verify", str(bad))
    assert r.returncode == 1 and "path to the source (/projects/demo.proj): a.md" in r.stdout
