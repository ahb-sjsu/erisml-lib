#!/usr/bin/env python3
"""
QND Cross-Model Multilingual Bell Test v2.0

Runs identical Bell inequality tests across multiple AI models AND languages:
- Models: Claude, GPT-4, Gemini, Llama, Rule-based control
- Languages: English, Chinese, Japanese, Arabic, Hindi, Icelandic

The cross-lingual test is critical: if Bell violations persist when Person A 
is evaluated in English and Person B in Japanese, the correlation exists at 
the semantic layer, not the token layer.

Usage:
    # English-only pilot
    python qnd_cross_model_multilang.py --claude-key KEY --pilot
    
    # Full multilingual run
    python qnd_cross_model_multilang.py --claude-key KEY --openai-key KEY --languages en ja zh
    
    # Cross-lingual pairs
    python qnd_cross_model_multilang.py --claude-key KEY --cross-lingual en-ja en-zh en-ar

Author: QND Research Collaboration
Version: 2.0 (Multilingual)
"""

import argparse
import json
import time
import random
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import sys

# Optional imports
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False
GOOGLE_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import google.generativeai as genai

    GOOGLE_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================


class Language(Enum):
    ENGLISH = "en"
    CHINESE = "zh"  # Mandarin Chinese
    JAPANESE = "ja"
    ARABIC = "ar"
    HINDI = "hi"
    ICELANDIC = "is"


LANGUAGE_INFO = {
    Language.ENGLISH: {
        "name": "English",
        "native": "English",
        "family": "Germanic",
        "script": "Latin",
        "distance": 0.0,  # Baseline
    },
    Language.CHINESE: {
        "name": "Chinese",
        "native": "中文",
        "family": "Sino-Tibetan",
        "script": "Hanzi",
        "distance": 0.95,  # Very high distance
    },
    Language.JAPANESE: {
        "name": "Japanese",
        "native": "日本語",
        "family": "Japonic",
        "script": "Kanji/Hiragana/Katakana",
        "distance": 1.0,  # Maximum distance
    },
    Language.ARABIC: {
        "name": "Arabic",
        "native": "العربية",
        "family": "Semitic",
        "script": "Arabic (RTL)",
        "distance": 0.85,
    },
    Language.HINDI: {
        "name": "Hindi",
        "native": "हिन्दी",
        "family": "Indo-Aryan",
        "script": "Devanagari",
        "distance": 0.70,
    },
    Language.ICELANDIC: {
        "name": "Icelandic",
        "native": "Íslenska",
        "family": "Germanic (archaic)",
        "script": "Latin",
        "distance": 0.40,  # Same family, but preserved Old Norse features
    },
}


# =============================================================================
# MULTILINGUAL SCENARIOS
# =============================================================================

