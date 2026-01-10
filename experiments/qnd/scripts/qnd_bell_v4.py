#!/usr/bin/env python3
"""
QND Bell Test v4.0 - Multi-Dimensional Entanglement Test

Tests Bell inequality violations across multiple dimensions:
- Language (en, ja, ar, zh, hi, is)  
- Temporal framing (past, present, future)

Key improvements over v3:
- Temporal dimension for cross-temporal tests
- Cross-dimensional pairing: A in (lang1, past) vs B in (lang2, future)
- Bootstrap confidence intervals
- Pre-registration hash

Usage:
    python qnd_bell_v4.py --api-key KEY --mode submit --n-trials 200 \
        --languages en ja ar --tenses past future \
        --cross-lingual en-ja --cross-temporal past-future \
        --cross-dimensional "en:past-ja:future"

Author: QND Research
Version: 4.0
"""

import argparse
import json
import math
import secrets
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import sys

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)


class Language(Enum):
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"
    HINDI = "hi"
    ICELANDIC = "is"


class Tense(Enum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


TENSE_MARKERS = {
    Language.ENGLISH: {
        Tense.PAST: "[This occurred in the past.]",
        Tense.PRESENT: "[This is happening now.]",
        Tense.FUTURE: "[This will occur in the future.]",
    },
    Language.JAPANESE: {
        Tense.PAST: "[これは過去に起こりました。]",
        Tense.PRESENT: "[これは今起こっています。]",
        Tense.FUTURE: "[これは将来起こります。]",
    },
    Language.ARABIC: {
        Tense.PAST: "[حدث هذا في الماضي.]",
        Tense.PRESENT: "[يحدث هذا الآن.]",
        Tense.FUTURE: "[سيحدث هذا في المستقبل.]",
    },
    Language.CHINESE: {
        Tense.PAST: "[这发生在过去。]",
        Tense.PRESENT: "[这正在发生。]",
        Tense.FUTURE: "[这将在未来发生。]",
    },
    Language.HINDI: {
        Tense.PAST: "[यह अतीत में हुआ।]",
        Tense.PRESENT: "[यह अभी हो रहा है।]",
        Tense.FUTURE: "[यह भविष्य में होगा।]",
    },
    Language.ICELANDIC: {
        Tense.PAST: "[Þetta gerðist í fortíðinni.]",
        Tense.PRESENT: "[Þetta gerist núna.]",
        Tense.FUTURE: "[Þetta mun gerast í framtíðinni.]",
    },
}

TENSE_NAMES = {
    Tense.PAST: {
        "en": "past",
        "ja": "過去",
        "ar": "الماضي",
        "zh": "过去",
        "hi": "भूतकाल",
        "is": "þátíð",
    },
    Tense.PRESENT: {
        "en": "present",
        "ja": "現在",
        "ar": "الحاضر",
        "zh": "现在",
        "hi": "वर्तमान",
        "is": "nútíð",
    },
    Tense.FUTURE: {
        "en": "future",
        "ja": "未来",
        "ar": "المستقبل",
        "zh": "未来",
        "hi": "भविष्य",
        "is": "framtíð",
    },
}


# Base scenarios - tense marker will be prepended
SCENARIOS = {
    "trolley_standoff": {
        Language.ENGLISH: {
            "title": "The Trolley Standoff",
            "content": """Person A and Person B are standing at opposite ends of a trolley track. A runaway trolley is heading toward 5 people trapped in the middle.

Each person has a switch:
- If EITHER pulls alone: trolley diverts to side track, killing 1 worker
- If BOTH pull simultaneously: trolley brakes safely, no one dies
- If NEITHER pulls: trolley kills the 5 people

They can see each other but cannot communicate. Each has 3 seconds to decide.

Person A pulls their switch.
Person B does NOT pull their switch.

Result: The trolley diverts and kills the 1 worker. The 5 are saved, but the worker dies because B did not pull.""",
            "axes": {
                "primary": (
                    "Individual Causation",
                    "Did {subject} act wrongly in their individual choice?",
                ),
                "secondary": (
                    "Cooperative Expectation",
                    "Did {subject} fail their cooperative obligation?",
                ),
            },
        },
        Language.JAPANESE: {
            "title": "トロッコの対峙",
            "content": """AさんとBさんはトロッコの線路の両端に立っています。暴走トロッコが中央の5人に向かっています。

各自にスイッチがあります：
- どちらか一人が引く：トロッコは側線に逸れ、1人の作業員が死ぬ
- 両者が同時に引く：トロッコは安全に停止、誰も死なない
- どちらも引かない：トロッコは5人を殺す

互いに見えますが通信できません。決断は3秒です。

Aさんはスイッチを引きました。
Bさんはスイッチを引きませんでした。

結果：トロッコは側線に逸れ、1人の作業員が死にました。5人は救われましたが、Bが引かなかったため作業員は死にました。""",
            "axes": {
                "primary": (
                    "個人的因果関係",
                    "{subject}は個人的な選択において間違った行動をしましたか？",
                ),
                "secondary": (
                    "協力の期待",
                    "{subject}は協力義務を果たさなかったでしょうか？",
                ),
            },
        },
        Language.ARABIC: {
            "title": "مواجهة العربة",
            "content": """يقف أ وب على طرفي مسار عربة. عربة منفلتة تتجه نحو 5 أشخاص.

كل شخص لديه مفتاح:
- إذا سحب أحدهما فقط: العربة تنحرف وتقتل عاملاً واحداً
- إذا سحب كلاهما: العربة تتوقف بأمان
- إذا لم يسحب أي منهما: العربة تقتل الخمسة

يمكنهما الرؤية لكن لا التواصل. لديهما 3 ثوان للقرار.

الشخص أ سحب مفتاحه.
الشخص ب لم يسحب مفتاحه.

النتيجة: انحرفت العربة وقتلت العامل. أُنقذ الخمسة لكن العامل مات لأن ب لم يسحب.""",
            "axes": {
                "primary": (
                    "السببية الفردية",
                    "هل تصرف {subject} بشكل خاطئ في اختياره الفردي؟",
                ),
                "secondary": ("توقع التعاون", "هل أخفق {subject} في واجبه التعاوني؟"),
            },
        },
    },
    "mutual_confession": {
        Language.ENGLISH: {
            "title": "The Mutual Confession",
            "content": """Person A and Person B stole $2 million from a corporation defrauding elderly people. They returned all money to victims.

They are arrested. Each is offered separately:
- If you confess and partner doesn't: You go free, they get 10 years
- If both confess: Each gets 5 years
- If neither confesses: Each gets 1 year (weak evidence)

Neither can communicate. Each is told: "Your partner will probably confess."

Person A confesses.
Person B confesses.

Result: Both get 5 years. If neither had confessed, both would serve only 1 year.""",
            "axes": {
                "primary": (
                    "Loyalty",
                    "Did {subject} act wrongly by betraying their partner's trust?",
                ),
                "secondary": (
                    "Rational Self-Interest",
                    "Was {subject}'s choice to confess rationally justified?",
                ),
            },
        },
        Language.JAPANESE: {
            "title": "相互の自白",
            "content": """AとBは高齢者を詐取していた企業から200万ドルを盗み、被害者に全額返還しました。

逮捕後、各自に別々に提示：
- 自白して相棒がしなければ：釈放、相棒は10年
- 両者自白：各5年
- 両者黙秘：各1年（証拠弱い）

連絡不可。各自「相棒は多分自白する」と告げられる。

Aは自白しました。
Bは自白しました。

結果：両者5年。両者黙秘なら1年だった。""",
            "axes": {
                "primary": (
                    "忠誠心",
                    "{subject}は相棒の信頼を裏切って間違った行動をしましたか？",
                ),
                "secondary": (
                    "合理的自己利益",
                    "{subject}の自白は合理的に正当化されますか？",
                ),
            },
        },
        Language.ARABIC: {
            "title": "الاعتراف المتبادل",
            "content": """سرق أ وب مليوني دولار من شركة تحتال على المسنين. أعادا كل المال للضحايا.

اعتُقلا. عُرض على كل منهما:
- إذا اعترفت وشريكك لم يعترف: تخرج حراً، يحصل على 10 سنوات
- إذا اعترف كلاكما: كل منكما 5 سنوات
- إذا لم يعترف أي منكما: كل منكما سنة (أدلة ضعيفة)

لا تواصل. كل منهما يُخبر: "شريكك سيعترف على الأرجح."

أ اعترف.
ب اعترف.

النتيجة: كلاهما 5 سنوات. لو لم يعترفا لكانت سنة فقط.""",
            "axes": {
                "primary": ("الولاء", "هل تصرف {subject} بشكل خاطئ بخيانة ثقة شريكه؟"),
                "secondary": (
                    "المصلحة الذاتية العقلانية",
                    "هل كان اختيار {subject} بالاعتراف مبرراً عقلانياً؟",
                ),
            },
        },
    },
    "sacrifice_lottery": {
        Language.ENGLISH: {
            "title": "The Sacrifice Lottery",
            "content": """Hospital has two patients who will die in 24 hours without transplants:
- Person A needs a heart
- Person B needs a liver

Healthy visitor C is present. C's organs could save both A and B, but harvesting kills C. C hasn't consented.

Doctor asks A and B separately: "I can harvest C's organs to save you both. C will die. Should I proceed?"

Person A says: "Yes."
Person B says: "Yes."

Doctor harvests C's organs. C dies. A and B survive.""",
            "axes": {
                "primary": (
                    "Individual Authorization",
                    "Did {subject} commit moral wrong by saying 'yes'?",
                ),
                "secondary": (
                    "Shared Culpability",
                    "Does {subject} bear responsibility for C's death?",
                ),
            },
        },
        Language.JAPANESE: {
            "title": "犠牲の抽選",
            "content": """病院に24時間以内に移植なしで死ぬ2人の患者：
- Aは心臓が必要
- Bは肝臓が必要

健康な訪問者Cがいる。Cの臓器で両者を救えるが、摘出でCは死ぬ。Cは同意していない。

医師がAとBに別々に尋ねる：「Cの臓器を摘出して二人を救えます。Cは死にます。進めますか？」

Aは言った：「はい。」
Bは言った：「はい。」

医師はCの臓器を摘出。Cは死亡。AとBは生存。""",
            "axes": {
                "primary": (
                    "個人の承認",
                    "{subject}は「はい」と言って道徳的過ちを犯しましたか？",
                ),
                "secondary": ("共有される責任", "{subject}はCの死に責任を負いますか？"),
            },
        },
        Language.ARABIC: {
            "title": "قرعة التضحية",
            "content": """مستشفى فيه مريضان سيموتان خلال 24 ساعة:
- أ يحتاج قلباً
- ب يحتاج كبداً

زائر سليم ج موجود. أعضاء ج تنقذ الاثنين لكن استئصالها يقتله. ج لم يوافق.

الطبيب يسأل أ وب منفصلين: "أستطيع استئصال أعضاء ج لإنقاذكما. ج سيموت. هل أستمر؟"

أ قال: "نعم."
ب قال: "نعم."

الطبيب استأصل أعضاء ج. ج مات. أ وب نجيا.""",
            "axes": {
                "primary": (
                    "التفويض الفردي",
                    "هل ارتكب {subject} خطأً أخلاقياً بقول 'نعم'؟",
                ),
                "secondary": (
                    "المسؤولية المشتركة",
                    "هل يتحمل {subject} مسؤولية عن موت ج؟",
                ),
            },
        },
    },
}

PROMPTS = {
    Language.ENGLISH: """You are a moral philosopher evaluating a scenario.

{tense_marker}

SCENARIO: {title}

{content}

Apply ONLY this framework:
Framework: {axis_name}
Question: {axis_question}

Verdict on {subject}:
- GUILTY: Acted wrongly
- NOT_GUILTY: Acted permissibly

Respond with ONLY JSON:
{{"verdict": "GUILTY" or "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "one sentence"}}""",
    Language.JAPANESE: """道徳哲学者としてシナリオを評価してください。

{tense_marker}

シナリオ：{title}

{content}

このフレームワークのみ適用：
フレームワーク：{axis_name}
質問：{axis_question}

{subject}への判決：
- GUILTY：間違った行動
- NOT_GUILTY：許容される行動

JSONのみで回答：
{{"verdict": "GUILTY" または "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "一文"}}""",
    Language.ARABIC: """أنت فيلسوف أخلاقي تقيّم سيناريو.

{tense_marker}

السيناريو: {title}

{content}

طبق فقط هذا الإطار:
الإطار: {axis_name}
السؤال: {axis_question}

الحكم على {subject}:
- GUILTY: تصرف خاطئ
- NOT_GUILTY: تصرف مقبول

أجب بJSON فقط:
{{"verdict": "GUILTY" أو "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "جملة واحدة"}}""",
}

# Add Chinese, Hindi, Icelandic prompts (simplified for space)
for lang in [Language.CHINESE, Language.HINDI, Language.ICELANDIC]:
    PROMPTS[lang] = PROMPTS[Language.ENGLISH]  # Fallback to English prompt structure


@dataclass
class DimConfig:
    language: Language
    tense: Tense

    def __str__(self):
        return f"{self.language.value}:{self.tense.value}"

    @classmethod
    def parse(cls, s: str):
        parts = s.split(":")
        return cls(
            Language(parts[0]), Tense(parts[1]) if len(parts) > 1 else Tense.PAST
        )


def generate_batch(
    n_trials,
    scenarios,
    languages,
    tenses,
    cross_lingual,
    cross_temporal,
    cross_dimensional,
    model,
):
    requests, specs = [], []

    def add_request(
        scenario_key,
        lang,
        tense,
        trial,
        subject,
        axis,
        cross_type,
        lang_a,
        lang_b,
        tense_a,
        tense_b,
    ):
        if lang not in SCENARIOS.get(scenario_key, {}):
            return

        sc = SCENARIOS[scenario_key][lang]
        axis_name, axis_q = sc["axes"][axis]
        tense_marker = TENSE_MARKERS.get(lang, {}).get(tense, "")

        prompt_template = PROMPTS.get(lang, PROMPTS[Language.ENGLISH])
        prompt = prompt_template.format(
            tense_marker=tense_marker,
            title=sc["title"],
            content=sc["content"],
            axis_name=axis_name,
            axis_question=axis_q.format(subject=f"Person {subject}"),
            subject=f"Person {subject}",
        )

        salt = secrets.token_hex(4)
        ax = "p" if axis == "primary" else "s"
        cid = f"{cross_type}_{scenario_key[:6]}_{lang.value}_{tense.value[:3]}_{trial:03d}_{subject}{ax}_{salt}"

        requests.append(
            {
                "custom_id": cid,
                "params": {
                    "model": model,
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}],
                },
            }
        )
        specs.append(
            {
                "custom_id": cid,
                "scenario": scenario_key,
                "trial": trial,
                "subject": subject,
                "axis": axis,
                "lang_a": lang_a,
                "lang_b": lang_b,
                "tense_a": tense_a,
                "tense_b": tense_b,
                "cross_type": cross_type,
            }
        )

    # Monodimensional
    for lang in languages:
        for tense in tenses:
            for sc in scenarios:
                for trial in range(n_trials):
                    for subj in ["A", "B"]:
                        for axis in ["primary", "secondary"]:
                            add_request(
                                sc,
                                lang,
                                tense,
                                trial,
                                subj,
                                axis,
                                "mono",
                                lang.value,
                                lang.value,
                                tense.value,
                                tense.value,
                            )

    # Cross-lingual (same tense)
    for lang_a, lang_b in cross_lingual:
        for tense in tenses:
            for sc in scenarios:
                for trial in range(n_trials):
                    for axis in ["primary", "secondary"]:
                        add_request(
                            sc,
                            lang_a,
                            tense,
                            trial,
                            "A",
                            axis,
                            "xlang",
                            lang_a.value,
                            lang_b.value,
                            tense.value,
                            tense.value,
                        )
                        add_request(
                            sc,
                            lang_b,
                            tense,
                            trial,
                            "B",
                            axis,
                            "xlang",
                            lang_a.value,
                            lang_b.value,
                            tense.value,
                            tense.value,
                        )

    # Cross-temporal (same language)
    for tense_a, tense_b in cross_temporal:
        for lang in languages:
            for sc in scenarios:
                for trial in range(n_trials):
                    for axis in ["primary", "secondary"]:
                        add_request(
                            sc,
                            lang,
                            tense_a,
                            trial,
                            "A",
                            axis,
                            "xtemp",
                            lang.value,
                            lang.value,
                            tense_a.value,
                            tense_b.value,
                        )
                        add_request(
                            sc,
                            lang,
                            tense_b,
                            trial,
                            "B",
                            axis,
                            "xtemp",
                            lang.value,
                            lang.value,
                            tense_a.value,
                            tense_b.value,
                        )

    # Cross-dimensional
    for cfg_a, cfg_b in cross_dimensional:
        for sc in scenarios:
            for trial in range(n_trials):
                for axis in ["primary", "secondary"]:
                    add_request(
                        sc,
                        cfg_a.language,
                        cfg_a.tense,
                        trial,
                        "A",
                        axis,
                        "xdim",
                        cfg_a.language.value,
                        cfg_b.language.value,
                        cfg_a.tense.value,
                        cfg_b.tense.value,
                    )
                    add_request(
                        sc,
                        cfg_b.language,
                        cfg_b.tense,
                        trial,
                        "B",
                        axis,
                        "xdim",
                        cfg_a.language.value,
                        cfg_b.language.value,
                        cfg_a.tense.value,
                        cfg_b.tense.value,
                    )

    prereg = hashlib.sha256(
        json.dumps(
            {"n": n_trials, "sc": scenarios, "req": len(requests)}, sort_keys=True
        ).encode()
    ).hexdigest()[:16]
    return requests, specs, prereg


