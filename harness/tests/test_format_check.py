import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import format_check as fc  # noqa: E402

TITLES = fc.BRIEFING


def briefing(style="{n}. **{t}:** {body}", bodies=None, extra="", order=None):
    order = order or list(range(len(TITLES)))
    rows = [style.format(n=i + 1, t=TITLES[i], body=(bodies or {}).get(TITLES[i], "something"))
            for i in order]
    return "## Briefing\n\n" + "\n".join(rows) + "\n" + extra + "\nWaiting for go.\n"


def test_good_styles():
    for style in ["{n}. **{t}:** {body}", "**{n}. {t}:** {body}", "### {n}. {t}\n{body}",
                  "## {t}\n{body}", "**{t}:** {body}"]:
        r = fc.check_briefing(briefing(style))
        assert r["ok"], (style, r)


def test_section_named_only_in_a_bullet_is_missing():
    text = briefing().replace("2. **Team:** something", "- Team folder absent.")
    r = fc.check_briefing(text)
    assert r["missing_sections"] == ["Team"] and not r["ok"]


def test_empty_out_of_order_and_too_long():
    assert fc.check_briefing(briefing(bodies={"Drift found": ""}))["empty_sections"] == ["Drift found"]
    swapped = list(range(10))
    swapped[0], swapped[9] = 9, 0
    assert fc.check_briefing(briefing(order=swapped))["out_of_order"]
    long = briefing("### {n}. {t}\n{body}", extra="\n".join(f"paragraph {i}" for i in range(40)))
    r = fc.check_briefing(long)
    assert r["briefing_lines"] > 40 and not r["ok"]


def test_plan_after_the_briefing_is_not_counted():
    text = briefing(extra="\n**First reply**\n" + "\n".join(f"- plan {i}" for i in range(30)))
    r = fc.check_briefing(text)
    assert r["ok"] and r["briefing_lines"] == 10


def test_note_and_role_card():
    note = "| Field | Content |\n|---|---|\n" + "\n".join(
        f"| **{f}** | <title> tag missing |" if f == "symptom" else f"| {f} | value |" for f in fc.NOTE)
    assert fc.check_note(note)["ok"]
    assert fc.check_note(note.replace("| fix | value |", "| fix | <what> |"))["empty_fields"] == ["fix"]
    card = "# x\n" + "".join(f"## {f}\nfilled\n" for f in fc.ROLE_CARD)
    assert fc.check_role_card(card)["ok"]
    assert fc.check_role_card(card.replace("## Goal\nfilled", "## Goal\n<goal>"))["empty_fields"] == ["Goal"]
