import re

_MD_PROTECT_RE = re.compile(
    r"(?P<block>^[ \t]*(?P<fence>[~`]{3,})[ \t]*[^\n]*\n.*?(?:^[ \t]*(?P=fence)[ \t]*$|\Z))"
    r"|(?P<inline>(?P<bt>`+)[^`]+?(?P=bt))"
    r"|(?P<details><details\b(?![^>]*\bmarkdown\s*=)[^>]*>)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE
)

def repl(m: re.Match) -> str:
    if m.group("details"):
        return re.sub(r"(?i)^<details\b", '<details markdown="1"', m.group("details"), count=1)
    return m.group(0)

tests = [
    "<details>",
    "<details open>",
    "<details class='x'>",
    "<details markdown='1'>",
    "```\n<details>\n```",
    "~~~bash\n<details>\n~~~",
    "`<details>`",
    "`` <details> ``"
]

for t in tests:
    print(f"IN : {t!r}")
    print(f"OUT: {_MD_PROTECT_RE.sub(repl, t)!r}")
    print("---")