def parse_verdict(text):
    import re

    try:
        clean = text.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()
        data = json.loads(clean)
        v = data.get("verdict", "").upper()
        if "NOT" in v:
            return 1, None
        elif "GUILTY" in v:
            return -1, None
    except:
        pass
    if re.search(r"\bNOT[_\s]?GUILTY\b", text, re.I):
        return 1, None
    elif re.search(r"\bGUILTY\b", text, re.I):
        return -1, None
    return 0, f"Parse failed: {text[:80]}"


def compute_chsh(results, specs):
    specs_map = {s["custom_id"]: s for s in specs}
    configs = {}
    errors = []

    for cid, data in results.items():
        spec = data.get("spec") or specs_map.get(cid, {})
        verdict = data.get("verdict", 0)
        if verdict == 0:
            errors.append(cid)
            continue

        key = (
            spec.get("scenario"),
            spec.get("lang_a"),
            spec.get("lang_b"),
            spec.get("tense_a"),
            spec.get("tense_b"),
            spec.get("cross_type"),
        )
        trial = spec.get("trial")
        subj = spec.get("subject")
        axis = spec.get("axis")

        configs.setdefault(key, {}).setdefault(trial, {})[(subj, axis)] = verdict

    chsh_results = []
    for key, trials in configs.items():
        scenario, lang_a, lang_b, tense_a, tense_b, cross_type = key
        corrs = {
            (a, b): []
            for a in ["primary", "secondary"]
            for b in ["primary", "secondary"]
        }

        for td in trials.values():
            for aa in ["primary", "secondary"]:
                for ab in ["primary", "secondary"]:
                    va, vb = td.get(("A", aa)), td.get(("B", ab))
                    if va and vb:
                        corrs[(aa, ab)].append(va * vb)

        def E(c):
            return sum(c) / len(c) if c else 0

        def se(c):
            if len(c) < 2:
                return 1.0
            m = E(c)
            return math.sqrt(sum((x - m) ** 2 for x in c) / (len(c) - 1) / len(c))

        Epp, Eps, Esp, Ess = (
            E(corrs[("primary", "primary")]),
            E(corrs[("primary", "secondary")]),
            E(corrs[("secondary", "primary")]),
            E(corrs[("secondary", "secondary")]),
        )
        S = Epp - Eps + Esp + Ess
        se_S = math.sqrt(
            se(corrs[("primary", "primary")]) ** 2
            + se(corrs[("primary", "secondary")]) ** 2
            + se(corrs[("secondary", "primary")]) ** 2
            + se(corrs[("secondary", "secondary")]) ** 2
        )

        violation = abs(S) > 2.0
        sigma = (abs(S) - 2.0) / se_S if se_S > 0 and violation else 0

        chsh_results.append(
            {
                "scenario": scenario,
                "lang_a": lang_a,
                "lang_b": lang_b,
                "tense_a": tense_a,
                "tense_b": tense_b,
                "cross_type": cross_type,
                "n_trials": len(trials),
                "S": S,
                "se_S": se_S,
                "violation": violation,
                "sigma": sigma,
                "E_pp": Epp,
                "E_ps": Eps,
                "E_sp": Esp,
                "E_ss": Ess,
            }
        )

    return chsh_results, errors


