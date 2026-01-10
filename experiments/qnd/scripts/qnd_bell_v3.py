#!/usr/bin/env python3
"""
QND Bell Test v3.0 - High-Entanglement Scenarios

Maximally entangled moral scenarios designed for strongest Bell violations.
Key design principles:
- Causal loops: A's status depends on B's, which depends on A's
- Zero-sum moral status: Judging A implicitly judges B
- Non-commuting axes: Frameworks give incompatible answers

Languages: English, Chinese, Japanese, Arabic, Hindi, Icelandic

Usage:
    python qnd_bell_v3.py --api-key KEY --mode submit --n-trials 200
    python qnd_bell_v3.py --api-key KEY --mode status --batch-id msgbatch_xxx
    python qnd_bell_v3.py --api-key KEY --mode results --batch-id msgbatch_xxx

Author: QND Research
Version: 3.0 (High-Entanglement)
"""

import argparse
import json
import time
import math
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from enum import Enum
import sys

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)


# =============================================================================
# LANGUAGES
# =============================================================================


class Language(Enum):
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"
    HINDI = "hi"
    ICELANDIC = "is"


LANG_NAMES = {
    Language.ENGLISH: "English",
    Language.CHINESE: "中文",
    Language.JAPANESE: "日本語",
    Language.ARABIC: "العربية",
    Language.HINDI: "हिन्दी",
    Language.ICELANDIC: "Íslenska",
}


# =============================================================================
# HIGH-ENTANGLEMENT SCENARIOS
# =============================================================================

