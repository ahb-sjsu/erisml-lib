#!/usr/bin/env python3
"""
series_check.py — mechanical proofreading + machine checks for a Geometric
Series volume (Markdown sources and, optionally, the built HTML).

It is deliberately conservative: everything it reports is either a hard
defect (undecodable bytes, unbalanced math, KaTeX parse failure, dangling
cross-reference, failing code block, broken internal link) or a *candidate*
flagged for a human/LLM proofreader (duplicate words, doubled punctuation,
spelling candidates, placeholders).

Checks
  encoding      strict UTF-8, U+FFFD, C1 controls, classic mojibake sequences
  structure     one H1 per file; "Chapter N" in H1 vs file order; heading jumps;
                section numbers N.M consistent with the chapter number
  math          unbalanced $ / $$ / \\begin-\\end; every snippet parsed by KaTeX
  xrefs         "Chapter/Section/Figure/Table/Theorem/Definition/Lemma/
                Proposition/Corollary/Equation/Appendix" references with no target
  prose         duplicate words, doubled punctuation, space before punctuation,
                unbalanced brackets per paragraph, placeholders (TODO, TBD, ...)
  spelling      codespell (if installed) + rare-token candidates (pyspellchecker)
  code          fenced python blocks executed in isolation (--run-code)
  links         relative links resolve; external URLs (--check-links) answer < 400
  build         build.py succeeds; built pages parse; internal hrefs resolve;
                every source page is listed in index.html

Usage (from the volume repo root):
    python .build/series_check.py                       # report to .build/reports/
    python .build/series_check.py --run-code --check-links
    python .build/series_check.py --html output          # also check a built tree
    python .build/series_check.py --json report.json --md report.md
Exit status is 1 when any hard defect is found, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import build as buildmod  # the canonical build.py next to this file
except Exception:  # pragma: no cover
    buildmod = None

HARD = {"encoding", "math-balance", "math-katex", "xref", "code-fail", "link-internal", "build", "structure-h1"}


class Report:
    def __init__(self):
        self.findings: list[dict] = []
        self.stats: dict = {}

    def add(self, check: str, file: str, line: int | None, msg: str, severity: str | None = None):
        self.findings.append({"check": check, "file": file, "line": line, "msg": msg,
                              "severity": severity or ("hard" if check in HARD else "candidate")})

    def hard(self) -> list[dict]:
        return [f for f in self.findings if f["severity"] == "hard"]


# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------

def discover_sources(repo: Path) -> tuple[dict | None, list[Path]]:
    if buildmod is not None:
        name = buildmod.detect_repo_name(repo)
        cfg = buildmod.BOOK_CONFIGS.get(name)
        if cfg:
            cfg = {**cfg, "slug": name}
            return cfg, buildmod.find_source_files(repo, cfg)
    # fallback: any markdown under common dirs
    files = []
    for d in ("chapters", "manuscript", "book/src", "src"):
        p = repo / d
        if p.exists():
            files += sorted(x for x in p.rglob("*.md") if not x.name.startswith("_"))
    return None, files


def strip_code(text: str) -> tuple[str, list[tuple[int, int, str, str]]]:
    """Blank out fenced code blocks (keeping line count). Return (text, [(start, end, lang, code)])."""
    blocks = []
    out_lines = text.split("\n")
    i = 0
    n = len(out_lines)
    while i < n:
        m = re.match(r"^\s*(```|~~~)\s*([\w+-]*)", out_lines[i])
        if m:
            fence, lang = m.group(1), m.group(2).lower()
            j = i + 1
            while j < n and not out_lines[j].strip().startswith(fence):
                j += 1
            code = "\n".join(out_lines[i + 1:j])
            blocks.append((i + 1, j + 1, lang, code))
            for k in range(i, min(j + 1, n)):
                out_lines[k] = ""
            i = j + 1
        else:
            i += 1
    return "\n".join(out_lines), blocks


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def mask(text: str, pattern: str, flags: int = 0, token: str = "X") -> str:
    """Replace matches with a single token (+ the newlines they contained) so
    line numbers survive and prose checks do not see runs of blanks."""
    return re.sub(pattern, lambda m: token + "".join(c for c in m.group(0) if c == "\n"), text, flags=flags)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

MOJIBAKE = re.compile(r"Ã[\x80-\xbf]|â€[\x9c\x9d\x98\x99\x93\x94\xa6]|Â[\xa0-\xbf]|\ufffd|[\u0080-\u009f]")


def check_encoding(path: Path, rel: str, rep: Report) -> str | None:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        rep.add("encoding", rel, raw.count(b"\n", 0, e.start) + 1, f"not valid UTF-8 at byte {e.start}: {e.reason}")
        text = raw.decode("utf-8", "replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        rep.add("encoding", rel, 1, "UTF-8 BOM present (python-markdown treats it as text)", "candidate")
    for m in MOJIBAKE.finditer(text):
        rep.add("encoding", rel, line_of(text, m.start()), f"mojibake / control char {m.group(0)!r}")
    return text


def check_structure(text: str, rel: str, rep: Report, order_idx: int, all_files: list[str]):
    body, _ = strip_code(text)
    h1s = [(line_of(body, m.start()), m.group(1).strip()) for m in re.finditer(r"^#\s+(.+)$", body, re.M)]
    if len(h1s) == 0:
        rep.add("structure-h1", rel, 1, "no H1 heading (build uses it as the page title)")
    elif len(h1s) > 1:
        rep.add("structure-h1", rel, h1s[1][0], f"{len(h1s)} H1 headings; only the first becomes the title")
    chapter_no = None
    if h1s:
        m = re.match(r"(?:Chapter|Ch\.?)\s+(\d+)", h1s[0][1], re.I)
        if m:
            chapter_no = int(m.group(1))
            fm = re.search(r"(?:ch|chapter)[-_]?0*(\d+)", Path(rel).stem, re.I)
            if fm and int(fm.group(1)) != chapter_no:
                rep.add("structure", rel, h1s[0][0],
                        f"H1 says Chapter {chapter_no} but filename says {fm.group(1)}", "hard")
    # heading level jumps
    prev = 1
    for m in re.finditer(r"^(#{2,6})\s+(.+)$", body, re.M):
        lvl = len(m.group(1))
        if lvl > prev + 1:
            rep.add("structure", rel, line_of(body, m.start()), f"heading level jumps from h{prev} to h{lvl}")
        prev = lvl
        if chapter_no is not None and lvl == 2:
            sm = re.match(r"(\d+)\.(\d+)", m.group(2).strip())
            if sm and int(sm.group(1)) != chapter_no:
                rep.add("structure", rel, line_of(body, m.start()),
                        f"section '{m.group(2).strip()[:40]}' numbered for chapter {sm.group(1)}, file is chapter {chapter_no}", "hard")
    # section number sequence
    secs = [tuple(map(int, s)) for s in re.findall(r"^##\s+(\d+)\.(\d+)\b", body, re.M)]
    for a, b in zip(secs, secs[1:]):
        if a[0] == b[0] and b[1] not in (a[1] + 1,):
            rep.add("structure", rel, None, f"section numbering {a[0]}.{a[1]} -> {b[0]}.{b[1]} is not consecutive")
    return chapter_no


def extract_math(text: str) -> list[tuple[int, str, bool]]:
    """Return [(line, tex, display)] for $$..$$, $..$, \\[..\\], \\(..\\) outside code."""
    body, _ = strip_code(text)
    body = strip_inline_code(body)
    out = []
    consumed = [False] * len(body)

    def take(m, tex, display):
        for k in range(m.start(), m.end()):
            consumed[k] = True
        out.append((line_of(body, m.start()), tex, display))

    for m in re.finditer(r"\$\$(.+?)\$\$", body, re.S):
        take(m, m.group(1), True)
    for m in re.finditer(r"\\\[(.+?)\\\]", body, re.S):
        if not consumed[m.start()]:
            take(m, m.group(1), True)
    for m in re.finditer(r"(?<![\$\\])\$(?!\$)(?!\s)(.+?)(?<![\s\\])\$(?!\$)", body):
        if not consumed[m.start()]:
            take(m, m.group(1), False)
    for m in re.finditer(r"\\\((.+?)\\\)", body):
        if not consumed[m.start()]:
            take(m, m.group(1), False)
    return out


def check_math_balance(text: str, rel: str, rep: Report):
    body, _ = strip_code(text)
    body = strip_inline_code(body)
    # $$ pairs
    dd = [m.start() for m in re.finditer(r"\$\$", body)]
    if len(dd) % 2:
        rep.add("math-balance", rel, line_of(body, dd[-1]), "odd number of $$ delimiters")
    # single $ per paragraph (after removing $$ blocks and escaped \$)
    stripped = re.sub(r"\$\$.+?\$\$", lambda m: " " * len(m.group(0)), body, flags=re.S)
    stripped = stripped.replace("\\$", "  ")
    for para_m in re.finditer(r"(?:[^\n]+\n?)+", stripped):
        para = para_m.group(0)
        if para.count("$") % 2:
            rep.add("math-balance", rel, line_of(stripped, para_m.start()),
                    "odd number of $ in paragraph (unclosed inline math, or a literal $ that needs \\$)")
    # environments
    for env in set(re.findall(r"\\begin\{(\w+\*?)\}", body)):
        b, e = len(re.findall(rf"\\begin\{{{re.escape(env)}\}}", body)), len(re.findall(rf"\\end\{{{re.escape(env)}\}}", body))
        if b != e:
            rep.add("math-balance", rel, None, f"\\begin{{{env}}} x{b} vs \\end{{{env}}} x{e}")


def check_math_katex(items: list[tuple[str, int, str, bool]], rep: Report):
    """items: [(rel, line, tex, display)] -> run katex_check.js once for all."""
    node = shutil.which("node")
    js = HERE / "katex_check.js"
    if not node or not js.exists():
        rep.stats["katex"] = "skipped (node or katex_check.js missing)"
        return
    payload = [{"id": i, "tex": t, "display": d} for i, (_, _, t, d) in enumerate(items)]
    env = dict(os.environ)
    if "KATEX_NODE_PATH" not in env:
        for cand in (HERE, HERE.parent, HERE.parent.parent,
                     HERE.parent.parent / 'erisml-lib' / 'tools' / 'series-build'):
            if (cand / "node_modules" / "katex").exists():
                env["KATEX_NODE_PATH"] = str(cand)
                break
    r = subprocess.run([node, str(js)], input=json.dumps(payload), text=True, encoding="utf-8",
                       capture_output=True, env=env)
    if r.returncode != 0:
        rep.stats["katex"] = f"skipped ({r.stderr.strip()[:120]})"
        return
    fails = json.loads(r.stdout or "[]")
    for f in fails:
        rel, line, tex, _ = items[f["id"]]
        rep.add("math-katex", rel, line, f"KaTeX: {f['error'][:110]}  in  {tex[:60]!r}")
    rep.stats["katex"] = f"{len(items)} snippets parsed, {len(fails)} failures"


XREF_KINDS = {
    "Chapter": r"Chapters?\s+(\d+)(?![.\d])",
    "Section": r"Sections?\s+(\d+\.\d+(?:\.\d+)?)",
    "Figure": r"Fig(?:ure|\.)s?\s+(\d+\.\d+|\d+)",
    "Table": r"Tables?\s+(\d+\.\d+|\d+)",
    "Theorem": r"Theorems?\s+(\d+\.\d+|\d+)",
    "Lemma": r"Lemmas?\s+(\d+\.\d+|\d+)",
    "Definition": r"Definitions?\s+(\d+\.\d+|\d+)",
    "Proposition": r"Propositions?\s+(\d+\.\d+|\d+)",
    "Corollary": r"Corollar(?:y|ies)\s+(\d+\.\d+|\d+)",
    "Equation": r"(?:Equation|Eq\.?)s?\s+\(?(\d+\.\d+)\)?",
    "Appendix": r"Appendix\s+([A-H])\b",
}


def collect_targets(texts: dict[str, str]) -> dict[str, set[str]]:
    T: dict[str, set[str]] = defaultdict(set)
    for rel, text in texts.items():
        body, _ = strip_code(text)
        for m in re.finditer(r"^#\s+(?:Chapter|Ch\.?)\s+(\d+)", body, re.M | re.I):
            T["Chapter"].add(m.group(1))
        for m in re.finditer(r"^#\s+Appendix\s+([A-H])\b", body, re.M | re.I):
            T["Appendix"].add(m.group(1).upper())
        if re.search(r"appendix[-_]([a-h])", Path(rel).stem, re.I):
            T["Appendix"].add(re.search(r"appendix[-_]([a-h])", Path(rel).stem, re.I).group(1).upper())
        for m in re.finditer(r"^#{2,4}\s+(\d+\.\d+(?:\.\d+)?)\b", body, re.M):
            T["Section"].add(m.group(1))
        for kind in ("Figure", "Table", "Theorem", "Lemma", "Definition", "Proposition", "Corollary"):
            # captions / labels typically: **Figure 2.1** | Figure 2.1: | > **Theorem 3.2**
            for m in re.finditer(rf"(?:^|\*\*|\b){kind}\s+(\d+\.\d+|\d+)\s*(?:\*\*|[:.]|—|–|\()", body, re.M):
                T[kind].add(m.group(1))
        for m in re.finditer(r"\\tag\{\(?(\d+\.\d+)\)?\}", body):
            T["Equation"].add(m.group(1))
        for m in re.finditer(r"^\s*\((\d+\.\d+)\)\s*$", body, re.M):  # bare (N.M) after display math
            T["Equation"].add(m.group(1))
        for m in re.finditer(r"\$\$[^$]*?\$\$\s*\((\d+\.\d+)\)", body, re.S):
            T["Equation"].add(m.group(1))
    return T


def check_xrefs(texts: dict[str, str], rep: Report):
    T = collect_targets(texts)
    stats = Counter()
    for rel, text in texts.items():
        body, _ = strip_code(text)
        body = strip_inline_code(body)
        for kind, pat in XREF_KINDS.items():
            for m in re.finditer(pat, body):
                ref = m.group(1)
                stats["refs"] += 1
                if kind == "Appendix":
                    ref = ref.upper()
                targets = T.get(kind, set())
                if not targets and kind not in ("Chapter", "Appendix", "Section"):
                    continue  # the book does not label this kind; cannot judge
                if ref not in targets:
                    # allow "Chapter 1" style refs to chapters that exist only by filename
                    if kind == "Chapter" and any(re.search(rf"(?:ch|chapter)[-_]?0*{ref}\b", Path(f).stem, re.I) for f in texts):
                        continue
                    rep.add("xref", rel, line_of(body, m.start()), f"{kind} {ref} referenced but no such {kind.lower()} is defined in this book")
                    stats["dangling"] += 1
    rep.stats["xrefs"] = f"{stats['refs']} references checked, {stats['dangling']} dangling; "\
                         f"targets: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(T.items()))


PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX|TK|PLACEHOLDER|lorem ipsum|citation needed|INSERT [A-Z ]+HERE)\b|\?\?\?|\[\s*(?:ref|cite|citation)\s*\]", re.I)
DUP_OK = {"that", "had", "is", "on", "in", "it", "do", "no", "so", "very", "long", "far", "many", "much", "we"}


def check_prose(text: str, rel: str, rep: Report):
    body, _ = strip_code(text)
    body = mask(body, r"`[^`\n]*`", token="CODE")
    body_nomath = mask(body, r"\$\$.+?\$\$|\$[^$\n]+\$|\\\[.+?\\\]|\\\(.+?\\\)", flags=re.S, token="MATH")
    for m in PLACEHOLDER.finditer(body_nomath):
        rep.add("placeholder", rel, line_of(body, m.start()), f"placeholder text {m.group(0)!r}")
    for m in re.finditer(r"\b([A-Za-z]{2,})\s+\1\b", body_nomath):
        if m.group(1).lower() not in DUP_OK:
            rep.add("prose-dup", rel, line_of(body, m.start()), f"duplicate word '{m.group(1)} {m.group(1)}'")
    for m in re.finditer(r"(?<!\.)\.\.(?!\.)|,,|;;|::|\s+[,;:](?!\S)|\s+\.(?=\s|$)", body_nomath):
        ctx = body_nomath[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
        rep.add("prose-punct", rel, line_of(body, m.start()), f"punctuation: ...{ctx}...")
    for para_m in re.finditer(r"(?:[^\n]+\n?)+", body_nomath):
        para = para_m.group(0)
        if para.lstrip().startswith(("|", "    ", "\t")):
            continue
        for o, c in (("(", ")"), ("[", "]")):
            if para.count(o) != para.count(c):
                rep.add("prose-brackets", rel, line_of(body, para_m.start()),
                        f"unbalanced {o}{c} in paragraph ({para.count(o)} vs {para.count(c)})")
                break
        for o, c in (("“", "”"),):
            if abs(para.count(o) - para.count(c)) > 1:
                rep.add("prose-quotes", rel, line_of(body, para_m.start()), "unbalanced curly quotes in paragraph")


def check_spelling(files: list[Path], repo: Path, rep: Report):
    cs = shutil.which("codespell")
    if cs:
        r = subprocess.run([cs, "-q", "3", "--builtin", "clear,rare,informal", *map(str, files)],
                           text=True, encoding="utf-8", errors="replace", capture_output=True)
        n = 0
        for line in r.stdout.splitlines():
            m = re.match(r"(.+?):(\d+): (.+?) ==> (.+)$", line)
            if m:
                rel = os.path.relpath(m.group(1), repo)
                rep.add("spelling", rel, int(m.group(2)), f"codespell: {m.group(3)} -> {m.group(4)}")
                n += 1
        rep.stats["codespell"] = f"{n} suggestions"
    else:
        rep.stats["codespell"] = "not installed (pip install codespell)"
    try:
        from spellchecker import SpellChecker
    except ImportError:
        rep.stats["rare-tokens"] = "pyspellchecker not installed"
        return
    sp = SpellChecker(distance=1)
    counts: Counter = Counter()
    where: dict[str, str] = {}
    for f in files:
        text, _ = strip_code(f.read_text(encoding="utf-8", errors="replace"))
        text = strip_inline_code(text)
        text = re.sub(r"\$\$.+?\$\$|\$[^$\n]+\$", " ", text, flags=re.S)
        text = re.sub(r"https?://\S+|\[[^\]]*\]\([^)]*\)", " ", text)
        for w in re.findall(r"\b[a-z]{4,}\b", text):
            counts[w] += 1
            where.setdefault(w, os.path.relpath(f, repo))
    unknown = [w for w in counts if w in sp.unknown([w])]
    # rare + unknown = likely typos; frequent + unknown = domain vocabulary
    cands = sorted((w for w in unknown if counts[w] <= 2), key=lambda w: (counts[w], w))
    for w in cands[:150]:
        corr = sp.correction(w)
        if corr and corr != w:
            rep.add("spelling-candidate", where[w], None, f"'{w}' (x{counts[w]}) — maybe '{corr}'")
    rep.stats["rare-tokens"] = f"{len(unknown)} unknown tokens, {len(cands)} rare (<=2 uses) listed as candidates (first 150)"


def check_links(texts: dict[str, str], repo: Path, rep: Report, external: bool):
    seen_ext: dict[str, str] = {}
    for rel, text in texts.items():
        body, _ = strip_code(text)
        body = mask(body, r"\$\$.+?\$\$|\$[^$\n]+\$", flags=re.S)
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", body):
            url = m.group(1)
            if "\\" in url or url.startswith("{"):
                continue  # TeX, not a link
            if url.startswith(("http://", "https://")):
                if not external:
                    continue
                if url not in seen_ext:
                    seen_ext[url] = head(url)
                if seen_ext[url] != "ok":
                    rep.add("link-external", rel, line_of(body, m.start()), f"{url} -> {seen_ext[url]}")
            elif url.startswith(("#", "mailto:")):
                continue
            else:
                target = (repo / rel).parent / url.split("#")[0]
                alt = target.with_suffix(".md") if target.suffix == ".html" else None
                if not target.exists() and not (alt and alt.exists()):
                    rep.add("link-internal", rel, line_of(body, m.start()), f"relative link target missing: {url}")
    if external:
        rep.stats["external-links"] = f"{len(seen_ext)} unique URLs, {sum(v != 'ok' for v in seen_ext.values())} failing"


def head(url: str) -> str:
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 series_check"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return "ok" if r.status < 400 else f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 429):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 series_check"})
                with urllib.request.urlopen(req, timeout=12) as r:
                    return "ok" if r.status < 400 else f"HTTP {r.status}"
            except Exception as e2:
                return f"{type(e2).__name__}: {str(e2)[:60]}"
        return f"HTTP {e.code}"
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:60]}"


def run_code_blocks(texts: dict[str, str], repo: Path, rep: Report, timeout: int):
    total = ok = 0
    results = []
    with tempfile.TemporaryDirectory(prefix="series-code-") as td:
        for rel, text in texts.items():
            _, blocks = strip_code(text)
            for start, end, lang, code in blocks:
                if lang not in ("python", "py", "python3"):
                    continue
                if re.search(r"^\s*(>>>|\.\.\.)", code, re.M):
                    continue  # doctest-style transcript, not runnable as-is
                total += 1
                src = Path(td) / f"blk_{total}.py"
                src.write_text(code, encoding="utf-8")
                t0 = time.time()
                try:
                    r = subprocess.run([sys.executable, "-I", str(src)], cwd=td, capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=timeout)
                    dt = time.time() - t0
                    if r.returncode == 0:
                        ok += 1
                        results.append({"file": rel, "line": start, "status": "ok", "seconds": round(dt, 1)})
                    else:
                        err = (r.stderr.strip().splitlines() or ["(no stderr)"])[-1]
                        kind = "import-unavailable" if "ModuleNotFoundError" in err else (
                            "needs-context" if "NameError" in err or "FileNotFoundError" in err else "error")
                        results.append({"file": rel, "line": start, "status": kind, "error": err[:160]})
                        sev = "candidate" if kind != "error" else "hard"
                        rep.add("code-fail" if kind == "error" else f"code-{kind}", rel, start, err[:160], sev)
                except subprocess.TimeoutExpired:
                    results.append({"file": rel, "line": start, "status": "timeout"})
                    rep.add("code-timeout", rel, start, f"exceeded {timeout}s", "candidate")
    rep.stats["code-blocks"] = f"{total} python blocks run: {ok} ok, {total - ok} not clean (see findings)"
    rep.stats["code-results"] = results


def check_build(repo: Path, html_dir: Path | None, rep: Report, ordered_sources: list[Path]):
    """Build to a temp dir (or use html_dir) and validate the HTML tree."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        rep.stats["build"] = "bs4 not installed; skipped"
        return
    tmp = None
    if html_dir is None:
        build_py = repo / ".build" / "build.py"
        if not build_py.exists():
            build_py = HERE / "build.py"
        tmp = Path(tempfile.mkdtemp(prefix="series-build-"))
        r = subprocess.run([sys.executable, str(build_py), "--repo-root", str(repo), "--output-dir", str(tmp), "-q"],
                           text=True, encoding="utf-8", errors="replace", capture_output=True)
        if r.returncode != 0:
            rep.add("build", ".build/build.py", None, (r.stdout + r.stderr).strip()[-400:])
            rep.stats["build"] = "FAILED"
            shutil.rmtree(tmp, ignore_errors=True)
            return
        html_dir = tmp
    pages = sorted(html_dir.glob("*.html"))
    names = {p.name for p in pages}
    if "index.html" not in names:
        rep.add("build", str(html_dir), None, "no index.html in built tree")
    broken = 0
    for p in pages:
        soup = BeautifulSoup(p.read_text(encoding="utf-8", errors="replace"), "html.parser")
        if not (soup.title and soup.title.string and soup.title.string.strip()):
            rep.add("build", p.name, None, "empty <title>")
        for a in soup.find_all("a", href=True):
            href = a["href"].split("#")[0]
            if not href or href.startswith(("http://", "https://", "mailto:", "//")):
                continue
            if href.startswith("../"):
                continue  # portal-level asset; validated by the Pages preflight
            if href not in names and not (html_dir / href).exists():
                rep.add("link-internal", p.name, None, f"href '{a['href']}' does not resolve in the built site")
                broken += 1
    idx = BeautifulSoup((html_dir / "index.html").read_text(encoding="utf-8", errors="replace"), "html.parser") \
        if "index.html" in names else None
    if idx is not None:
        listed = {a["href"].split("#")[0] for a in idx.find_all("a", href=True)}
        for p in pages:
            if p.name != "index.html" and p.name not in listed:
                rep.add("build", "index.html", None, f"{p.name} is built but not listed on the contents page")
    rep.stats["build"] = f"{len(pages)} pages, {broken} broken internal links" + (" (temp build)" if tmp else f" ({html_dir})")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def write_reports(rep: Report, repo: Path, json_path: Path, md_path: Path, cfg: dict | None, n_files: int, n_words: int):
    hard = rep.hard()
    by_check = Counter(f["check"] for f in rep.findings)
    data = {"repo": repo.name, "book": cfg and {"number": cfg["number"], "title": cfg["title"]},
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"), "files": n_files, "words": n_words,
            "hard_defects": len(hard), "counts": dict(by_check), "stats": rep.stats, "findings": rep.findings}
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

    lines = [f"# series_check report — {cfg['title'] if cfg else repo.name}", "",
             f"Generated {data['generated']} over {n_files} source files ({n_words:,} words).", "",
             f"**Hard defects: {len(hard)}**  ·  candidates: {len(rep.findings) - len(hard)}", "", "## Summary", ""]
    lines.append("| check | findings |\n|---|---|")
    for k, v in sorted(by_check.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## Machine stats", ""]
    for k, v in rep.stats.items():
        if k == "code-results":
            continue
        lines.append(f"- **{k}**: {v}")
    if rep.stats.get("code-results"):
        lines += ["", "## Code blocks", "", "| file | line | status | note |", "|---|---|---|---|"]
        for r in rep.stats["code-results"]:
            lines.append(f"| {r['file']} | {r['line']} | {r['status']} | {r.get('error', r.get('seconds', ''))} |")
    lines += ["", "## Findings", ""]
    for sev in ("hard", "candidate"):
        group = [f for f in rep.findings if f["severity"] == sev]
        if not group:
            continue
        lines.append(f"### {sev} ({len(group)})\n")
        for f in sorted(group, key=lambda x: (x["check"], x["file"], x["line"] or 0)):
            loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            lines.append(f"- `{f['check']}` {loc} — {f['msg']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Mechanical checks for a Geometric Series volume")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--html", default=None, help="built HTML dir to validate (default: temp build)")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--run-code", action="store_true", help="execute fenced python blocks")
    ap.add_argument("--code-timeout", type=int, default=90)
    ap.add_argument("--check-links", action="store_true", help="HEAD-check external URLs")
    ap.add_argument("--no-spelling", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--md", default=None)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    cfg, files = discover_sources(repo)
    if not files:
        print("no source files found"); sys.exit(1)
    rep = Report()
    texts: dict[str, str] = {}
    rels = [os.path.relpath(f, repo).replace("\\", "/") for f in files]
    for f, rel in zip(files, rels):
        t = check_encoding(f, rel, rep)
        texts[rel] = t
    n_words = sum(len(re.findall(r"\w+", t)) for t in texts.values())
    for i, (rel, t) in enumerate(texts.items()):
        check_structure(t, rel, rep, i, rels)
        check_math_balance(t, rel, rep)
        check_prose(t, rel, rep)
    math_items = [(rel, ln, tex, disp) for rel, t in texts.items() for ln, tex, disp in extract_math(t)]
    check_math_katex(math_items, rep)
    check_xrefs(texts, rep)
    check_links(texts, repo, rep, external=args.check_links)
    if not args.no_spelling:
        check_spelling(files, repo, rep)
    if args.run_code:
        run_code_blocks(texts, repo, rep, args.code_timeout)
    if not args.no_build:
        check_build(repo, Path(args.html).resolve() if args.html else None, rep, files)

    out_dir = repo / ".build" / "reports"
    json_path = Path(args.json) if args.json else out_dir / "series_check.json"
    md_path = Path(args.md) if args.md else out_dir / "series_check.md"
    write_reports(rep, repo, json_path, md_path, cfg, len(files), n_words)
    hard = rep.hard()
    print(f"{cfg['title'] if cfg else repo.name}: {len(files)} files, {n_words:,} words — "
          f"{len(hard)} hard defect(s), {len(rep.findings) - len(hard)} candidate(s)")
    for k, v in rep.stats.items():
        if k != "code-results":
            print(f"  {k}: {v}")
    print(f"  report: {md_path}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