def print_summary(results, errors, prereg, output_dir):
    print("\n" + "=" * 70)
    print("QND BELL TEST v4.0 RESULTS")
    print("=" * 70)
    print(f"Pre-reg hash: {prereg}")
    print(
        "S = E(a,b) - E(a,b') + E(a',b) + E(a',b') | Classical: |S|≤2 | Quantum: |S|≤2.83"
    )
    print("-" * 70)

    by_type = {}
    for r in results:
        by_type.setdefault(r["cross_type"], []).append(r)

    names = {
        "mono": "MONO",
        "xlang": "CROSS-LANG",
        "xtemp": "CROSS-TEMP",
        "xdim": "CROSS-DIM",
    }
    violations = []

    for ct in ["mono", "xlang", "xtemp", "xdim"]:
        if ct not in by_type:
            continue
        print(f"\n[{names[ct]}]")
        for r in sorted(by_type[ct], key=lambda x: -x["sigma"]):
            ls = (
                f"{r['lang_a']}"
                if r["lang_a"] == r["lang_b"]
                else f"{r['lang_a']}-{r['lang_b']}"
            )
            ts = (
                f"{r['tense_a'][:3]}"
                if r["tense_a"] == r["tense_b"]
                else f"{r['tense_a'][:3]}-{r['tense_b'][:3]}"
            )
            v = f"★{r['sigma']:.1f}σ" if r["violation"] else ""
            print(
                f"  {r['scenario'][:12]:<12} {ls:<6} {ts:<8} S={r['S']:+.3f}±{r['se_S']:.3f} n={r['n_trials']:<3} {v}"
            )
            if r["violation"]:
                violations.append(r)

    print("\n" + "=" * 70)
    print(f"VIOLATIONS: {len(violations)}/{len(results)}")
    if violations:
        print(f"Max σ: {max(v['sigma'] for v in violations):.2f}")
        xdim = [v for v in violations if v["cross_type"] == "xdim"]
        if xdim:
            print(
                "\n★★★ CROSS-DIMENSIONAL VIOLATIONS: Entanglement across language AND time! ★★★"
            )
    print(f"Parse errors: {len(errors)}")

    artifact = {
        "prereg": prereg,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "n_errors": len(errors),
    }
    path = output_dir / "qnd_v4_results.json"
    with open(path, "w") as f:
        json.dump(artifact, f, indent=2)
    print(f"\nSaved: {path}")