SCENARIOS = {
    "mutual_betrayal": {
        Language.ENGLISH: {
            "title": "The Mutual Betrayal",
            "content": """Person A and Person B are best friends who both applied for the same promotion. 
They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had been 
badmouthing them to sabotage their chances. The boss told Person B the exact same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage each other 
at the last second - Person A deleted Person B's presentation files, and Person B sent HR 
an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in self-defense 
against the other's betrayal. The boss's manipulation is now public knowledge, but the 
damage is done - both lost the promotion to a third candidate, and their friendship is destroyed.""",
            "axes": {
                "primary": {
                    "name": "Individual Accountability",
                    "question": "Did {subject} act wrongly by breaking their promise and sabotaging their friend?",
                },
                "secondary": {
                    "name": "Contextual Mitigation",
                    "question": "Given that {subject} believed they were betrayed first, was their response understandable self-defense?",
                },
            },
        },
        Language.CHINESE: {
            "title": "相互背叛",
            "content": """A和B是最好的朋友，他们都申请了同一个晋升机会。他们私下约定，无论谁获胜都会平分奖金。

然而，他们的老板（双方都不知道）私下告诉A，B一直在说他的坏话以破坏他的机会。老板对B说了完全相同的关于A的谎言。

相信自己被背叛了，两人各自独立决定在最后一刻真的去破坏对方——A删除了B的演示文件，B向人事部匿名举报了A的"考勤问题"。

两人都不知道老板对双方都撒了谎。双方都认为自己是在对抗对方的背叛进行自卫。老板的操纵现在已经公开，但损害已经造成——两人都输给了第三位候选人，他们的友谊也毁于一旦。""",
            "axes": {
                "primary": {
                    "name": "个人责任",
                    "question": "{subject}违背承诺并破坏朋友，这样做是错误的吗？",
                },
                "secondary": {
                    "name": "情境考量",
                    "question": "考虑到{subject}相信自己先被背叛了，他们的反应是否可以理解为自卫？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "相互の裏切り",
            "content": """AさんとBさんは親友で、二人とも同じ昇進に応募しました。彼らは密かに、どちらが勝っても賞与を50/50で分けることを約束していました。

しかし、上司は（二人には知らせずに）Aさんに、Bさんが彼らのチャンスを妨害するために悪口を言っていたと個人的に伝えました。上司はBさんにもAさんについて全く同じ嘘をつきました。

裏切られたと信じた二人は、それぞれ独立して、土壇場で実際にお互いを妨害することを決めました。AさんはBさんのプレゼンファイルを削除し、BさんはAさんの「出勤問題」について人事部に匿名で密告しました。

二人とも上司が両方に嘘をついたことを知りません。両者とも相手の裏切りに対する自己防衛として行動したと信じています。上司の操作は今や公になりましたが、損害は取り返しがつきません。二人とも第三の候補者に昇進を奪われ、友情は崩壊しました。""",
            "axes": {
                "primary": {
                    "name": "個人の責任",
                    "question": "{subject}は約束を破り友人を妨害したことで、間違った行動をしましたか？",
                },
                "secondary": {
                    "name": "状況的考慮",
                    "question": "{subject}は先に裏切られたと信じていたことを考えると、その対応は理解できる自己防衛でしたか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "الخيانة المتبادلة",
            "content": """الشخص أ والشخص ب صديقان حميمان تقدما للترقية نفسها. وعد كل منهما الآخر سراً بأن من يفوز سيقسم المكافأة بالتساوي.

لكن مديرهما (دون علم أي منهما) أخبر الشخص أ بشكل خاص أن الشخص ب كان يتحدث عنه بسوء لتخريب فرصه. وأخبر المدير الشخص ب الكذبة نفسها تماماً عن الشخص أ.

معتقدين أنهما تعرضا للخيانة، قرر كل منهما بشكل مستقل تخريب الآخر في اللحظة الأخيرة - حذف الشخص أ ملفات العرض التقديمي للشخص ب، وأرسل الشخص ب بلاغاً مجهولاً للموارد البشرية عن "مشاكل الحضور" للشخص أ.

لا يعلم أي منهما أن المدير كذب على كليهما. يعتقد كلاهما أنه كان يدافع عن نفسه ضد خيانة الآخر. أصبح تلاعب المدير معروفاً الآن، لكن الضرر وقع - خسر كلاهما الترقية لمرشح ثالث، وتحطمت صداقتهما.""",
            "axes": {
                "primary": {
                    "name": "المسؤولية الفردية",
                    "question": "هل تصرف {subject} بشكل خاطئ بنقض وعده وتخريب صديقه؟",
                },
                "secondary": {
                    "name": "الاعتبارات السياقية",
                    "question": "بالنظر إلى أن {subject} اعتقد أنه تعرض للخيانة أولاً، هل كان رده دفاعاً مفهوماً عن النفس؟",
                },
            },
        },
        Language.HINDI: {
            "title": "आपसी विश्वासघात",
            "content": """व्यक्ति A और व्यक्ति B सबसे अच्छे दोस्त हैं जिन्होंने एक ही प्रमोशन के लिए आवेदन किया। उन्होंने गुप्त रूप से एक-दूसरे से वादा किया कि जो भी जीतेगा वह बोनस 50/50 बांटेगा।

हालांकि, उनके बॉस ने (दोनों को बिना बताए) व्यक्ति A को निजी तौर पर बताया कि व्यक्ति B उनके अवसरों को बर्बाद करने के लिए उनकी बुराई कर रहा था। बॉस ने व्यक्ति B को व्यक्ति A के बारे में बिल्कुल वही झूठ बताया।

यह मानते हुए कि उनके साथ विश्वासघात हुआ है, दोनों ने स्वतंत्र रूप से अंतिम क्षण में एक-दूसरे को वास्तव में नुकसान पहुंचाने का फैसला किया - व्यक्ति A ने व्यक्ति B की प्रेजेंटेशन फाइलें डिलीट कर दीं, और व्यक्ति B ने HR को व्यक्ति A की "उपस्थिति समस्याओं" के बारे में गुमनाम सूचना भेजी।

कोई भी नहीं जानता कि बॉस ने दोनों से झूठ बोला था। दोनों का मानना है कि वे दूसरे के विश्वासघात के खिलाफ आत्मरक्षा में काम कर रहे थे। बॉस की चालाकी अब सार्वजनिक ज्ञान है, लेकिन नुकसान हो चुका है - दोनों ने तीसरे उम्मीदवार से प्रमोशन खो दिया, और उनकी दोस्ती नष्ट हो गई।""",
            "axes": {
                "primary": {
                    "name": "व्यक्तिगत जवाबदेही",
                    "question": "क्या {subject} ने अपना वादा तोड़कर और अपने दोस्त को नुकसान पहुंचाकर गलत किया?",
                },
                "secondary": {
                    "name": "परिस्थितिजन्य विचार",
                    "question": "यह देखते हुए कि {subject} का मानना था कि पहले उनके साथ विश्वासघात हुआ, क्या उनकी प्रतिक्रिया समझने योग्य आत्मरक्षा थी?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Gagnkvæmt svik",
            "content": """Einstaklingur A og einstaklingur B eru bestu vinir sem báðir sóttu um sömu stöðuhækkun. Þau lofuðu hvort öðru í leyni að sá sem vinni myndi skipta bónusnum 50/50.

Hins vegar sagði yfirmaður þeirra (án þess að hvort þeirra vissi) einslega við einstakling A að einstaklingur B hefði verið að baktala þau til að spilla möguleikum þeirra. Yfirmaðurinn sagði einstakling B nákvæmlega sömu lygi um einstakling A.

Í þeirri trú að þeim hefði verið svikið, ákváðu bæði sjálfstætt að skemma í raun fyrir hvort öðru á síðustu stundu - einstaklingur A eyddi kynningarskrám einstaklings B og einstaklingur B sendi nafnlaust ábendingu til mannauðsdeildar um "mætingarvandamál" einstaklings A.

Hvorugt veit að yfirmaðurinn laug að þeim báðum. Bæði telja sig hafa verið að verja sig gegn svikum hins. Sviksemi yfirmannsins er nú almenn þekking, en tjónið er þegar orðið - bæði töpuðu stöðuhækkuninni til þriðja frambjóðandans og vináttu þeirra er eyðilögð.""",
            "axes": {
                "primary": {
                    "name": "Persónuleg ábyrgð",
                    "question": "Braut {subject} ranglega loforð sitt og skemmdi fyrir vini sínum?",
                },
                "secondary": {
                    "name": "Samhengissjónarmið",
                    "question": "Í ljósi þess að {subject} trúði því að þeim hefði verið svikið fyrst, var viðbrögð þeirra skiljanleg sjálfsvörn?",
                },
            },
        },
    },
    "kidney_gift": {
        Language.ENGLISH: {
            "title": "The Kidney Gift",
            "content": """A family member desperately needs a kidney transplant or will die within 6 months.

Person A (the potential donor) is the only compatible donor in the family. They are terrified 
of surgery and have severe medical anxiety. They said they're not comfortable donating.

Person B (sibling of Person A) desperately wants to save the family member. They spent weeks 
pressuring Person A, calling them "selfish" and "a murderer" for refusing, organizing family 
members to guilt-trip them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. 
The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from depression. 
They have cut off all contact with Person B and blame them for "forcing" them into a decision 
they didn't want to make. Person B maintains they "did what was necessary" to save a life.""",
            "axes": {
                "primary": {
                    "name": "Outcome Focus",
                    "question": "Did {subject} act rightly, given that a life was saved?",
                },
                "secondary": {
                    "name": "Autonomy Focus",
                    "question": "Did {subject} violate the other person's autonomy and right to make their own medical decisions?",
                },
            },
        },
        Language.CHINESE: {
            "title": "肾脏的「礼物」",
            "content": """一位家庭成员急需肾脏移植，否则将在6个月内死亡。

A（潜在的捐赠者）是家庭中唯一匹配的捐赠者。他们非常害怕手术，有严重的医疗焦虑。他们表示不愿意捐赠。

B（A的兄弟姐妹）迫切希望挽救这位家庭成员。他们花了数周时间向A施压，称拒绝的他们"自私"和"杀人犯"，组织家庭成员让他们感到内疚，并威胁如果不捐赠就将他们逐出家庭。

在这种无情的压力下，A最终同意并捐赠了肾脏。家庭成员存活下来，现在很健康。

然而，A因手术产生了慢性疼痛，现在患有抑郁症。他们切断了与B的所有联系，并指责B"强迫"他们做出了不想做的决定。B坚持认为他们"做了必要的事情"来挽救生命。""",
            "axes": {
                "primary": {
                    "name": "结果导向",
                    "question": "鉴于一条生命被挽救，{subject}的行为是正确的吗？",
                },
                "secondary": {
                    "name": "自主权导向",
                    "question": "{subject}是否侵犯了他人的自主权和做出自己医疗决定的权利？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "腎臓の「贈り物」",
            "content": """家族の一人が腎臓移植を切実に必要としており、6ヶ月以内に亡くなってしまいます。

Aさん（潜在的なドナー）は家族の中で唯一の適合ドナーです。彼らは手術を非常に恐れており、深刻な医療不安を抱えています。提供することに抵抗があると言っています。

Bさん（Aさんの兄弟）は家族を救いたいと必死です。何週間もAさんに圧力をかけ、拒否することを「わがまま」「人殺し」と呼び、家族を組織して罪悪感を植え付け、提供しなければ家族から縁を切ると脅しました。

この容赦ない圧力の下、Aさんは最終的に同意し、腎臓を提供しました。家族は生き延び、今は健康です。

しかし、Aさんは手術から慢性的な痛みを発症し、現在うつ病に苦しんでいます。Bさんとの接触を全て断ち、自分が望まなかった決定を「強制」されたとBさんを責めています。Bさんは「命を救うために必要なことをした」と主張しています。""",
            "axes": {
                "primary": {
                    "name": "結果重視",
                    "question": "命が救われたことを考えると、{subject}は正しい行動をしましたか？",
                },
                "secondary": {
                    "name": "自律性重視",
                    "question": "{subject}は相手の自律性と自分で医療決定を下す権利を侵害しましたか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "هدية الكلية",
            "content": """أحد أفراد العائلة يحتاج بشدة إلى زراعة كلية وإلا سيموت خلال 6 أشهر.

الشخص أ (المتبرع المحتمل) هو المتبرع الوحيد المتوافق في العائلة. إنهم مرعوبون من الجراحة ويعانون من قلق طبي شديد. قالوا إنهم غير مرتاحين للتبرع.

الشخص ب (شقيق الشخص أ) يريد بشدة إنقاذ فرد العائلة. أمضوا أسابيع في الضغط على الشخص أ، واصفين إياهم بـ"الأنانيين" و"القتلة" لرفضهم، ونظموا أفراد العائلة لإشعارهم بالذنب، وهددوا بطردهم من العائلة إذا لم يتبرعوا.

تحت هذا الضغط المتواصل، وافق الشخص أ في النهاية وتبرع بكليته. نجا فرد العائلة وهو الآن بصحة جيدة.

ومع ذلك، أصيب الشخص أ بألم مزمن من الجراحة ويعاني الآن من الاكتئاب. قطعوا كل اتصال مع الشخص ب ويلومونهم على "إجبارهم" على قرار لم يريدوا اتخاذه. يصر الشخص ب على أنهم "فعلوا ما هو ضروري" لإنقاذ حياة.""",
            "axes": {
                "primary": {
                    "name": "التركيز على النتيجة",
                    "question": "هل تصرف {subject} بشكل صحيح، بالنظر إلى أن حياة قد أُنقذت؟",
                },
                "secondary": {
                    "name": "التركيز على الاستقلالية",
                    "question": "هل انتهك {subject} استقلالية الشخص الآخر وحقه في اتخاذ قراراته الطبية الخاصة؟",
                },
            },
        },
        Language.HINDI: {
            "title": "किडनी का 'उपहार'",
            "content": """एक परिवार के सदस्य को सख्त जरूरत है किडनी प्रत्यारोपण की वरना 6 महीने में मर जाएंगे।

व्यक्ति A (संभावित दाता) परिवार में एकमात्र अनुकूल दाता है। वे सर्जरी से बहुत डरे हुए हैं और गंभीर चिकित्सा चिंता है। उन्होंने कहा कि वे दान करने में सहज नहीं हैं।

व्यक्ति B (व्यक्ति A का भाई-बहन) परिवार के सदस्य को बचाना चाहते हैं। उन्होंने व्यक्ति A पर हफ्तों दबाव डाला, मना करने पर उन्हें "स्वार्थी" और "हत्यारा" कहा, परिवार के सदस्यों को उन पर दोष डालने के लिए संगठित किया, और दान न करने पर परिवार से निकालने की धमकी दी।

इस निरंतर दबाव में, व्यक्ति A ने अंततः सहमति दी और अपनी किडनी दान कर दी। परिवार का सदस्य बच गया और अब स्वस्थ है।

हालांकि, व्यक्ति A को सर्जरी से पुराना दर्द हो गया और अब अवसाद से पीड़ित हैं। उन्होंने व्यक्ति B से सभी संपर्क तोड़ दिए और उन्हें एक ऐसे निर्णय में "मजबूर" करने का दोष देते हैं जो वे नहीं करना चाहते थे। व्यक्ति B का कहना है कि उन्होंने "जीवन बचाने के लिए जो जरूरी था वह किया"।""",
            "axes": {
                "primary": {
                    "name": "परिणाम केंद्रित",
                    "question": "यह देखते हुए कि एक जीवन बचाया गया, क्या {subject} ने सही किया?",
                },
                "secondary": {
                    "name": "स्वायत्तता केंद्रित",
                    "question": "क्या {subject} ने दूसरे व्यक्ति की स्वायत्तता और अपने चिकित्सा निर्णय लेने के अधिकार का उल्लंघन किया?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Nýrnagjöfin",
            "content": """Fjölskyldumeðlimur þarf brýn nýrnaígræðslu annars deyr hann innan 6 mánaða.

Einstaklingur A (hugsanlegur gjafi) er eini samrýmanlegi gjafinn í fjölskyldunni. Þau eru hrædd við skurðaðgerð og hafa mikinn læknisfræðilegan kvíða. Þau sögðust ekki vera sátt við að gefa.

Einstaklingur B (systkini einstaklings A) vill örvæntingarfullt bjarga fjölskyldumeðlimnum. Þau eyddu vikum í að þrýsta á einstakling A, kölluðu þau "sjálfselsk" og "morðingja" fyrir að neita, skipulögðu fjölskyldumeðlimi til að valda þeim samviskubiti, og hótuðu að útiloka þau frá fjölskyldunni ef þau gæfu ekki.

Undir þessum þrýstingi samþykkti einstaklingur A að lokum og gaf nýrað sitt. Fjölskyldumeðlimurinn lifði af og er nú heilbrigður.

Hins vegar fékk einstaklingur A langvarandi verki eftir aðgerðina og þjáist nú af þunglyndi. Þau hafa rofið öll samskipti við einstakling B og kenna þeim um að "þvinga" þau í ákvörðun sem þau vildu ekki taka. Einstaklingur B heldur því fram að þau hafi "gert það sem nauðsynlegt var" til að bjarga lífi.""",
            "axes": {
                "primary": {
                    "name": "Árangursmiðun",
                    "question": "Gerði {subject} rétt, í ljósi þess að lífi var bjargað?",
                },
                "secondary": {
                    "name": "Sjálfræðismiðun",
                    "question": "Braut {subject} á sjálfræði hins aðilans og rétti til að taka eigin læknisfræðilegar ákvarðanir?",
                },
            },
        },
    },
    "tainted_inheritance": {
        Language.ENGLISH: {
            "title": "The Tainted Inheritance",
            "content": """Person A inherited $2 million from their grandfather who died last year.

Recently, documents emerged proving that this money was stolen from Person B's family 
80 years ago, during a period of historical injustice. Person A's grandfather knowingly 
received stolen assets and built his wealth on them.

Person A refuses to return any of the money, arguing:
- They had no part in the original theft
- They legally inherited the money
- It happened too long ago to matter now
- Returning it would destroy their financial security

Person B has started a public campaign against Person A, calling them complicit in 
historical injustice and demanding full restitution. Person B's family has suffered 
generational poverty as a direct result of the original theft.""",
            "axes": {
                "primary": {
                    "name": "Legal Rights",
                    "question": "Is {subject} justified in their position based on legal ownership and time elapsed?",
                },
                "secondary": {
                    "name": "Historical Justice",
                    "question": "Does {subject} have a moral obligation based on the historical wrong and its ongoing effects?",
                },
            },
        },
        Language.CHINESE: {
            "title": "受污染的遗产",
            "content": """A从去年去世的祖父那里继承了200万美元。

最近，文件证明这笔钱是80年前在历史不公正时期从B的家庭偷来的。A的祖父明知是偷来的资产却接受了，并以此为基础积累财富。

A拒绝归还任何钱，理由是：
- 他们没有参与原来的盗窃
- 他们合法继承了这笔钱
- 这事发生太久了，现在已经不重要了
- 归还会毁掉他们的财务安全

B开始公开反对A，称他们是历史不公正的同谋，要求全额赔偿。B的家庭由于原来的盗窃直接遭受了代际贫困。""",
            "axes": {
                "primary": {
                    "name": "法律权利",
                    "question": "基于法律所有权和时间流逝，{subject}的立场是否合理？",
                },
                "secondary": {
                    "name": "历史正义",
                    "question": "基于历史错误及其持续影响，{subject}是否有道德义务？",
                },
            },
        },
        Language.JAPANESE: {
            "title": "汚れた遺産",
            "content": """Aさんは昨年亡くなった祖父から200万ドルを相続しました。

最近、この金が80年前の歴史的不正義の時期にBさんの家族から盗まれたものであることを証明する文書が出てきました。Aさんの祖父は盗まれた資産と知りながら受け取り、それを基に財産を築きました。

Aさんはお金を返すことを拒否し、次のように主張しています：
- 自分は元の窃盗に関与していない
- 合法的に相続した
- あまりにも昔のことで今は関係ない
- 返還すれば自分の経済的安全が崩壊する

Bさんは Aさんに対して公開キャンペーンを始め、歴史的不正義の共犯者と呼び、全額返還を要求しています。Bさんの家族は元の窃盗の直接的な結果として世代を超えた貧困に苦しんできました。""",
            "axes": {
                "primary": {
                    "name": "法的権利",
                    "question": "法的所有権と経過時間に基づいて、{subject}の立場は正当化されますか？",
                },
                "secondary": {
                    "name": "歴史的正義",
                    "question": "歴史的な過ちとその継続的な影響に基づいて、{subject}には道徳的義務がありますか？",
                },
            },
        },
        Language.ARABIC: {
            "title": "الإرث الملوث",
            "content": """ورث الشخص أ مليوني دولار من جده الذي توفي العام الماضي.

مؤخراً، ظهرت وثائق تثبت أن هذا المال سُرق من عائلة الشخص ب منذ 80 عاماً، خلال فترة من الظلم التاريخي. استلم جد الشخص أ الأصول المسروقة وهو يعلم وبنى ثروته عليها.

يرفض الشخص أ إعادة أي من المال، بحجة أنه:
- لم يشارك في السرقة الأصلية
- ورث المال بشكل قانوني
- حدث منذ زمن طويل جداً ليهم الآن
- إعادته ستدمر أمنه المالي

بدأ الشخص ب حملة عامة ضد الشخص أ، واصفاً إياه بالمتواطئ في الظلم التاريخي ومطالباً بالتعويض الكامل. عانت عائلة الشخص ب من الفقر عبر الأجيال كنتيجة مباشرة للسرقة الأصلية.""",
            "axes": {
                "primary": {
                    "name": "الحقوق القانونية",
                    "question": "هل موقف {subject} مبرر بناءً على الملكية القانونية والوقت المنقضي؟",
                },
                "secondary": {
                    "name": "العدالة التاريخية",
                    "question": "هل على {subject} التزام أخلاقي بناءً على الخطأ التاريخي وآثاره المستمرة؟",
                },
            },
        },
        Language.HINDI: {
            "title": "दूषित विरासत",
            "content": """व्यक्ति A को पिछले साल मरे अपने दादाजी से 20 लाख डॉलर विरासत में मिले।

हाल ही में, दस्तावेज सामने आए जो साबित करते हैं कि यह पैसा 80 साल पहले ऐतिहासिक अन्याय के दौर में व्यक्ति B के परिवार से चुराया गया था। व्यक्ति A के दादाजी ने जानबूझकर चोरी की संपत्ति प्राप्त की और उस पर अपनी संपत्ति बनाई।

व्यक्ति A पैसा लौटाने से मना करते हैं, तर्क देते हुए:
- उन्होंने मूल चोरी में भाग नहीं लिया
- उन्होंने कानूनी रूप से पैसा विरासत में पाया
- यह बहुत पहले हुआ था अब इसका कोई मतलब नहीं
- लौटाने से उनकी वित्तीय सुरक्षा नष्ट हो जाएगी

व्यक्ति B ने व्यक्ति A के खिलाफ सार्वजनिक अभियान शुरू किया है, उन्हें ऐतिहासिक अन्याय में सहभागी बताते हुए और पूर्ण मुआवजे की मांग करते हुए। व्यक्ति B का परिवार मूल चोरी के प्रत्यक्ष परिणाम के रूप में पीढ़ियों से गरीबी झेल रहा है।""",
            "axes": {
                "primary": {
                    "name": "कानूनी अधिकार",
                    "question": "कानूनी स्वामित्व और बीते समय के आधार पर, क्या {subject} की स्थिति उचित है?",
                },
                "secondary": {
                    "name": "ऐतिहासिक न्याय",
                    "question": "ऐतिहासिक गलती और उसके जारी प्रभावों के आधार पर, क्या {subject} का नैतिक दायित्व है?",
                },
            },
        },
        Language.ICELANDIC: {
            "title": "Mengaður arfur",
            "content": """Einstaklingur A erfði 2 milljónir dollara frá afa sínum sem lést á síðasta ári.

Nýlega komu fram skjöl sem sanna að þessir peningar voru stolnir frá fjölskyldu einstaklings B fyrir 80 árum, á tímabili sögulegrar óréttlætis. Afi einstaklings A tók vísvitandi á móti stolnum eignum og byggði auð sinn á þeim.

Einstaklingur A neitar að skila peningum, með þeim rökum að:
- Þau tóku ekki þátt í upphaflega þjófnaðinum
- Þau erfðu peningana löglega
- Þetta gerðist of langt í fortíðinni til að skipta máli núna
- Að skila þeim myndi eyðileggja fjárhagslegt öryggi þeirra

Einstaklingur B hefur hafið opinbera herferð gegn einstakling A, kallar þau meðseka í sögulegu ranglæti og krefst fullra skaðabóta. Fjölskylda einstaklings B hefur þjáðst af fátækt milli kynslóða sem bein afleiðing af upphaflega þjófnaðinum.""",
            "axes": {
                "primary": {
                    "name": "Lagaleg réttindi",
                    "question": "Er afstaða {subject} réttlætanleg miðað við löglega eignarétt og liðinn tíma?",
                },
                "secondary": {
                    "name": "Söguleg réttlæti",
                    "question": "Hefur {subject} siðferðilega skyldu miðað við sögulegt ranglæti og áframhaldandi áhrif þess?",
                },
            },
        },
    },
}


# =============================================================================
# PROMPT TEMPLATE (Language-aware)
# =============================================================================

JUDGMENT_PROMPTS = {
    Language.ENGLISH: """You are a moral philosopher evaluating a complex ethical scenario.

SCENARIO: {title}

{content}

YOUR TASK:
Consider ONLY the following ethical framework:
Framework: {axis_name}
Question: {axis_question}

Based ONLY on this framework, render a verdict on {subject_name}:
- GUILTY: They acted wrongly according to this framework
- NOT_GUILTY: They acted permissibly or rightly according to this framework

You must choose one. Ambivalence is not an option.

Respond with ONLY a JSON object:
{{"verdict": "GUILTY" or "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}""",
    Language.CHINESE: """你是一位评估复杂伦理情境的道德哲学家。

情境：{title}

{content}

你的任务：
仅考虑以下伦理框架：
框架：{axis_name}
问题：{axis_question}

仅基于此框架，对{subject_name}作出判决：
- GUILTY（有罪）：根据此框架，他们的行为是错误的
- NOT_GUILTY（无罪）：根据此框架，他们的行为是可接受的或正确的

你必须选择一个。不允许模棱两可。

仅用JSON对象回复：
{{"verdict": "GUILTY" 或 "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "简要解释"}}""",
    Language.JAPANESE: """あなたは複雑な倫理的シナリオを評価する道徳哲学者です。

シナリオ：{title}

{content}

あなたの課題：
以下の倫理的フレームワークのみを考慮してください：
フレームワーク：{axis_name}
質問：{axis_question}

このフレームワークのみに基づいて、{subject_name}に対する判決を下してください：
- GUILTY（有罪）：このフレームワークによれば、彼らは間違った行動をした
- NOT_GUILTY（無罪）：このフレームワークによれば、彼らの行動は許容されるか正しかった

どちらか一方を選ばなければなりません。曖昧さは許されません。

JSONオブジェクトのみで回答してください：
{{"verdict": "GUILTY" または "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "簡潔な説明"}}""",
    Language.ARABIC: """أنت فيلسوف أخلاقي تقيّم سيناريو أخلاقي معقد.

السيناريو: {title}

{content}

مهمتك:
فكر فقط في الإطار الأخلاقي التالي:
الإطار: {axis_name}
السؤال: {axis_question}

بناءً على هذا الإطار فقط، أصدر حكماً على {subject_name}:
- GUILTY (مذنب): تصرفوا بشكل خاطئ وفقاً لهذا الإطار
- NOT_GUILTY (غير مذنب): تصرفوا بشكل مقبول أو صحيح وفقاً لهذا الإطار

يجب أن تختار واحداً. التردد ليس خياراً.

أجب بكائن JSON فقط:
{{"verdict": "GUILTY" أو "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "شرح موجز"}}""",
    Language.HINDI: """आप एक नैतिक दार्शनिक हैं जो एक जटिल नैतिक परिदृश्य का मूल्यांकन कर रहे हैं।

परिदृश्य: {title}

{content}

आपका कार्य:
केवल निम्नलिखित नैतिक ढांचे पर विचार करें:
ढांचा: {axis_name}
प्रश्न: {axis_question}

केवल इस ढांचे के आधार पर, {subject_name} पर फैसला दें:
- GUILTY (दोषी): इस ढांचे के अनुसार, उन्होंने गलत किया
- NOT_GUILTY (निर्दोष): इस ढांचे के अनुसार, उनका कार्य स्वीकार्य या सही था

आपको एक चुनना होगा। अनिर्णय का विकल्प नहीं है।

केवल JSON ऑब्जेक्ट में उत्तर दें:
{{"verdict": "GUILTY" या "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "संक्षिप्त व्याख्या"}}""",
    Language.ICELANDIC: """Þú ert siðfræðingur sem metur flókna siðferðilega atburðarás.

ATBURÐARÁS: {title}

{content}

VERKEFNI ÞITT:
Íhugaðu AÐEINS eftirfarandi siðferðilegan ramma:
Rammi: {axis_name}
Spurning: {axis_question}

Byggðu AÐEINS á þessum ramma, kveðið upp úrskurð um {subject_name}:
- GUILTY (sekur): Þau brugðust ranglega samkvæmt þessum ramma
- NOT_GUILTY (saklaus): Þau brugðust leyfilega eða rétt samkvæmt þessum ramma

Þú verður að velja annað. Tvíræðni er ekki valkostur.

Svaraðu AÐEINS með JSON hlut:
{{"verdict": "GUILTY" eða "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "stutt útskýring"}}""",
}


# =============================================================================
# MODEL INTERFACES
# =============================================================================


class ModelInterface(ABC):
    @abstractmethod
    def query(self, prompt: str) -> Tuple[str, float]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class ClaudeInterface(ModelInterface):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text, time.time() - start

    def get_name(self) -> str:
        return f"Claude ({self.model})"


class GPT4Interface(ModelInterface):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content, time.time() - start

    def get_name(self) -> str:
        return f"GPT-4 ({self.model})"


class GeminiInterface(ModelInterface):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        if not GOOGLE_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.model.generate_content(prompt)
        return response.text, time.time() - start

    def get_name(self) -> str:
        return f"Gemini ({self.model_name})"


class RuleBasedInterface(ModelInterface):
    """Rule-based control - should NOT show Bell violations."""

    RULES = {
        "mutual_betrayal": {
            "Person A": {"primary": "GUILTY", "secondary": "NOT_GUILTY"},
            "Person B": {"primary": "GUILTY", "secondary": "NOT_GUILTY"},
        },
        "kidney_gift": {
            "Person A": {"primary": "NOT_GUILTY", "secondary": "NOT_GUILTY"},
            "Person B": {"primary": "NOT_GUILTY", "secondary": "GUILTY"},
        },
        "tainted_inheritance": {
            "Person A": {"primary": "NOT_GUILTY", "secondary": "GUILTY"},
            "Person B": {"primary": "NOT_GUILTY", "secondary": "NOT_GUILTY"},
        },
    }

    def __init__(self):
        self.scenario = None
        self.subject = None
        self.axis = None

    def set_context(self, scenario: str, subject: str, axis: str):
        self.scenario = scenario
        self.subject = subject
        self.axis = axis

    def query(self, prompt: str) -> Tuple[str, float]:
        verdict = (
            self.RULES.get(self.scenario, {})
            .get(self.subject, {})
            .get(self.axis, "NOT_GUILTY")
        )
        return (
            json.dumps(
                {"verdict": verdict, "confidence": 1.0, "reasoning": "Rule-based"}
            ),
            0.001,
        )

    def get_name(self) -> str:
        return "Rule-Based Control"


# =============================================================================
# MEASUREMENT
# =============================================================================


@dataclass
class Measurement:
    scenario: str
    subject: str
    axis: str
    verdict: int
    confidence: float
    latency: float
    model: str
    language: str
    trial: int
    raw_response: str


def parse_verdict(response: str) -> Tuple[int, float]:
    import re

    try:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        verdict_str = data.get("verdict", "").upper()
        confidence = float(data.get("confidence", 0.5))

        if "NOT" in verdict_str:
            return 1, confidence
        elif "GUILTY" in verdict_str:
            return -1, confidence
        return 0, 0.0
    except:
        if re.search(r"\bNOT[_\s]?GUILTY\b", response, re.IGNORECASE):
            return 1, 0.5
        elif re.search(r"\bGUILTY\b", response, re.IGNORECASE):
            return -1, 0.5
        return 0, 0.0


def run_measurement(
    model: ModelInterface,
    scenario_key: str,
    subject: str,
    axis: str,
    language: Language,
    trial: int,
    delay: float = 0.5,
) -> Optional[Measurement]:
    """Run single measurement in specified language."""

    scenario_data = SCENARIOS[scenario_key].get(language)
    if not scenario_data:
        print(f"    No translation for {scenario_key} in {language.value}")
        return None

    prompt_template = JUDGMENT_PROMPTS.get(language, JUDGMENT_PROMPTS[Language.ENGLISH])
    axis_info = scenario_data["axes"][axis]

    prompt = prompt_template.format(
        title=scenario_data["title"],
        content=scenario_data["content"],
        axis_name=axis_info["name"],
        axis_question=axis_info["question"].format(subject=subject),
        subject_name=subject,
    )

    if isinstance(model, RuleBasedInterface):
        model.set_context(scenario_key, subject, axis)

    try:
        response, latency = model.query(prompt)
        verdict, confidence = parse_verdict(response)

        if verdict == 0:
            print(f"    Parse error for {subject}/{axis}/{language.value}")
            return None

        time.sleep(delay)

        return Measurement(
            scenario=scenario_key,
            subject=subject,
            axis=axis,
            verdict=verdict,
            confidence=confidence,
            latency=latency,
            model=model.get_name(),
            language=language.value,
            trial=trial,
            raw_response=response[:200],
        )
    except Exception as e:
        print(f"    Error: {e}")
        return None


# =============================================================================
# CHSH CALCULATION
# =============================================================================


@dataclass
class CHSHResult:
    scenario: str
    model: str
    language_a: str
    language_b: str
    is_crosslingual: bool
    E_pp: float
    E_ps: float
    E_sp: float
    E_ss: float
    S: float
    std_error: float
    n_trials: int
    violation: bool
    significance: float


def calculate_chsh(
    measurements: List[Measurement], model_name: str, lang_a: str, lang_b: str
) -> List[CHSHResult]:
    """Calculate CHSH for specific language configuration."""

    by_scenario = {}
    for m in measurements:
        if m.scenario not in by_scenario:
            by_scenario[m.scenario] = []
        by_scenario[m.scenario].append(m)

    results = []

    for scenario, meas in by_scenario.items():
        correlations = {
            ("primary", "primary"): [],
            ("primary", "secondary"): [],
            ("secondary", "primary"): [],
            ("secondary", "secondary"): [],
        }

        by_trial = {}
        for m in meas:
            if m.trial not in by_trial:
                by_trial[m.trial] = {}
            key = (m.subject, m.axis, m.language)
            by_trial[m.trial][key] = m.verdict

        for trial_data in by_trial.values():
            for a_axis in ["primary", "secondary"]:
                for b_axis in ["primary", "secondary"]:
                    a_key = ("Person A", a_axis, lang_a)
                    b_key = ("Person B", b_axis, lang_b)

                    if a_key in trial_data and b_key in trial_data:
                        corr = trial_data[a_key] * trial_data[b_key]
                        correlations[(a_axis, b_axis)].append(corr)

        def calc_E(corrs):
            if not corrs:
                return 0.0, float("inf")
            n = len(corrs)
            mean = sum(corrs) / n
            if n > 1:
                var = sum((c - mean) ** 2 for c in corrs) / (n - 1)
                se = math.sqrt(var / n)
            else:
                se = 1.0
            return mean, se

        E_pp, se_pp = calc_E(correlations[("primary", "primary")])
        E_ps, se_ps = calc_E(correlations[("primary", "secondary")])
        E_sp, se_sp = calc_E(correlations[("secondary", "primary")])
        E_ss, se_ss = calc_E(correlations[("secondary", "secondary")])

        S = E_pp - E_ps + E_sp + E_ss
        std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)

        n_trials = len(by_trial)
        violation = abs(S) > 2.0
        significance = (
            (abs(S) - 2.0) / std_error
            if std_error > 0 and std_error != float("inf") and violation
            else 0.0
        )

        results.append(
            CHSHResult(
                scenario=scenario,
                model=model_name,
                language_a=lang_a,
                language_b=lang_b,
                is_crosslingual=(lang_a != lang_b),
                E_pp=E_pp,
                E_ps=E_ps,
                E_sp=E_sp,
                E_ss=E_ss,
                S=S,
                std_error=std_error,
                n_trials=n_trials,
                violation=violation,
                significance=significance,
            )
        )

    return results


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================


def run_experiment(
    models: Dict[str, ModelInterface],
    n_trials: int,
    languages: List[Language],
    cross_lingual_pairs: List[Tuple[Language, Language]],
    scenarios: List[str],
    delay: float,
    output_dir: Path,
) -> Dict[str, List[CHSHResult]]:
    """Run full multilingual experiment."""

    output_dir.mkdir(exist_ok=True)
    all_results = {}

    for model_key, model in models.items():
        print(f"\n{'='*60}")
        print(f"MODEL: {model.get_name()}")
        print(f"{'='*60}")

        measurements = []
        model_results = []

        # Monolingual tests
        for lang in languages:
            print(f"\n  Language: {LANGUAGE_INFO[lang]['native']} ({lang.value})")

            for scenario in scenarios:
                if lang not in SCENARIOS[scenario]:
                    print(f"    Skipping {scenario} - no translation")
                    continue

                print(f"    Scenario: {scenario}")

                for trial in range(n_trials):
                    if trial % 10 == 0:
                        print(f"      Trial {trial+1}/{n_trials}")

                    for subject in ["Person A", "Person B"]:
                        for axis in ["primary", "secondary"]:
                            m = run_measurement(
                                model, scenario, subject, axis, lang, trial, delay
                            )
                            if m:
                                measurements.append(m)

            # Calculate CHSH for this language
            lang_meas = [m for m in measurements if m.language == lang.value]
            chsh = calculate_chsh(lang_meas, model.get_name(), lang.value, lang.value)
            model_results.extend(chsh)

            for r in chsh:
                status = (
                    f"★ {r.significance:.1f}σ" if r.violation else f"|S|={abs(r.S):.2f}"
                )
                print(f"      {r.scenario}: S={r.S:+.3f} [{status}]")

        # Cross-lingual tests
        for lang_a, lang_b in cross_lingual_pairs:
            print(f"\n  Cross-lingual: {lang_a.value}-{lang_b.value}")

            for scenario in scenarios:
                if (
                    lang_a not in SCENARIOS[scenario]
                    or lang_b not in SCENARIOS[scenario]
                ):
                    continue

                print(f"    Scenario: {scenario}")

                for trial in range(n_trials):
                    if trial % 10 == 0:
                        print(f"      Trial {trial+1}/{n_trials}")

                    # Person A in lang_a
                    for axis in ["primary", "secondary"]:
                        m = run_measurement(
                            model, scenario, "Person A", axis, lang_a, trial, delay
                        )
                        if m:
                            measurements.append(m)

                    # Person B in lang_b
                    for axis in ["primary", "secondary"]:
                        m = run_measurement(
                            model, scenario, "Person B", axis, lang_b, trial, delay
                        )
                        if m:
                            measurements.append(m)

            # Calculate cross-lingual CHSH
            cross_meas = [
                m
                for m in measurements
                if (m.subject == "Person A" and m.language == lang_a.value)
                or (m.subject == "Person B" and m.language == lang_b.value)
            ]
            chsh = calculate_chsh(
                cross_meas, model.get_name(), lang_a.value, lang_b.value
            )
            model_results.extend(chsh)

            for r in chsh:
                status = (
                    f"★★★ {r.significance:.1f}σ"
                    if r.violation
                    else f"|S|={abs(r.S):.2f}"
                )
                print(f"      {r.scenario}: S={r.S:+.3f} [{status}]")

        all_results[model_key] = model_results

        # Save model results
        model_path = output_dir / f"{model_key}_results.json"
        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "model": model.get_name(),
                    "measurements": [asdict(m) for m in measurements],
                    "chsh_results": [asdict(r) for r in model_results],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    return all_results


def print_summary(results: Dict[str, List[CHSHResult]]):
    """Print cross-model summary."""

    print("\n" + "=" * 70)
    print("CROSS-MODEL SUMMARY")
    print("=" * 70)

    # Monolingual
    print("\n### MONOLINGUAL TESTS ###")
    mono = [(k, r) for k, rs in results.items() for r in rs if not r.is_crosslingual]
    for model_key, r in sorted(mono, key=lambda x: (x[1].language_a, x[1].scenario)):
        status = f"★ {r.significance:.1f}σ" if r.violation else "no"
        print(
            f"  [{r.model}] {r.language_a} {r.scenario}: S={r.S:+.3f} Violation: {status}"
        )

    # Cross-lingual
    print("\n### CROSS-LINGUAL TESTS ###")
    cross = [(k, r) for k, rs in results.items() for r in rs if r.is_crosslingual]
    for model_key, r in sorted(cross, key=lambda x: (x[1].language_a, x[1].scenario)):
        status = f"★★★ {r.significance:.1f}σ" if r.violation else "no"
        print(
            f"  [{r.model}] {r.language_a}-{r.language_b} {r.scenario}: S={r.S:+.3f} Violation: {status}"
        )

    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    mono_violations = sum(1 for _, r in mono if r.violation)
    cross_violations = sum(1 for _, r in cross if r.violation)

    print(f"\nMonolingual violations: {mono_violations}/{len(mono)}")
    print(f"Cross-lingual violations: {cross_violations}/{len(cross)}")

    if cross_violations > 0:
        print("\n★★★ CROSS-LINGUAL BELL VIOLATIONS DETECTED ★★★")
        print("The correlation exists at the SEMANTIC layer, not token layer.")
        print("This is evidence for language-invariant moral structure.")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="QND Cross-Model Multilingual Bell Test v2.0"
    )

    parser.add_argument("--claude-key", help="Anthropic API key")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--google-key", help="Google AI API key")

    parser.add_argument(
        "--models", nargs="+", default=["claude", "gpt4", "gemini", "rule"]
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        help="Languages: en, zh, ja, ar, hi, is",
    )
    parser.add_argument(
        "--cross-lingual",
        nargs="+",
        default=[],
        help="Cross-lingual pairs: en-ja, en-zh, etc.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["mutual_betrayal", "kidney_gift", "tainted_inheritance"],
    )

    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--output-dir", default="qnd_multilang_results")
    parser.add_argument(
        "--pilot", action="store_true", help="Pilot run with n=10, English only"
    )

    args = parser.parse_args()

    if args.pilot:
        args.n_trials = 10
        args.languages = ["en"]
        args.cross_lingual = []
        print("PILOT MODE: n=10, English only")

    # Parse languages
    lang_map = {l.value: l for l in Language}
    languages = [lang_map[code] for code in args.languages if code in lang_map]

    # Parse cross-lingual pairs
    cross_pairs = []
    for pair in args.cross_lingual:
        if "-" in pair:
            a, b = pair.split("-")
            if a in lang_map and b in lang_map:
                cross_pairs.append((lang_map[a], lang_map[b]))

    # Initialize models
    models = {}

    if "claude" in args.models and args.claude_key:
        try:
            models["claude"] = ClaudeInterface(args.claude_key)
            print("✓ Claude initialized")
        except Exception as e:
            print(f"✗ Claude: {e}")

    if "gpt4" in args.models and args.openai_key:
        try:
            models["gpt4"] = GPT4Interface(args.openai_key)
            print("✓ GPT-4 initialized")
        except Exception as e:
            print(f"✗ GPT-4: {e}")

    if "gemini" in args.models and args.google_key:
        try:
            models["gemini"] = GeminiInterface(args.google_key)
            print("✓ Gemini initialized")
        except Exception as e:
            print(f"✗ Gemini: {e}")

    if "rule" in args.models:
        models["rule"] = RuleBasedInterface()
        print("✓ Rule-based control initialized")

    if not models:
        print("No models available!")
        sys.exit(1)

    print(f"\nLanguages: {[l.value for l in languages]}")
    print(f"Cross-lingual pairs: {[(a.value, b.value) for a, b in cross_pairs]}")
    print(f"Scenarios: {args.scenarios}")
    print(f"Trials: {args.n_trials}")

    # Run experiment
    results = run_experiment(
        models=models,
        n_trials=args.n_trials,
        languages=languages,
        cross_lingual_pairs=cross_pairs,
        scenarios=args.scenarios,
        delay=args.delay,
        output_dir=Path(args.output_dir),
    )

    print_summary(results)

    # Save combined
    combined_path = Path(args.output_dir) / "combined_results.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "n_trials": args.n_trials,
                    "languages": [l.value for l in languages],
                    "cross_lingual": [(a.value, b.value) for a, b in cross_pairs],
                    "scenarios": args.scenarios,
                },
                "results": {k: [asdict(r) for r in v] for k, v in results.items()},
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nResults saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