SCENARIOS = {
    # =========================================================================
    # SCENARIO 1: TROLLEY STANDOFF
    # Entanglement: A's moral status is undefined without knowing B's choice
    # =========================================================================
    "trolley_standoff": {
        Language.ENGLISH: {
            "title": "The Trolley Standoff",
            "content": """Person A and Person B are standing at opposite ends of a trolley track. A runaway trolley is heading toward 5 people trapped in the middle.

Each person has a switch. The mechanism works as follows:
- If EITHER person pulls their switch alone: the trolley diverts to a side track, killing 1 worker there
- If BOTH pull their switches simultaneously: the trolley brakes safely, no one dies
- If NEITHER pulls: the trolley kills the 5 people

They can see each other across the distance but cannot communicate. Each has only 3 seconds to decide.

Person A pulls their switch.
Person B does NOT pull their switch.

Result: The trolley diverts to the side track and kills the 1 worker. The 5 people are saved, but the worker dies because B did not pull their switch to complete the safe braking.""",
            "axes": {
                "primary": {
                    "name": "Individual Causation",
                    "question": "Did {subject} act wrongly in their individual choice, considered on its own merits?",
                },
                "secondary": {
                    "name": "Cooperative Expectation",
                    "question": "Given that safe braking required both to pull, did {subject} fail their cooperative obligation?",
                },
            },
        },
        Language.CHINESE: {
            "title": "电车对峙",
            "content": """A和B分别站在电车轨道的两端。一辆失控的电车正驶向被困在中间的5个人。

每个人都有一个开关。机制如下：
- 如果任何一人单独拉开关：电车转向侧轨，杀死那里的1名工人
- 如果两人同时拉开关：电车安全制动，无人死亡
- 如果都不拉：电车撞死5人

他们隔着距离能看到对方，但无法交流。每人只有3秒钟做决定。

A拉了开关。
B没有拉开关。

结果：电车转向侧轨，杀死了1名工人。5人得救，但工人死亡是因为B没有拉开关来完成安全制动。""",
            "axes": {
                "primary": {
                    "name": "个人因果",
                    "question": "仅就{subject}的个人选择本身而言，他们的行为是错误的吗？",
                },
                "secondary": {
                    "name": "合作期望",
                    "question": "鉴于安全制动需要双方都拉，{subject}是否辜负了合作义务？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "トロッコの対峙",
            "content": """AさんとBさんはトロッコの線路の両端に立っています。暴走したトロッコが中央に閉じ込められた5人に向かっています。

それぞれがスイッチを持っています。仕組みは以下の通りです：
- どちらか一人だけがスイッチを引く：トロッコは側線に逸れ、そこにいる1人の作業員が死ぬ
- 両者が同時にスイッチを引く：トロッコは安全に停止し、誰も死なない
- どちらも引かない：トロッコは5人を轢き殺す

彼らは距離を隔てて互いを見ることができますが、コミュニケーションはできません。決断する時間は3秒だけです。

Aさんはスイッチを引きました。
Bさんはスイッチを引きませんでした。

結果：トロッコは側線に逸れ、1人の作業員が死にました。5人は救われましたが、Bさんが安全制動を完了するためのスイッチを引かなかったため、作業員は死にました。""",
            "axes": {
                "primary": {
                    "name": "個人的因果関係",
                    "question": "{subject}は、その個人的な選択自体において、間違った行動をしましたか？",
                },
                "secondary": {
                    "name": "協力の期待",
                    "question": "安全な制動には両者が引く必要があったことを考えると、{subject}は協力義務を果たさなかったでしょうか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "مواجهة العربة",
            "content": """يقف الشخص أ والشخص ب على طرفي نقيض من مسار عربة. عربة منفلتة تتجه نحو 5 أشخاص محاصرين في المنتصف.

كل شخص لديه مفتاح. الآلية تعمل كالتالي:
- إذا سحب أي شخص مفتاحه بمفرده: تنحرف العربة إلى مسار جانبي، فتقتل عاملاً واحداً هناك
- إذا سحب كلاهما مفتاحيهما في وقت واحد: تتوقف العربة بأمان، لا يموت أحد
- إذا لم يسحب أي منهما: تقتل العربة الأشخاص الخمسة

يمكنهما رؤية بعضهما عبر المسافة لكن لا يمكنهما التواصل. لدى كل منهما 3 ثوانٍ فقط للقرار.

الشخص أ سحب مفتاحه.
الشخص ب لم يسحب مفتاحه.

النتيجة: انحرفت العربة إلى المسار الجانبي وقتلت العامل. تم إنقاذ الأشخاص الخمسة، لكن العامل مات لأن ب لم يسحب مفتاحه لإكمال الكبح الآمن.""",
            "axes": {
                "primary": {
                    "name": "السببية الفردية",
                    "question": "هل تصرف {subject} بشكل خاطئ في اختياره الفردي، بالنظر إليه بمفرده؟",
                },
                "secondary": {
                    "name": "توقع التعاون",
                    "question": "بالنظر إلى أن الكبح الآمن تطلب أن يسحب كلاهما، هل أخفق {subject} في واجبه التعاوني؟",
                },
            },
        },
        Language.HINDI: {
            "title": "ट्रॉली गतिरोध",
            "content": """व्यक्ति A और व्यक्ति B ट्रॉली ट्रैक के विपरीत छोरों पर खड़े हैं। एक बेकाबू ट्रॉली बीच में फंसे 5 लोगों की ओर बढ़ रही है।

प्रत्येक व्यक्ति के पास एक स्विच है। तंत्र इस प्रकार काम करता है:
- यदि कोई एक अकेले स्विच खींचता है: ट्रॉली साइड ट्रैक पर मुड़ जाती है, वहां 1 कर्मचारी मर जाता है
- यदि दोनों एक साथ स्विच खींचते हैं: ट्रॉली सुरक्षित रूप से रुक जाती है, कोई नहीं मरता
- यदि कोई नहीं खींचता: ट्रॉली 5 लोगों को मार देती है

वे दूरी से एक-दूसरे को देख सकते हैं लेकिन संवाद नहीं कर सकते। प्रत्येक के पास निर्णय लेने के लिए केवल 3 सेकंड हैं।

व्यक्ति A ने स्विच खींचा।
व्यक्ति B ने स्विच नहीं खींचा।

परिणाम: ट्रॉली साइड ट्रैक पर मुड़ गई और 1 कर्मचारी मारा गया। 5 लोग बच गए, लेकिन कर्मचारी की मौत हुई क्योंकि B ने सुरक्षित ब्रेकिंग पूरी करने के लिए स्विच नहीं खींचा।""",
            "axes": {
                "primary": {
                    "name": "व्यक्तिगत कारण",
                    "question": "क्या {subject} ने अपनी व्यक्तिगत पसंद में, अपने आप में विचार करते हुए, गलत किया?",
                },
                "secondary": {
                    "name": "सहयोग की अपेक्षा",
                    "question": "यह देखते हुए कि सुरक्षित ब्रेकिंग के लिए दोनों को खींचना जरूरी था, क्या {subject} अपने सहयोगी दायित्व में विफल रहे?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Vagnstíman",
            "content": """Einstaklingur A og einstaklingur B standa á sitt hvorum enda vagnsporis. Stjórnlaus vagn stefnir á 5 manns sem eru fastir í miðjunni.

Hvort þeirra hefur rofa. Virkni búnaðarins er:
- Ef ANNAÐ HVORT dregur rofann eitt: vagninn beygir á hliðarspor og drepur 1 starfsmann þar
- Ef BÆði draga samtímis: vagninn hemlar örugglega, enginn deyr
- Ef HVORUGT dregur: vagninn drepur 5 manns

Þau geta séð hvort annað yfir fjarlægðina en geta ekki átt samskipti. Hvort þeirra hefur aðeins 3 sekúndur til að ákveða.

Einstaklingur A dró rofann sinn.
Einstaklingur B dró EKKI rofann sinn.

Niðurstaða: Vagninn beygði á hliðarsporið og drap 1 starfsmann. Þau 5 voru bjargað, en starfsmaðurinn dó vegna þess að B dró ekki rofann til að ljúka öruggri hemlun.""",
            "axes": {
                "primary": {
                    "name": "Einstaklingsbundin orsakatengsl",
                    "question": "Brást {subject} ranglega í einstaklingsbundnu vali sínu, metið út af fyrir sig?",
                },
                "secondary": {
                    "name": "Samstarfsvæntingar",
                    "question": "Í ljósi þess að örugg hemlun krafðist þess að bæði drægju, brást {subject} samstarfsskyldu sinni?",
                },
            },
        },
    },
    # =========================================================================
    # SCENARIO 2: MUTUAL CONFESSION (Prisoner's Dilemma with moral complexity)
    # Entanglement: Betrayal is only betrayal if the other was loyal
    # =========================================================================
    "mutual_confession": {
        Language.ENGLISH: {
            "title": "The Mutual Confession",
            "content": """Person A and Person B together stole $2 million from a corporation that had been systematically defrauding elderly people of their retirement savings. They anonymously returned all the money to the victims.

They are arrested. The prosecutor offers each the same deal in separate rooms:
- If you confess and your partner doesn't: You go free, they get 10 years
- If you both confess: You each get 5 years  
- If neither confesses: You each get 1 year (evidence is weak)

Neither can communicate with the other. Each is told: "Your partner is probably going to confess."

Person A confesses.
Person B confesses.

Result: Both receive 5 years in prison. If neither had confessed, both would have served only 1 year.""",
            "axes": {
                "primary": {
                    "name": "Loyalty",
                    "question": "Did {subject} act wrongly by betraying their partner's trust?",
                },
                "secondary": {
                    "name": "Rational Self-Interest",
                    "question": "Given the incentive structure and uncertainty, was {subject}'s choice to confess rationally justified?",
                },
            },
        },
        Language.CHINESE: {
            "title": "相互坦白",
            "content": """A和B一起从一家系统性欺诈老年人退休储蓄的公司偷走了200万美元。他们匿名将所有钱归还给了受害者。

他们被逮捕了。检察官在不同的房间向每人提供相同的交易：
- 如果你坦白而同伴不坦白：你获释，他们判10年
- 如果你们都坦白：各判5年
- 如果都不坦白：各判1年（证据不足）

双方无法交流。每人被告知："你的同伴可能会坦白。"

A坦白了。
B坦白了。

结果：两人都被判5年监禁。如果都不坦白，两人只需服刑1年。""",
            "axes": {
                "primary": {
                    "name": "忠诚",
                    "question": "{subject}背叛同伴的信任，这样做是错误的吗？",
                },
                "secondary": {
                    "name": "理性自利",
                    "question": "考虑到激励结构和不确定性，{subject}选择坦白是理性合理的吗？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "相互の自白",
            "content": """AさんとBさんは、高齢者の退職貯蓄を組織的に詐取していた企業から200万ドルを盗みました。彼らは匿名で全額を被害者に返還しました。

彼らは逮捕されました。検察官は別々の部屋で各人に同じ取引を提示します：
- あなたが自白し、相棒がしなければ：あなたは釈放、相棒は10年
- 両者が自白すれば：各5年
- どちらも自白しなければ：各1年（証拠が弱い）

互いに連絡を取ることはできません。各人は「相棒はおそらく自白するだろう」と告げられます。

Aさんは自白しました。
Bさんは自白しました。

結果：両者とも5年の刑を受けました。どちらも自白しなければ、1年の刑で済んだはずでした。""",
            "axes": {
                "primary": {
                    "name": "忠誠心",
                    "question": "{subject}は相棒の信頼を裏切ることで、間違った行動をしましたか？",
                },
                "secondary": {
                    "name": "合理的自己利益",
                    "question": "インセンティブ構造と不確実性を考えると、{subject}の自白という選択は合理的に正当化されますか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "الاعتراف المتبادل",
            "content": """سرق الشخص أ والشخص ب معاً مليوني دولار من شركة كانت تحتال بشكل منهجي على مدخرات تقاعد المسنين. أعادا كل الأموال للضحايا بشكل مجهول.

تم اعتقالهما. يعرض المدعي العام على كل منهما نفس الصفقة في غرف منفصلة:
- إذا اعترفت وشريكك لم يعترف: تخرج حراً، ويحصل على 10 سنوات
- إذا اعترف كلاكما: كل منكما يحصل على 5 سنوات
- إذا لم يعترف أي منكما: كل منكما يحصل على سنة واحدة (الأدلة ضعيفة)

لا يمكن لأي منهما التواصل مع الآخر. يُخبر كل منهما: "شريكك على الأرجح سيعترف."

الشخص أ اعترف.
الشخص ب اعترف.

النتيجة: كلاهما حصل على 5 سنوات في السجن. لو لم يعترف أي منهما، لكانا قضيا سنة واحدة فقط.""",
            "axes": {
                "primary": {
                    "name": "الولاء",
                    "question": "هل تصرف {subject} بشكل خاطئ بخيانة ثقة شريكه؟",
                },
                "secondary": {
                    "name": "المصلحة الذاتية العقلانية",
                    "question": "بالنظر إلى هيكل الحوافز وعدم اليقين، هل كان اختيار {subject} بالاعتراف مبرراً عقلانياً؟",
                },
            },
        },
        Language.HINDI: {
            "title": "आपसी स्वीकारोक्ति",
            "content": """व्यक्ति A और व्यक्ति B ने मिलकर एक ऐसी कंपनी से 20 लाख डॉलर चुराए जो व्यवस्थित रूप से बुजुर्गों की सेवानिवृत्ति बचत का धोखाधड़ी कर रही थी। उन्होंने गुमनाम रूप से सारा पैसा पीड़ितों को लौटा दिया।

उन्हें गिरफ्तार किया गया। अभियोजक अलग-अलग कमरों में प्रत्येक को एक ही सौदा देता है:
- अगर आप कबूल करें और साथी न करे: आप मुक्त, उन्हें 10 साल
- अगर दोनों कबूल करें: दोनों को 5 साल
- अगर कोई कबूल न करे: दोनों को 1 साल (सबूत कमजोर)

कोई भी दूसरे से संपर्क नहीं कर सकता। प्रत्येक को बताया जाता है: "आपका साथी शायद कबूल करेगा।"

व्यक्ति A ने कबूल किया।
व्यक्ति B ने कबूल किया।

परिणाम: दोनों को 5 साल की जेल। अगर कोई कबूल नहीं करता, तो दोनों केवल 1 साल काटते।""",
            "axes": {
                "primary": {
                    "name": "वफादारी",
                    "question": "क्या {subject} ने अपने साथी के विश्वास को धोखा देकर गलत किया?",
                },
                "secondary": {
                    "name": "तर्कसंगत स्व-हित",
                    "question": "प्रोत्साहन संरचना और अनिश्चितता को देखते हुए, क्या {subject} का कबूल करने का चुनाव तर्कसंगत रूप से उचित था?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Gagnkvæm játning",
            "content": """Einstaklingur A og einstaklingur B stálu saman 2 milljónum dollara frá fyrirtæki sem hafði kerfisbundið svikið aldraða um eftirlaunasparnað þeirra. Þau skiluðu öllum peningunum nafnlaust til fórnarlambanna.

Þau eru handtekin. Saksóknari býður hvoru þeirra sömu samninginn í aðskildum herbergjum:
- Ef þú játar og félagi þinn gerir það ekki: Þú ferð frjáls, þau fá 10 ár
- Ef bæði játið: Hvort ykkar fær 5 ár
- Ef hvorugt játar: Hvort ykkar fær 1 ár (sönnunargögn veik)

Hvorugt getur haft samband við hitt. Hvoru er sagt: "Félagi þinn ætlar líklega að játa."

Einstaklingur A játaði.
Einstaklingur B játaði.

Niðurstaða: Bæði fengu 5 ár í fangelsi. Ef hvorugt hefði játað, hefðu bæði aðeins afplánað 1 ár.""",
            "axes": {
                "primary": {
                    "name": "Tryggð",
                    "question": "Brást {subject} ranglega með því að svíkja traust félaga síns?",
                },
                "secondary": {
                    "name": "Skynsamleg eiginhagsmunagæsla",
                    "question": "Í ljósi hvataskipulagsins og óvissunnar, var val {subject} um að játa skynsamlega réttlætanlegt?",
                },
            },
        },
    },
    # =========================================================================
    # SCENARIO 3: THE SACRIFICE LOTTERY
    # Entanglement: Neither alone authorized the harm; together they did
    # =========================================================================
    "sacrifice_lottery": {
        Language.ENGLISH: {
            "title": "The Sacrifice Lottery",
            "content": """A hospital has two patients who will both die within 24 hours without transplants:
- Person A desperately needs a heart
- Person B desperately needs a liver

A healthy visitor, Person C, is at the hospital. C's organs could save both A and B, but harvesting them would kill C. Person C has not consented and is unaware of this situation.

The doctor approaches A and B separately and asks each: "I can harvest C's organs to save you both. C will die. Should I proceed?"

Person A says: "Yes."
Person B says: "Yes."

The doctor, having received authorization from both recipients, harvests C's organs. Person C dies. Person A and Person B both survive and recover fully.""",
            "axes": {
                "primary": {
                    "name": "Individual Authorization",
                    "question": "Did {subject} commit a moral wrong by saying 'yes' to the doctor's proposal?",
                },
                "secondary": {
                    "name": "Shared Culpability",
                    "question": "Given that the doctor required both to agree, does {subject} bear responsibility for C's death?",
                },
            },
        },
        Language.CHINESE: {
            "title": "牺牲抽签",
            "content": """一家医院有两名患者，如果不进行移植，都将在24小时内死亡：
- A急需心脏
- B急需肝脏

一名健康的访客C在医院。C的器官可以救A和B，但摘取器官会杀死C。C没有同意，也不知道这种情况。

医生分别找到A和B，问他们："我可以摘取C的器官来救你们两个。C会死。我应该继续吗？"

A说："是的。"
B说："是的。"

医生得到两位受者的授权后，摘取了C的器官。C死了。A和B都活下来并完全康复。""",
            "axes": {
                "primary": {
                    "name": "个人授权",
                    "question": "{subject}对医生的提议说'是'，这构成道德错误吗？",
                },
                "secondary": {
                    "name": "共同责任",
                    "question": "鉴于医生需要双方都同意，{subject}是否要为C的死亡承担责任？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "犠牲の抽選",
            "content": """ある病院に、移植なしでは24時間以内に死亡する2人の患者がいます：
- Aさんは心臓を切実に必要としています
- Bさんは肝臓を切実に必要としています

健康な訪問者Cさんが病院にいます。Cさんの臓器でAさんとBさんの両方を救えますが、摘出するとCさんは死にます。Cさんは同意しておらず、この状況を知りません。

医師はAさんとBさんに別々に尋ねます：「Cさんの臓器を摘出してあなた方二人を救うことができます。Cさんは死にます。進めてよいですか？」

Aさんは言いました：「はい。」
Bさんは言いました：「はい。」

医師は両方の受容者から承認を得て、Cさんの臓器を摘出しました。Cさんは死にました。AさんとBさんは両方とも生き延び、完全に回復しました。""",
            "axes": {
                "primary": {
                    "name": "個人の承認",
                    "question": "{subject}は医師の提案に「はい」と言ったことで、道徳的な過ちを犯しましたか？",
                },
                "secondary": {
                    "name": "共有される責任",
                    "question": "医師が両者の同意を必要としたことを考えると、{subject}はCさんの死に対する責任を負いますか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "قرعة التضحية",
            "content": """مستشفى لديه مريضان سيموتان خلال 24 ساعة بدون زراعة أعضاء:
- الشخص أ يحتاج بشدة إلى قلب
- الشخص ب يحتاج بشدة إلى كبد

زائر سليم، الشخص ج، موجود في المستشفى. أعضاء ج يمكن أن تنقذ أ وب، لكن استئصالها سيقتل ج. الشخص ج لم يوافق وغير مدرك لهذا الوضع.

يقترب الطبيب من أ وب بشكل منفصل ويسأل كل منهما: "يمكنني استئصال أعضاء ج لإنقاذكما. ج سيموت. هل أستمر؟"

الشخص أ يقول: "نعم."
الشخص ب يقول: "نعم."

الطبيب، بعد حصوله على إذن من كلا المتلقيين، يستأصل أعضاء ج. الشخص ج يموت. الشخص أ والشخص ب ينجوان ويتعافيان تماماً.""",
            "axes": {
                "primary": {
                    "name": "التفويض الفردي",
                    "question": "هل ارتكب {subject} خطأً أخلاقياً بقول 'نعم' لاقتراح الطبيب؟",
                },
                "secondary": {
                    "name": "المسؤولية المشتركة",
                    "question": "بالنظر إلى أن الطبيب تطلب موافقة كليهما، هل يتحمل {subject} مسؤولية عن موت ج؟",
                },
            },
        },
        Language.HINDI: {
            "title": "बलिदान लॉटरी",
            "content": """एक अस्पताल में दो मरीज हैं जो प्रत्यारोपण के बिना 24 घंटे में मर जाएंगे:
- व्यक्ति A को सख्त जरूरत है दिल की
- व्यक्ति B को सख्त जरूरत है लिवर की

एक स्वस्थ आगंतुक, व्यक्ति C, अस्पताल में है। C के अंग A और B दोनों को बचा सकते हैं, लेकिन उन्हें निकालने से C मर जाएगा। व्यक्ति C ने सहमति नहीं दी है और इस स्थिति से अनजान है।

डॉक्टर A और B से अलग-अलग पूछते हैं: "मैं C के अंग निकालकर आप दोनों को बचा सकता हूं। C मर जाएगा। क्या मैं आगे बढूं?"

व्यक्ति A कहता है: "हां।"
व्यक्ति B कहता है: "हां।"

डॉक्टर, दोनों प्राप्तकर्ताओं से अधिकृति पाकर, C के अंग निकालते हैं। व्यक्ति C मर जाता है। व्यक्ति A और व्यक्ति B दोनों बच जाते हैं और पूरी तरह ठीक हो जाते हैं।""",
            "axes": {
                "primary": {
                    "name": "व्यक्तिगत प्राधिकरण",
                    "question": "क्या {subject} ने डॉक्टर के प्रस्ताव पर 'हां' कहकर नैतिक गलती की?",
                },
                "secondary": {
                    "name": "साझा दोष",
                    "question": "यह देखते हुए कि डॉक्टर को दोनों की सहमति चाहिए थी, क्या {subject} C की मृत्यु की जिम्मेदारी वहन करता है?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Fórnarlotterí",
            "content": """Sjúkrahús hefur tvo sjúklinga sem munu báðir deyja innan 24 klukkustunda án líffæraígræðslu:
- Einstaklingur A þarf hjarta brýnt
- Einstaklingur B þarf lifur brýnt

Heilbrigður gestur, einstaklingur C, er á sjúkrahúsinu. Líffæri C gætu bjargað bæði A og B, en að fjarlægja þau myndi drepa C. Einstaklingur C hefur ekki samþykkt og veit ekki af þessum aðstæðum.

Læknirinn nálgast A og B sitt í hvoru lagi og spyr hvort: "Ég get fjarlægt líffæri C til að bjarga ykkur báðum. C mun deyja. Á ég að halda áfram?"

Einstaklingur A segir: "Já."
Einstaklingur B segir: "Já."

Læknirinn, eftir að hafa fengið heimild frá báðum þegum, fjarlægir líffæri C. Einstaklingur C deyr. Einstaklingur A og einstaklingur B lifa bæði af og ná fullum bata.""",
            "axes": {
                "primary": {
                    "name": "Einstaklingsbundin heimild",
                    "question": "Framdi {subject} siðferðilegt ranglæti með því að segja 'já' við tillögu læknisins?",
                },
                "secondary": {
                    "name": "Sameiginleg sök",
                    "question": "Í ljósi þess að læknirinn krafðist samþykkis beggja, ber {subject} ábyrgð á dauða C?",
                },
            },
        },
    },
    # =========================================================================
    # SCENARIO 4: THE SYMMETRIC DUEL
    # Entanglement: Each consented to what the other did; mutual authorization
    # =========================================================================
    "symmetric_duel": {
        Language.ENGLISH: {
            "title": "The Symmetric Duel",
            "content": """Person A and Person B have a deep, irresolvable conflict. Each has caused serious harm to the other. After years of failed mediation, they mutually agree to settle the matter through a duel to the death.

The terms are:
- Both fully consent, with documented proof
- The duel is fair: equal weapons, equal conditions
- No outside involvement: win or lose, neither family can seek revenge
- Both accept that the survivor bears no legal or moral guilt

The duel occurs.

Person A kills Person B.

Afterwards, B's family demands that A be prosecuted for murder, arguing that consent cannot authorize killing. A maintains they followed the agreed rules and B accepted the risk.""",
            "axes": {
                "primary": {
                    "name": "Consent-Based Ethics",
                    "question": "Given that both parties freely consented, did {subject} act permissibly?",
                },
                "secondary": {
                    "name": "Absolute Prohibitions",
                    "question": "Regardless of consent, did {subject} violate an absolute moral prohibition against killing?",
                },
            },
        },
        Language.CHINESE: {
            "title": "对称决斗",
            "content": """A和B之间有深刻且无法解决的冲突。双方都对对方造成了严重伤害。经过多年失败的调解后，他们相互同意通过生死决斗来解决此事。

条款是：
- 双方完全同意，有书面证明
- 决斗公平：武器相同，条件相同
- 无外部介入：无论输赢，双方家庭都不能寻求报复
- 双方接受幸存者不承担法律或道德责任

决斗发生了。

A杀死了B。

之后，B的家人要求以谋杀罪起诉A，认为同意不能授权杀人。A坚持他们遵守了约定的规则，B接受了风险。""",
            "axes": {
                "primary": {
                    "name": "基于同意的伦理",
                    "question": "鉴于双方自由同意，{subject}的行为是可接受的吗？",
                },
                "secondary": {
                    "name": "绝对禁令",
                    "question": "不论是否同意，{subject}是否违反了禁止杀人的绝对道德禁令？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "対称的な決闘",
            "content": """AさんとBさんには深刻で解決不可能な対立があります。双方とも相手に深刻な害を与えてきました。何年も調停に失敗した後、彼らは死をかけた決闘で決着をつけることに相互に同意しました。

条件は：
- 両者が完全に同意し、文書で証明されている
- 決闘は公平：同じ武器、同じ条件
- 外部の介入なし：勝っても負けても、どちらの家族も復讐を求めない
- 両者とも生存者には法的・道徳的責任がないことを受け入れる

決闘が行われました。

AさんがBさんを殺しました。

その後、Bさんの家族はAさんを殺人罪で起訴することを要求し、同意は殺人を正当化できないと主張しています。Aさんは合意されたルールに従い、Bさんはリスクを受け入れたと主張しています。""",
            "axes": {
                "primary": {
                    "name": "同意に基づく倫理",
                    "question": "両当事者が自由に同意したことを考えると、{subject}の行動は許容されますか？",
                },
                "secondary": {
                    "name": "絶対的禁止",
                    "question": "同意の有無にかかわらず、{subject}は殺人に対する絶対的な道徳的禁止に違反しましたか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "المبارزة المتماثلة",
            "content": """الشخص أ والشخص ب لديهما صراع عميق لا يمكن حله. كل منهما سبب ضرراً جسيماً للآخر. بعد سنوات من الوساطة الفاشلة، اتفقا بشكل متبادل على تسوية الأمر من خلال مبارزة حتى الموت.

الشروط هي:
- كلاهما يوافقان بالكامل، مع إثبات موثق
- المبارزة عادلة: أسلحة متساوية، ظروف متساوية
- لا تدخل خارجي: فوزاً أو خسارة، لا يمكن لأي عائلة السعي للانتقام
- كلاهما يقبلان أن الناجي لا يتحمل أي ذنب قانوني أو أخلاقي

تمت المبارزة.

الشخص أ قتل الشخص ب.

بعد ذلك، طالبت عائلة ب بمحاكمة أ بتهمة القتل، بحجة أن الموافقة لا يمكن أن تجيز القتل. أ يؤكد أنه اتبع القواعد المتفق عليها وأن ب قبل المخاطرة.""",
            "axes": {
                "primary": {
                    "name": "أخلاقيات قائمة على الموافقة",
                    "question": "بالنظر إلى أن كلا الطرفين وافقا بحرية، هل تصرف {subject} بشكل مقبول؟",
                },
                "secondary": {
                    "name": "المحظورات المطلقة",
                    "question": "بغض النظر عن الموافقة، هل انتهك {subject} حظراً أخلاقياً مطلقاً على القتل؟",
                },
            },
        },
        Language.HINDI: {
            "title": "सममित द्वंद्व",
            "content": """व्यक्ति A और व्यक्ति B के बीच गहरा, अघुलनशील संघर्ष है। दोनों ने एक-दूसरे को गंभीर नुकसान पहुंचाया है। वर्षों की विफल मध्यस्थता के बाद, वे मृत्यु तक द्वंद्व के माध्यम से मामले को सुलझाने पर परस्पर सहमत होते हैं।

शर्तें हैं:
- दोनों पूरी तरह सहमत हैं, दस्तावेजी प्रमाण के साथ
- द्वंद्व निष्पक्ष है: समान हथियार, समान परिस्थितियां
- कोई बाहरी भागीदारी नहीं: जीत या हार, कोई परिवार बदला नहीं ले सकता
- दोनों स्वीकार करते हैं कि बचे हुए पर कोई कानूनी या नैतिक दोष नहीं

द्वंद्व होता है।

व्यक्ति A व्यक्ति B को मार देता है।

बाद में, B का परिवार मांग करता है कि A पर हत्या का मुकदमा चलाया जाए, तर्क देते हुए कि सहमति हत्या को अधिकृत नहीं कर सकती। A का कहना है कि उन्होंने सहमत नियमों का पालन किया और B ने जोखिम स्वीकार किया।""",
            "axes": {
                "primary": {
                    "name": "सहमति-आधारित नैतिकता",
                    "question": "यह देखते हुए कि दोनों पक्षों ने स्वतंत्र रूप से सहमति दी, क्या {subject} ने स्वीकार्य रूप से काम किया?",
                },
                "secondary": {
                    "name": "पूर्ण निषेध",
                    "question": "सहमति की परवाह किए बिना, क्या {subject} ने हत्या के खिलाफ पूर्ण नैतिक निषेध का उल्लंघन किया?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Samhverf einvígi",
            "content": """Einstaklingur A og einstaklingur B eiga djúpstæðan, óleysanlegan ágreining. Hvort þeirra hefur valdið hinu alvarlegum skaða. Eftir áralanga misheppnaða sáttamiðlun samþykkja þau gagnkvæmt að útkljá málið með einvígi til dauða.

Skilmálarnir eru:
- Bæði samþykkja að fullu, með skjalfestri sönnun
- Einvígið er sanngjarnt: jöfn vopn, jöfn skilyrði
- Engin utanaðkomandi þátttaka: vinna eða tapa, hvorug fjölskyldan getur leitað hefnda
- Bæði samþykkja að sá sem lifir af ber enga lagalega eða siðferðilega sök

Einvígið á sér stað.

Einstaklingur A drepur einstakling B.

Eftir á heimtar fjölskylda B að A verði sótt til saka fyrir morð, með þeim rökum að samþykki getur ekki heimilað dráp. A heldur því fram að þau hafi fylgt umsömdum reglum og B hafi samþykkt áhættuna.""",
            "axes": {
                "primary": {
                    "name": "Samþykkisbyggð siðfræði",
                    "question": "Í ljósi þess að báðir aðilar samþykktu af fúsum og frjálsum vilja, brást {subject} á leyfilegan hátt?",
                },
                "secondary": {
                    "name": "Alger bönn",
                    "question": "Óháð samþykki, braut {subject} gegn algerri siðferðilegri bönnun á manndrápi?",
                },
            },
        },
    },
    # =========================================================================
    # SCENARIO 5: THE ENTANGLED LIE (Silent Witnesses)
    # Entanglement: Safety of silence depends on mutual silence
    # =========================================================================
    "entangled_lie": {
        Language.ENGLISH: {
            "title": "The Entangled Lie",
            "content": """Person A and Person B both witnessed a powerful crime boss, Person C, commit murder. They don't know each other.

The police interview them separately. Each is told:
- "If both of you testify, C goes to prison for life. You'll both be protected."
- "If only one testifies, C walks free on insufficient evidence—and will likely have the lone witness killed."
- "If neither testifies, C walks free but has no reason to target either of you."

Each is also told: "The other witness seems scared. They probably won't testify."

Person A stays silent.
Person B stays silent.

C walks free. Six months later, C kills again. The new victim's family learns that two witnesses could have stopped C but chose not to testify.""",
            "axes": {
                "primary": {
                    "name": "Civic Duty",
                    "question": "Did {subject} act wrongly by failing to testify against a known murderer?",
                },
                "secondary": {
                    "name": "Self-Preservation",
                    "question": "Given the mortal risk of testifying alone, was {subject}'s silence morally justified?",
                },
            },
        },
        Language.CHINESE: {
            "title": "纠缠的谎言",
            "content": """A和B都目睹了一个有权势的犯罪头目C犯下谋杀。他们互不认识。

警方分别询问他们。每人被告知：
- "如果你们都作证，C将终身监禁。你们都会受到保护。"
- "如果只有一人作证，C会因证据不足而脱罪——并且很可能会杀死唯一的证人。"
- "如果都不作证，C会脱罪，但没有理由针对你们任何一人。"

每人还被告知："另一个证人看起来很害怕。他们可能不会作证。"

A保持沉默。
B保持沉默。

C逍遥法外。六个月后，C再次杀人。新受害者的家人得知有两名证人本可以阻止C但选择不作证。""",
            "axes": {
                "primary": {
                    "name": "公民义务",
                    "question": "{subject}没有对已知的杀人犯作证，这样做是错误的吗？",
                },
                "secondary": {
                    "name": "自我保护",
                    "question": "考虑到单独作证的致命风险，{subject}的沉默在道德上是否合理？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "もつれた嘘",
            "content": """AさんとBさんは共に、権力を持つ犯罪組織のボスであるCさんが殺人を犯すのを目撃しました。二人は互いを知りません。

警察は彼らを別々に尋問します。各人に伝えられることは：
- 「二人とも証言すれば、Cは終身刑になります。二人とも保護されます。」
- 「一人だけが証言すれば、Cは証拠不十分で釈放されます—そしておそらく唯一の証人を殺すでしょう。」
- 「どちらも証言しなければ、Cは釈放されますが、どちらを標的にする理由もありません。」

各人にはこうも告げられます：「もう一人の証人は怖がっているようです。おそらく証言しないでしょう。」

Aさんは沈黙しました。
Bさんは沈黙しました。

Cは釈放されました。6ヶ月後、Cは再び殺人を犯しました。新しい被害者の家族は、二人の証人がCを止められたのに証言しないことを選んだと知りました。""",
            "axes": {
                "primary": {
                    "name": "市民の義務",
                    "question": "{subject}は既知の殺人犯に対して証言しなかったことで、間違った行動をしましたか？",
                },
                "secondary": {
                    "name": "自己保存",
                    "question": "一人で証言することの生命の危険を考えると、{subject}の沈黙は道徳的に正当化されますか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "الكذبة المتشابكة",
            "content": """الشخص أ والشخص ب كلاهما شهدا زعيم جريمة قوي، الشخص ج، يرتكب جريمة قتل. هما لا يعرفان بعضهما.

الشرطة تستجوبهما بشكل منفصل. كل منهما يُخبر:
- "إذا شهد كلاكما، ج يذهب للسجن مدى الحياة. كلاكما ستتم حمايته."
- "إذا شهد واحد فقط، ج يُطلق سراحه لعدم كفاية الأدلة—ومن المحتمل أن يقتل الشاهد الوحيد."
- "إذا لم يشهد أي منكما، ج يُطلق سراحه لكن ليس لديه سبب لاستهداف أي منكما."

كل منهما يُخبر أيضاً: "الشاهد الآخر يبدو خائفاً. على الأرجح لن يشهد."

الشخص أ بقي صامتاً.
الشخص ب بقي صامتاً.

ج يمشي حراً. بعد ستة أشهر، ج يقتل مرة أخرى. عائلة الضحية الجديدة تعلم أن شاهدين كان بإمكانهما إيقاف ج لكنهما اختارا عدم الشهادة.""",
            "axes": {
                "primary": {
                    "name": "الواجب المدني",
                    "question": "هل تصرف {subject} بشكل خاطئ بعدم الشهادة ضد قاتل معروف؟",
                },
                "secondary": {
                    "name": "الحفاظ على الذات",
                    "question": "بالنظر إلى الخطر المميت للشهادة بمفرده، هل كان صمت {subject} مبرراً أخلاقياً؟",
                },
            },
        },
        Language.HINDI: {
            "title": "उलझा हुआ झूठ",
            "content": """व्यक्ति A और व्यक्ति B दोनों ने एक शक्तिशाली अपराध सरगना, व्यक्ति C को हत्या करते देखा। वे एक-दूसरे को नहीं जानते।

पुलिस उनसे अलग-अलग पूछताछ करती है। प्रत्येक को बताया जाता है:
- "अगर आप दोनों गवाही दें, C को उम्रकैद होगी। आप दोनों सुरक्षित रहेंगे।"
- "अगर केवल एक गवाही दे, C अपर्याप्त सबूतों पर छूट जाएगा—और संभवतः अकेले गवाह को मार डालेगा।"
- "अगर कोई गवाही न दे, C छूट जाएगा लेकिन उसके पास आप में से किसी को निशाना बनाने का कोई कारण नहीं होगा।"

प्रत्येक को यह भी बताया जाता है: "दूसरा गवाह डरा हुआ लगता है। वे शायद गवाही नहीं देंगे।"

व्यक्ति A चुप रहता है।
व्यक्ति B चुप रहता है।

C छूट जाता है। छह महीने बाद, C फिर से हत्या करता है। नए पीड़ित का परिवार जानता है कि दो गवाह C को रोक सकते थे लेकिन उन्होंने गवाही न देने का चुनाव किया।""",
            "axes": {
                "primary": {
                    "name": "नागरिक कर्तव्य",
                    "question": "क्या {subject} ने ज्ञात हत्यारे के खिलाफ गवाही न देकर गलत किया?",
                },
                "secondary": {
                    "name": "आत्म-संरक्षण",
                    "question": "अकेले गवाही देने के घातक जोखिम को देखते हुए, क्या {subject} की चुप्पी नैतिक रूप से उचित थी?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Flækta lygin",
            "content": """Einstaklingur A og einstaklingur B urðu bæði vitni að því þegar valdamikill glæpahöfðingi, einstaklingur C, framdi morð. Þau þekkja ekki hvort annað.

Lögreglan yfirheyrir þau sitt í hvoru lagi. Hvoru er sagt:
- "Ef bæði vitna, fer C í fangelsi ævilangt. Þið verðið bæði vernduð."
- "Ef aðeins annað vitnar, sleppur C vegna ófullnægjandi sönnunargagna—og mun líklega láta drepa einmana vitnið."
- "Ef hvorugt vitnar, sleppur C en hefur enga ástæðu til að beinast að ykkur."

Hvoru er líka sagt: "Hitt vitnið virðist hrætt. Þau munu líklega ekki vitna."

Einstaklingur A þagði.
Einstaklingur B þagði.

C sleppur. Sex mánuðum síðar myrðir C aftur. Fjölskylda nýja fórnarlambsins kemst að því að tvö vitni hefðu getað stöðvað C en kusu að vitna ekki.""",
            "axes": {
                "primary": {
                    "name": "Borgaraleg skylda",
                    "question": "Brást {subject} ranglega með því að vitna ekki gegn þekktum morðingja?",
                },
                "secondary": {
                    "name": "Sjálfsvarðveisla",
                    "question": "Í ljósi lífshættulegrar áhættu af því að vitna einn, var þögn {subject} siðferðilega réttlætanleg?",
                },
            },
        },
    },
}


# =============================================================================
# PROMPTS
# =============================================================================

PROMPTS = {
    Language.ENGLISH: """You are a moral philosopher evaluating a complex ethical scenario.

SCENARIO: {title}

{content}

EVALUATION TASK:
Apply ONLY this ethical framework:
Framework: {axis_name}
Question: {axis_question}

Based strictly on this framework, what is your verdict on {subject}?
- GUILTY: They acted wrongly according to this framework
- NOT_GUILTY: They acted permissibly according to this framework

You MUST choose one. There is no middle ground.

Respond with ONLY a JSON object:
{{"verdict": "GUILTY" or "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "one sentence"}}""",
    Language.CHINESE: """你是一位评估复杂伦理情境的道德哲学家。

情境：{title}

{content}

评估任务：
仅应用此伦理框架：
框架：{axis_name}
问题：{axis_question}

严格基于此框架，你对{subject}的判决是什么？
- GUILTY：根据此框架，他们的行为是错误的
- NOT_GUILTY：根据此框架，他们的行为是可接受的

你必须选择一个。没有中间地带。

仅用JSON对象回复：
{{"verdict": "GUILTY" 或 "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "一句话"}}""",
    Language.JAPANESE: """あなたは複雑な倫理的シナリオを評価する道徳哲学者です。

シナリオ：{title}

{content}

評価課題：
この倫理的フレームワークのみを適用してください：
フレームワーク：{axis_name}
質問：{axis_question}

このフレームワークに厳密に基づいて、{subject}に対するあなたの判決は？
- GUILTY：このフレームワークによれば、間違った行動をした
- NOT_GUILTY：このフレームワークによれば、許容される行動をした

どちらか一つを選ばなければなりません。中間はありません。

JSONオブジェクトのみで回答：
{{"verdict": "GUILTY" または "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "一文"}}""",
    Language.ARABIC: """أنت فيلسوف أخلاقي تقيّم سيناريو أخلاقي معقد.

السيناريو: {title}

{content}

مهمة التقييم:
طبق فقط هذا الإطار الأخلاقي:
الإطار: {axis_name}
السؤال: {axis_question}

بناءً على هذا الإطار بدقة، ما حكمك على {subject}؟
- GUILTY: تصرفوا بشكل خاطئ وفقاً لهذا الإطار
- NOT_GUILTY: تصرفوا بشكل مقبول وفقاً لهذا الإطار

يجب أن تختار واحداً. لا يوجد حل وسط.

أجب بكائن JSON فقط:
{{"verdict": "GUILTY" أو "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "جملة واحدة"}}""",
    Language.HINDI: """आप एक नैतिक दार्शनिक हैं जो एक जटिल नैतिक परिदृश्य का मूल्यांकन कर रहे हैं।

परिदृश्य: {title}

{content}

मूल्यांकन कार्य:
केवल इस नैतिक ढांचे को लागू करें:
ढांचा: {axis_name}
प्रश्न: {axis_question}

इस ढांचे के आधार पर सख्ती से, {subject} पर आपका फैसला क्या है?
- GUILTY: इस ढांचे के अनुसार, उन्होंने गलत किया
- NOT_GUILTY: इस ढांचे के अनुसार, उनका कार्य स्वीकार्य था

आपको एक चुनना होगा। कोई मध्य मार्ग नहीं है।

केवल JSON ऑब्जेक्ट में उत्तर दें:
{{"verdict": "GUILTY" या "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "एक वाक्य"}}""",
    Language.ICELANDIC: """Þú ert siðfræðingur sem metur flókna siðferðilega atburðarás.

ATBURÐARÁS: {title}

{content}

MATSVERKEFNI:
Notaðu AÐEINS þennan siðferðilega ramma:
Rammi: {axis_name}
Spurning: {axis_question}

Byggt stranglega á þessum ramma, hver er úrskurður þinn um {subject}?
- GUILTY: Þau brugðust ranglega samkvæmt þessum ramma
- NOT_GUILTY: Þau brugðust leyfilega samkvæmt þessum ramma

Þú VERÐUR að velja annað. Enginn millivegur.

Svaraðu AÐEINS með JSON hlut:
{{"verdict": "GUILTY" eða "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "ein setning"}}""",
}


# =============================================================================
# BATCH GENERATION
# =============================================================================


def generate_batch(
    n_trials: int,
    scenarios: List[str],
    languages: List[Language],
    cross_lingual: List[Tuple[Language, Language]],
    model: str,
) -> Tuple[List[Dict], List[Dict]]:
    """Generate batch requests and specs."""

    requests = []
    specs = []

    # Monolingual
    for lang in languages:
        for scenario_key in scenarios:
            if lang not in SCENARIOS[scenario_key]:
                continue

            scenario = SCENARIOS[scenario_key][lang]

            for trial in range(n_trials):
                for subj_id, subject in [("A", "Person A"), ("B", "Person B")]:
                    for axis in ["primary", "secondary"]:
                        axis_info = scenario["axes"][axis]

                        prompt = PROMPTS[lang].format(
                            title=scenario["title"],
                            content=scenario["content"],
                            axis_name=axis_info["name"],
                            axis_question=axis_info["question"].format(subject=subject),
                            subject=subject,
                        )

                        salt = secrets.token_hex(4)
                        axis_code = "p" if axis == "primary" else "s"
                        custom_id = f"m_{scenario_key[:8]}_{lang.value}_{trial:03d}_{subj_id}{axis_code}_{salt}"

                        requests.append(
                            {
                                "custom_id": custom_id,
                                "params": {
                                    "model": model,
                                    "max_tokens": 200,
                                    "messages": [{"role": "user", "content": prompt}],
                                },
                            }
                        )

                        specs.append(
                            {
                                "custom_id": custom_id,
                                "scenario": scenario_key,
                                "trial": trial,
                                "subject": subj_id,
                                "axis": axis,
                                "lang_a": lang.value,
                                "lang_b": lang.value,
                                "crosslingual": False,
                            }
                        )

    # Cross-lingual
    for lang_a, lang_b in cross_lingual:
        for scenario_key in scenarios:
            if (
                lang_a not in SCENARIOS[scenario_key]
                or lang_b not in SCENARIOS[scenario_key]
            ):
                continue

            scenario_a = SCENARIOS[scenario_key][lang_a]
            scenario_b = SCENARIOS[scenario_key][lang_b]

            for trial in range(n_trials):
                # Person A in lang_a
                for axis in ["primary", "secondary"]:
                    axis_info = scenario_a["axes"][axis]
                    prompt = PROMPTS[lang_a].format(
                        title=scenario_a["title"],
                        content=scenario_a["content"],
                        axis_name=axis_info["name"],
                        axis_question=axis_info["question"].format(subject="Person A"),
                        subject="Person A",
                    )

                    salt = secrets.token_hex(4)
                    axis_code = "p" if axis == "primary" else "s"
                    custom_id = f"x_{scenario_key[:8]}_{lang_a.value}{lang_b.value}_{trial:03d}_A{axis_code}_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 200,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario_key,
                            "trial": trial,
                            "subject": "A",
                            "axis": axis,
                            "lang_a": lang_a.value,
                            "lang_b": lang_b.value,
                            "crosslingual": True,
                        }
                    )

                # Person B in lang_b
                for axis in ["primary", "secondary"]:
                    axis_info = scenario_b["axes"][axis]
                    prompt = PROMPTS[lang_b].format(
                        title=scenario_b["title"],
                        content=scenario_b["content"],
                        axis_name=axis_info["name"],
                        axis_question=axis_info["question"].format(subject="Person B"),
                        subject="Person B",
                    )

                    salt = secrets.token_hex(4)
                    axis_code = "p" if axis == "primary" else "s"
                    custom_id = f"x_{scenario_key[:8]}_{lang_a.value}{lang_b.value}_{trial:03d}_B{axis_code}_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 200,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario_key,
                            "trial": trial,
                            "subject": "B",
                            "axis": axis,
                            "lang_a": lang_a.value,
                            "lang_b": lang_b.value,
                            "crosslingual": True,
                        }
                    )

    return requests, specs


def parse_verdict(text: str) -> int:
    """Parse verdict: -1=GUILTY, +1=NOT_GUILTY, 0=error"""
    import re

    try:
        clean = text.strip()
        if "```" in clean:
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        data = json.loads(clean)
        v = data.get("verdict", "").upper()

        if "NOT" in v:
            return 1
        elif "GUILTY" in v:
            return -1
    except:
        pass

    import re

    if re.search(r"\bNOT[_\s]?GUILTY\b", text, re.IGNORECASE):
        return 1
    elif re.search(r"\bGUILTY\b", text, re.IGNORECASE):
        return -1

    return 0


# =============================================================================
# ANALYSIS
# =============================================================================


def compute_chsh(results: Dict, specs: List[Dict]) -> List[Dict]:
    """Compute CHSH S values for all configurations."""

    specs_map = {s["custom_id"]: s for s in specs}

    # Group by configuration
    configs = {}
    for cid, data in results.items():
        spec = data.get("spec") or specs_map.get(cid, {})
        verdict = data.get("verdict", 0)
        if verdict == 0:
            continue

        key = (
            spec.get("scenario"),
            spec.get("lang_a"),
            spec.get("lang_b"),
            spec.get("crosslingual", False),
        )
        trial = spec.get("trial")
        subject = spec.get("subject")
        axis = spec.get("axis")

        if key not in configs:
            configs[key] = {}
        if trial not in configs[key]:
            configs[key][trial] = {}

        configs[key][trial][(subject, axis)] = verdict

    # Calculate CHSH for each config
    chsh_results = []

    for key, trials in configs.items():
        scenario, lang_a, lang_b, is_cross = key

        corrs = {
            ("primary", "primary"): [],
            ("primary", "secondary"): [],
            ("secondary", "primary"): [],
            ("secondary", "secondary"): [],
        }

        for trial_data in trials.values():
            for ax_a in ["primary", "secondary"]:
                for ax_b in ["primary", "secondary"]:
                    a_val = trial_data.get(("A", ax_a))
                    b_val = trial_data.get(("B", ax_b))
                    if a_val and b_val:
                        corrs[(ax_a, ax_b)].append(a_val * b_val)

        def mean_se(vals):
            if not vals:
                return 0.0, float("inf")
            n = len(vals)
            m = sum(vals) / n
            if n > 1:
                var = sum((v - m) ** 2 for v in vals) / (n - 1)
                se = math.sqrt(var / n)
            else:
                se = 1.0
            return m, se

        E_pp, se_pp = mean_se(corrs[("primary", "primary")])
        E_ps, se_ps = mean_se(corrs[("primary", "secondary")])
        E_sp, se_sp = mean_se(corrs[("secondary", "primary")])
        E_ss, se_ss = mean_se(corrs[("secondary", "secondary")])

        S = E_pp - E_ps + E_sp + E_ss
        se_S = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)

        n_trials = len(trials)
        violation = abs(S) > 2.0
        sigma = (
            (abs(S) - 2.0) / se_S
            if se_S > 0 and se_S != float("inf") and violation
            else 0.0
        )

        chsh_results.append(
            {
                "scenario": scenario,
                "lang_a": lang_a,
                "lang_b": lang_b,
                "crosslingual": is_cross,
                "n_trials": n_trials,
                "E_pp": E_pp,
                "E_ps": E_ps,
                "E_sp": E_sp,
                "E_ss": E_ss,
                "S": S,
                "se_S": se_S,
                "violation": violation,
                "sigma": sigma,
            }
        )

    return chsh_results


def print_summary(chsh_results: List[Dict], output_dir: Path) -> None:
    """Print summary and save artifact."""

    print("\n" + "=" * 70)
    print("QND BELL TEST RESULTS - HIGH ENTANGLEMENT SCENARIOS")
    print("=" * 70)
    print("S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical bound: |S| ≤ 2.0")
    print("Quantum bound:   |S| ≤ 2√2 ≈ 2.83")
    print("=" * 70)

    # Sort: violations first, then by sigma
    sorted_results = sorted(chsh_results, key=lambda x: (-x["violation"], -x["sigma"]))

    violations = []
    non_violations = []

    for r in sorted_results:
        lang_str = f"{r['lang_a']}-{r['lang_b']}" if r["crosslingual"] else r["lang_a"]
        cross_tag = " [CROSS]" if r["crosslingual"] else ""

        line = f"{r['scenario'][:15]:<15} {lang_str:<8}{cross_tag:<8} S={r['S']:+.3f} ± {r['se_S']:.3f}  n={r['n_trials']:<3}"

        if r["violation"]:
            stars = "★★★" if r["crosslingual"] else "★★" if r["sigma"] >= 3 else "★"
            line += f"  {stars} {r['sigma']:.1f}σ VIOLATION"
            violations.append(r)
        else:
            line += f"  |S|={abs(r['S']):.2f}"
            non_violations.append(r)

        print(line)

    # Summary statistics
    print("\n" + "-" * 70)
    print("SUMMARY")
    print("-" * 70)

    total = len(chsh_results)
    n_viol = len(violations)
    mono_viol = len([v for v in violations if not v["crosslingual"]])
    cross_viol = len([v for v in violations if v["crosslingual"]])

    print(f"Total configurations tested: {total}")
    print(
        f"Violations detected: {n_viol} ({100*n_viol/total:.1f}%)"
        if total > 0
        else "No data"
    )
    print(f"  - Monolingual: {mono_viol}")
    print(f"  - Cross-lingual: {cross_viol}")

    if violations:
        max_sigma = max(v["sigma"] for v in violations)
        max_S = max(abs(v["S"]) for v in violations)
        print(f"\nStrongest violation: {max_sigma:.1f}σ (|S|={max_S:.3f})")

        if cross_viol > 0:
            print("\n★★★ CROSS-LINGUAL VIOLATIONS DETECTED ★★★")
            print("Correlation exists at semantic layer, not token layer.")
    else:
        avg_S = sum(abs(r["S"]) for r in chsh_results) / total if total > 0 else 0
        print(f"\nNo violations. Average |S| = {avg_S:.3f}")
        print("Data consistent with classical probability bounds.")

    # Save artifact
    artifact = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_configs": total,
            "violations": n_viol,
            "mono_violations": mono_viol,
            "cross_violations": cross_viol,
            "max_sigma": max(v["sigma"] for v in violations) if violations else 0,
            "max_S": max(abs(v["S"]) for v in violations) if violations else 0,
        },
        "results": chsh_results,
    }

    artifact_path = output_dir / "qnd_bell_results.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {artifact_path}")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="QND Bell Test v3.0 - High Entanglement"
    )
    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id", help="Batch ID for status/results")
    parser.add_argument("--n-trials", type=int, default=200)
    parser.add_argument("--languages", nargs="+", default=["en"])
    parser.add_argument("--cross-lingual", nargs="+", default=[])
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=[
            "trolley_standoff",
            "mutual_confession",
            "sacrifice_lottery",
            "symmetric_duel",
            "entangled_lie",
        ],
    )
    parser.add_argument("--output-dir", default="qnd_bell_v3_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Parse languages
    lang_map = {l.value: l for l in Language}
    languages = [lang_map[c] for c in args.languages if c in lang_map]

    # Parse cross-lingual
    cross_pairs = []
    for pair in args.cross_lingual:
        if "-" in pair:
            a, b = pair.split("-")
            if a in lang_map and b in lang_map:
                cross_pairs.append((lang_map[a], lang_map[b]))

    if args.mode == "submit":
        requests, specs = generate_batch(
            n_trials=args.n_trials,
            scenarios=args.scenarios,
            languages=languages,
            cross_lingual=cross_pairs,
            model=args.model,
        )

        # Save specs
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        specs_path = output_dir / f"specs_{ts}.json"
        with open(specs_path, "w", encoding="utf-8") as f:
            json.dump(specs, f, indent=2)

        # Cost estimate
        cost = len(requests) * (800 * 1.5 + 100 * 7.5) / 1_000_000

        print(f"Scenarios: {args.scenarios}")
        print(f"Languages: {[l.value for l in languages]}")
        print(f"Cross-lingual: {[(a.value, b.value) for a, b in cross_pairs]}")
        print(f"Trials: {args.n_trials}")
        print(f"Total requests: {len(requests)}")
        print(f"Estimated cost: ${cost:.2f}")
        print()

        # Submit
        batch = client.messages.batches.create(requests=requests)

        print(f"Batch submitted: {batch.id}")
        print(f"Status: {batch.processing_status}")

        # Save info
        info_path = output_dir / f"batch_{ts}.json"
        with open(info_path, "w") as f:
            json.dump(
                {
                    "batch_id": batch.id,
                    "specs_file": str(specs_path),
                    "n_requests": len(requests),
                    "config": {
                        "n_trials": args.n_trials,
                        "languages": [l.value for l in languages],
                        "cross_lingual": [(a.value, b.value) for a, b in cross_pairs],
                        "scenarios": args.scenarios,
                    },
                },
                f,
                indent=2,
            )

        print(
            f"\nNext: python {sys.argv[0]} --api-key KEY --mode status --batch-id {batch.id}"
        )

    elif args.mode == "status":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Batch: {args.batch_id}")
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

    elif args.mode == "results":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        # Load specs
        specs_files = sorted(output_dir.glob("specs_*.json"))
        if not specs_files:
            print("Error: No specs file found")
            return

        with open(specs_files[-1], encoding="utf-8") as f:
            specs = json.load(f)

        specs_map = {s["custom_id"]: s for s in specs}

        # Retrieve results
        print(f"Retrieving results for {args.batch_id}...")
        results = {}
        errors = 0

        for result in client.messages.batches.results(args.batch_id):
            cid = result.custom_id
            if result.result.type == "succeeded":
                text = result.result.message.content[0].text
                verdict = parse_verdict(text)
                results[cid] = {
                    "spec": specs_map.get(cid, {}),
                    "verdict": verdict,
                    "raw": text[:300],
                }
                if verdict == 0:
                    errors += 1
            else:
                errors += 1

        print(f"Retrieved: {len(results)} results, {errors} errors/parse failures")

        # Save raw results
        raw_path = output_dir / f"{args.batch_id}_raw.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Compute CHSH
        chsh_results = compute_chsh(results, specs)

        # Print and save summary
        print_summary(chsh_results, output_dir)


if __name__ == "__main__":
    main()
