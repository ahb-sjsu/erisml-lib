"""Fire tests for build.py's math protection.

Run: python tools/series-build/test_build_math.py
The first four cases fail on the builder as it was before 2026-11-25.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

CASES = [
    # (name, markdown, must contain, must not contain)
    ("wrapped inline math", "object is $\\mathbb{E}_x\n\\operatorname{tr}(P_C\\Sigma_\\delta)$, with $a_b$ and $c_d$.",
     ["$\\mathbb{E}_x\n\\operatorname{tr}(P_C\\Sigma_\\delta)$", "$a_b$", "$c_d$"], ["<em>"]),
    ("less-than in math", "Let $1\\le k<n$, $\\lambda>0$ hold.", ["$1\\le k&lt;n$", "$\\lambda&gt;0$"], ["<n$"]),
    ("currency outside math", "Pay \\$50. Then $\\Delta d_1 = -50$ follows.",
     ['<span class="currency">&#36;</span>50', "$\\Delta d_1 = -50$"], ["\\$50"]),
    ("currency inside math", "Cost $\\text{price }\\$5 + x_1$ here.", ["$\\text{price }\\$5 + x_1$"], ["currency"]),
    ("code is untouched", "```\necho \\$HOME $x_1$\n```\n", ["echo \\$HOME $x_1$"], ["currency"]),
    ("no pairing across a blank line", "A price of $5 here.\n\nAnother $x_1$ there.", ["$x_1$"], []),
]


def main() -> int:
    bad = 0
    for name, md, want, forbid in CASES:
        out = build.md_to_html(md)
        ok = all(w in out for w in want) and not any(f in out for f in forbid)
        bad += not ok
        print("PASS" if ok else "FAIL", name)
        if not ok:
            print("    got:", repr(out))
    print("failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
