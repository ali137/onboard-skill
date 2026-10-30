import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import format_check as fc  # noqa: E402

TITLES = fc.BRIEFING


GOOD = {"Where things stand": "Project: a CLI. Phase: 2.",
        "Limits": "decide alone: layout; ask the user before: scope; never touch: x."}
HEAD = "## Briefing: phase session, reports to the user. Solo session.\n\n"


def briefing(style="{n}. **{t}:** {body}", bodies=None, extra="", order=None):
    order = order or list(range(len(TITLES)))
    bodies = dict(GOOD, **(bodies or {}))
    rows = [style.format(n=i + 1, t=TITLES[i], body=bodies.get(TITLES[i], "something"))
            for i in order]
    return HEAD + "\n".join(rows) + "\n" + extra + "\nWaiting for go.\n"


def test_good_styles():
    for style in ["{n}. **{t}:** {body}", "**{n}. {t}:** {body}", "### {n}. {t}\n{body}",
                  "## {t}\n{body}", "**{t}:** {body}", "{t}: {body}", "**{t} (a note):** {body}"]:
        r = fc.check_briefing(briefing(style))
        assert r["ok"], (style, r)


def test_section_named_only_in_a_bullet_is_missing():
    text = briefing().replace("2. **Drift:** something", "- Drift none.")
    r = fc.check_briefing(text)
    assert r["missing_sections"] == ["Drift"] and not r["ok"]


def test_empty_out_of_order_and_too_long():
    assert fc.check_briefing(briefing(bodies={"Drift": ""}))["empty_sections"] == ["Drift"]
    swapped = list(range(len(TITLES)))
    swapped[0], swapped[-1] = swapped[-1], 0
    assert fc.check_briefing(briefing(order=swapped))["out_of_order"]
    long = briefing("### {n}. {t}\n{body}", extra="\n".join(f"paragraph {i}" for i in range(40)))
    r = fc.check_briefing(long)
    assert r["briefing_lines"] > fc.MAX_BRIEFING_LINES and not r["ok"]


def test_plan_after_the_briefing_is_not_counted():
    text = briefing(extra="\n**First reply**\n" + "\n".join(f"- plan {i}" for i in range(30)))
    r = fc.check_briefing(text)
    assert r["ok"] and r["briefing_lines"] == 8


def test_required_clauses():
    r = fc.check_briefing(briefing(bodies={"Where things stand": "Phase 2 is active.",
                                           "Limits": "Never touch x; ask before y."}))
    assert r["missing_clauses"] == ["Where things stand: project", "Limits: decide alone"]
    assert not r["ok"]
    # the heading must say who the newcomer reports to
    r = fc.check_briefing(briefing().replace(", reports to the user", ""))
    assert r["missing_clauses"] == ["heading: reports to"] and not r["ok"]
    # a clause on the section's next lines counts
    r = fc.check_briefing(briefing("### {n}. {t}\n{body}"))
    assert r["ok"] and not r["missing_clauses"], r


def test_note_and_role_card():
    note = "| Field | Content |\n|---|---|\n" + "\n".join(
        f"| **{f}** | <title> tag missing |" if f == "symptom" else f"| {f} | value |" for f in fc.NOTE)
    assert fc.check_note(note)["ok"]
    assert fc.check_note(note.replace("| fix | value |", "| fix | <what> |"))["empty_fields"] == ["fix"]
    card = "# x\n" + "".join(f"## {f}\nfilled\n" for f in fc.ROLE_CARD)
    assert fc.check_role_card(card)["ok"]
    assert fc.check_role_card(card.replace("## Goal\nfilled", "## Goal\n<goal>"))["empty_fields"] == ["Goal"]


def test_the_compact_briefing():
    """The compact briefing (phase 18) in the skill's own example form passes; phase 13's
    12-section form fails it (format_check_v1.py reads that one); a go given in the
    starting prompt ends the briefing instead of "Waiting for go."."""
    text = open(os.path.join(os.path.dirname(fc.__file__), "..", "onboard/references/join.md")).read()
    example = text.split("```\n## Briefing")[1].split("```")[0]
    r = fc.check_briefing("## Briefing" + example)
    assert r["ok"] and r["sections_found"] == 8, r
    old = HEAD + "\n".join(f"{i + 1}. **{t}:** x" for i, t in enumerate(
        ["Who I am", "Team", "Where things stand", "Settled decisions", "Claims checked",
         "Drift found", "Rule conflicts", "Matching experience notes", "My next task",
         "My limits", "Quick check", "Questions for the lead"])) + "\nWaiting for go.\n"
    assert not fc.check_briefing(old)["ok"]
    started = briefing().replace("Waiting for go.", "Go given in the starting prompt; starting.")
    r = fc.check_briefing(started + "\nNow fixing bakery/inventory.py.\n")
    assert r["ok"] and r["waiting_for_go"]
    assert not fc.check_briefing(briefing().replace("Waiting for go.", ""))["ok"]


def test_end_line_inside_a_section_does_not_end_the_briefing():
    """The end line counts only after the last section: a section that quotes it neither
    ends the briefing early nor stands in for the missing end line."""
    quoting = briefing(bodies={"Where things stand": "Project: a CLI. The lead's prompt says go "
                                                     "given in the starting prompt counts."})
    r = fc.check_briefing(quoting)
    assert r["ok"] and r["sections_found"] == 8 and r["briefing_lines"] == 8, r
    r = fc.check_briefing(quoting.replace("Waiting for go.", ""))
    assert not r["waiting_for_go"] and not r["ok"]
    inside = briefing("### {n}. {t}\n{body}", bodies={"Settled": "none\nWaiting for go."})
    r = fc.check_briefing(inside.removesuffix("\nWaiting for go.\n"))
    assert r["sections_found"] == 8 and not r["waiting_for_go"] and not r["ok"], r


def test_label_variants_and_collisions():
    """"Quick check" stands for Check; "reports to" may sit on the line under the heading;
    a numbered item that only starts with a label word is not a briefing line."""
    r = fc.check_briefing(briefing().replace("**Check:**", "**Quick check:**"))
    assert r["ok"], r
    r = fc.check_briefing(briefing().replace(", reports to the user. Solo session.",
                                             "\nReports to the user. Solo session."))
    assert r["ok"], r
    r = fc.check_briefing(briefing(bodies={"Drift": "1 drift\n1. Check command `make test` fails"}))
    assert r["ok"] and r["sections_found"] == 8, r