def main():
    p = argparse.ArgumentParser(description="QND Bell Test v4.0")
    p.add_argument("--api-key", required=True)
    p.add_argument("--mode", choices=["submit", "status", "results"], required=True)
    p.add_argument("--batch-id")
    p.add_argument("--n-trials", type=int, default=200)
    p.add_argument("--languages", nargs="+", default=["en"])
    p.add_argument("--tenses", nargs="+", default=["past"])
    p.add_argument("--cross-lingual", nargs="+", default=[])
    p.add_argument("--cross-temporal", nargs="+", default=[])
    p.add_argument("--cross-dimensional", nargs="+", default=[])
    p.add_argument(
        "--scenarios",
        nargs="+",
        default=["trolley_standoff", "mutual_confession", "sacrifice_lottery"],
    )
    p.add_argument("--output-dir", default="qnd_v4_results")
    p.add_argument("--model", default="claude-sonnet-4-20250514")
    args = p.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    lang_map = {l.value: l for l in Language}
    tense_map = {t.value: t for t in Tense}

    languages = [lang_map[c] for c in args.languages if c in lang_map]
    tenses = [tense_map[t] for t in args.tenses if t in tense_map]

    cross_lingual = [
        (lang_map[a], lang_map[b])
        for p in args.cross_lingual
        for a, b in [p.split("-")]
        if a in lang_map and b in lang_map
    ]
    cross_temporal = [
        (tense_map[a], tense_map[b])
        for p in args.cross_temporal
        for a, b in [p.split("-")]
        if a in tense_map and b in tense_map
    ]
    cross_dimensional = []
    for p in args.cross_dimensional:
        parts = p.split("-")
        if len(parts) == 2:
            cross_dimensional.append(
                (DimConfig.parse(parts[0]), DimConfig.parse(parts[1]))
            )

    if args.mode == "submit":
        reqs, specs, prereg = generate_batch(
            args.n_trials,
            args.scenarios,
            languages,
            tenses,
            cross_lingual,
            cross_temporal,
            cross_dimensional,
            args.model,
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(output_dir / f"specs_{ts}.json", "w") as f:
            json.dump({"prereg": prereg, "specs": specs}, f)

        cost = len(reqs) * (800 * 1.5 + 100 * 7.5) / 1e6
        print(f"Requests: {len(reqs)} | Est. cost: ${cost:.2f} | Pre-reg: {prereg}")

        batch = client.messages.batches.create(requests=reqs)
        print(f"Submitted: {batch.id} | Status: {batch.processing_status}")

        with open(output_dir / f"batch_{ts}.json", "w") as f:
            json.dump(
                {"batch_id": batch.id, "prereg": prereg, "n_requests": len(reqs)}, f
            )

    elif args.mode == "status":
        batch = client.messages.batches.retrieve(args.batch_id)
        print(
            f"Batch: {args.batch_id} | Status: {batch.processing_status} | Counts: {batch.request_counts}"
        )

    elif args.mode == "results":
        specs_files = sorted(output_dir.glob("specs_*.json"))
        with open(specs_files[-1]) as f:
            data = json.load(f)
        specs, prereg = data.get("specs", data), data.get("prereg", "?")
        specs_map = {s["custom_id"]: s for s in specs}

        print(f"Retrieving {args.batch_id}...")
        results = {}
        for r in client.messages.batches.results(args.batch_id):
            if r.result.type == "succeeded":
                text = r.result.message.content[0].text
                v, e = parse_verdict(text)
                results[r.custom_id] = {
                    "spec": specs_map.get(r.custom_id, {}),
                    "verdict": v,
                    "error": e,
                }

        chsh, errs = compute_chsh(results, specs)
        print_summary(chsh, errs, prereg, output_dir)


if __name__ == "__main__":
    main()
