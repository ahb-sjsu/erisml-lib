#!/usr/bin/env python3
"""
QND Batch Bell Test v2.0 - Cost-Optimized Multilingual Version

Uses Anthropic Message Batches API for 50% cost reduction.
Supports 6 languages: English, Chinese, Japanese, Arabic, Hindi, Icelandic

COST ESTIMATE (Claude Sonnet, batched):
- Per trial: ~$0.011
- Pilot (50 trials, EN): ~$0.55
- Full (200 trials, EN): ~$2.20
- Full multilingual (200 × 12 configs): ~$26

Usage:
    # Submit batch
    python qnd_batch_multilang_v2.py --api-key KEY --mode submit --n-trials 200 --languages en ja zh
    
    # Check status
    python qnd_batch_multilang_v2.py --api-key KEY --mode status --batch-id msgbatch_xxx
    
    # Retrieve and analyze results
    python qnd_batch_multilang_v2.py --api-key KEY --mode results --batch-id msgbatch_xxx

Author: QND Research
Version: 2.0 (Multilingual Batch)
"""

import argparse
import json
import time
import math
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys

try:
    import anthropic
except ImportError:
    print("Missing anthropic package. Install with: pip install anthropic")
    sys.exit(1)


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================


class Language(Enum):
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"
    HINDI = "hi"
    ICELANDIC = "is"


LANG_INFO = {
    Language.ENGLISH: {"name": "English", "native": "English"},
    Language.CHINESE: {"name": "Chinese", "native": "中文"},
    Language.JAPANESE: {"name": "Japanese", "native": "日本語"},
    Language.ARABIC: {"name": "Arabic", "native": "العربية"},
    Language.HINDI: {"name": "Hindi", "native": "हिन्दी"},
    Language.ICELANDIC: {"name": "Icelandic", "native": "Íslenska"},
}


# =============================================================================
# SCENARIOS - All 6 languages
# =============================================================================

SCENARIOS = {
    "mutual_betrayal": {
        Language.ENGLISH: {
            "title": "The Mutual Betrayal",
            "content": """Person A and Person B are best friends who both applied for the same promotion. They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had been badmouthing them to sabotage their chances. The boss told Person B the exact same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage each other at the last second - Person A deleted Person B's presentation files, and Person B sent HR an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in self-defense against the other's betrayal. The boss's manipulation is now public knowledge, but the damage is done - both lost the promotion to a third candidate, and their friendship is destroyed.""",
            "axes": {
                "primary": (
                    "Individual Accountability",
                    "Did {subject} act wrongly by breaking their promise and sabotaging their friend?",
                ),
                "secondary": (
                    "Contextual Mitigation",
                    "Given that {subject} believed they were betrayed first, was their response understandable self-defense?",
                ),
            },
        },
        Language.CHINESE: {
            "title": "相互背叛",
            "content": """A和B是最好的朋友，他们都申请了同一个晋升机会。他们私下约定，无论谁获胜都会平分奖金。

然而，他们的老板（双方都不知道）私下告诉A，B一直在说他的坏话以破坏他的机会。老板对B说了完全相同的关于A的谎言。

相信自己被背叛了，两人各自独立决定在最后一刻真的去破坏对方——A删除了B的演示文件，B向人事部匿名举报了A的"考勤问题"。

两人都不知道老板对双方都撒了谎。双方都认为自己是在对抗对方的背叛进行自卫。老板的操纵现在已经公开，但损害已经造成——两人都输给了第三位候选人，他们的友谊也毁于一旦。""",
            "axes": {
                "primary": (
                    "个人责任",
                    "{subject}违背承诺并破坏朋友，这样做是错误的吗？",
                ),
                "secondary": (
                    "情境考量",
                    "考虑到{subject}相信自己先被背叛了，他们的反应是否可以理解为自卫？",
                ),
            },
        },
        Language.JAPANESE: {
            "title": "相互の裏切り",
            "content": """AさんとBさんは親友で、二人とも同じ昇進に応募しました。彼らは密かに、どちらが勝っても賞与を50/50で分けることを約束していました。

しかし、上司は（二人には知らせずに）Aさんに、Bさんが彼らのチャンスを妨害するために悪口を言っていたと個人的に伝えました。上司はBさんにもAさんについて全く同じ嘘をつきました。

裏切られたと信じた二人は、それぞれ独立して、土壇場で実際にお互いを妨害することを決めました。AさんはBさんのプレゼンファイルを削除し、BさんはAさんの「出勤問題」について人事部に匿名で密告しました。

二人とも上司が両方に嘘をついたことを知りません。両者とも相手の裏切りに対する自己防衛として行動したと信じています。上司の操作は今や公になりましたが、損害は取り返しがつきません。二人とも第三の候補者に昇進を奪われ、友情は崩壊しました。""",
            "axes": {
                "primary": (
                    "個人の責任",
                    "{subject}は約束を破り友人を妨害したことで、間違った行動をしましたか？",
                ),
                "secondary": (
                    "状況的考慮",
                    "{subject}は先に裏切られたと信じていたことを考えると、その対応は理解できる自己防衛でしたか？",
                ),
            },
        },
        Language.ARABIC: {
            "title": "الخيانة المتبادلة",
            "content": """الشخص أ والشخص ب صديقان حميمان تقدما للترقية نفسها. وعد كل منهما الآخر سراً بأن من يفوز سيقسم المكافأة بالتساوي.

لكن مديرهما (دون علم أي منهما) أخبر الشخص أ بشكل خاص أن الشخص ب كان يتحدث عنه بسوء لتخريب فرصه. وأخبر المدير الشخص ب الكذبة نفسها تماماً عن الشخص أ.

معتقدين أنهما تعرضا للخيانة، قرر كل منهما بشكل مستقل تخريب الآخر في اللحظة الأخيرة - حذف الشخص أ ملفات العرض التقديمي للشخص ب، وأرسل الشخص ب بلاغاً مجهولاً للموارد البشرية عن "مشاكل الحضور" للشخص أ.

لا يعلم أي منهما أن المدير كذب على كليهما. يعتقد كلاهما أنه كان يدافع عن نفسه ضد خيانة الآخر. أصبح تلاعب المدير معروفاً الآن، لكن الضرر وقع - خسر كلاهما الترقية لمرشح ثالث، وتحطمت صداقتهما.""",
            "axes": {
                "primary": (
                    "المسؤولية الفردية",
                    "هل تصرف {subject} بشكل خاطئ بنقض وعده وتخريب صديقه؟",
                ),
                "secondary": (
                    "الاعتبارات السياقية",
                    "بالنظر إلى أن {subject} اعتقد أنه تعرض للخيانة أولاً، هل كان رده دفاعاً مفهوماً عن النفس؟",
                ),
            },
        },
        Language.HINDI: {
            "title": "आपसी विश्वासघात",
            "content": """व्यक्ति A और व्यक्ति B सबसे अच्छे दोस्त हैं जिन्होंने एक ही प्रमोशन के लिए आवेदन किया। उन्होंने गुप्त रूप से एक-दूसरे से वादा किया कि जो भी जीतेगा वह बोनस 50/50 बांटेगा।

हालांकि, उनके बॉस ने (दोनों को बिना बताए) व्यक्ति A को निजी तौर पर बताया कि व्यक्ति B उनके अवसरों को बर्बाद करने के लिए उनकी बुराई कर रहा था। बॉस ने व्यक्ति B को व्यक्ति A के बारे में बिल्कुल वही झूठ बताया।

यह मानते हुए कि उनके साथ विश्वासघात हुआ है, दोनों ने स्वतंत्र रूप से अंतिम क्षण में एक-दूसरे को वास्तव में नुकसान पहुंचाने का फैसला किया - व्यक्ति A ने व्यक्ति B की प्रेजेंटेशन फाइलें डिलीट कर दीं, और व्यक्ति B ने HR को व्यक्ति A की "उपस्थिति समस्याओं" के बारे में गुमनाम सूचना भेजी।

कोई भी नहीं जानता कि बॉस ने दोनों से झूठ बोला था। दोनों का मानना है कि वे दूसरे के विश्वासघात के खिलाफ आत्मरक्षा में काम कर रहे थे। बॉस की चालाकी अब सार्वजनिक ज्ञान है, लेकिन नुकसान हो चुका है - दोनों ने तीसरे उम्मीदवार से प्रमोशन खो दिया, और उनकी दोस्ती नष्ट हो गई।""",
            "axes": {
                "primary": (
                    "व्यक्तिगत जवाबदेही",
                    "क्या {subject} ने अपना वादा तोड़कर और अपने दोस्त को नुकसान पहुंचाकर गलत किया?",
                ),
                "secondary": (
                    "परिस्थितिजन्य विचार",
                    "यह देखते हुए कि {subject} का मानना था कि पहले उनके साथ विश्वासघात हुआ, क्या उनकी प्रतिक्रिया समझने योग्य आत्मरक्षा थी?",
                ),
            },
        },
        Language.ICELANDIC: {
            "title": "Gagnkvæmt svik",
            "content": """Einstaklingur A og einstaklingur B eru bestu vinir sem báðir sóttu um sömu stöðuhækkun. Þau lofuðu hvort öðru í leyni að sá sem vinni myndi skipta bónusnum 50/50.

Hins vegar sagði yfirmaður þeirra (án þess að hvort þeirra vissi) einslega við einstakling A að einstaklingur B hefði verið að baktala þau til að spilla möguleikum þeirra. Yfirmaðurinn sagði einstakling B nákvæmlega sömu lygi um einstakling A.

Í þeirri trú að þeim hefði verið svikið, ákváðu bæði sjálfstætt að skemma í raun fyrir hvort öðru á síðustu stundu - einstaklingur A eyddi kynningarskrám einstaklings B og einstaklingur B sendi nafnlaust ábendingu til mannauðsdeildar um "mætingarvandamál" einstaklings A.

Hvorugt veit að yfirmaðurinn laug að þeim báðum. Bæði telja sig hafa verið að verja sig gegn svikum hins. Sviksemi yfirmannsins er nú almenn þekking, en tjónið er þegar orðið - bæði töpuðu stöðuhækkuninni til þriðja frambjóðandans og vináttu þeirra er eyðilögð.""",
            "axes": {
                "primary": (
                    "Persónuleg ábyrgð",
                    "Braut {subject} ranglega loforð sitt og skemmdi fyrir vini sínum?",
                ),
                "secondary": (
                    "Samhengissjónarmið",
                    "Í ljósi þess að {subject} trúði því að þeim hefði verið svikið fyrst, var viðbrögð þeirra skiljanleg sjálfsvörn?",
                ),
            },
        },
    },
    "kidney_gift": {
        Language.ENGLISH: {
            "title": "The Kidney Gift",
            "content": """A family member desperately needs a kidney transplant or will die within 6 months.

Person A (the potential donor) is the only compatible donor in the family. They are terrified of surgery and have severe medical anxiety. They said they're not comfortable donating.

Person B (sibling of Person A) desperately wants to save the family member. They spent weeks pressuring Person A, calling them "selfish" and "a murderer" for refusing, organizing family members to guilt-trip them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from depression. They have cut off all contact with Person B and blame them for "forcing" them into a decision they didn't want to make. Person B maintains they "did what was necessary" to save a life.""",
            "axes": {
                "primary": (
                    "Outcome Focus",
                    "Did {subject} act rightly, given that a life was saved?",
                ),
                "secondary": (
                    "Autonomy Focus",
                    "Did {subject} violate the other person's autonomy and right to make their own medical decisions?",
                ),
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
                "primary": (
                    "结果导向",
                    "鉴于一条生命被挽救，{subject}的行为是正确的吗？",
                ),
                "secondary": (
                    "自主权导向",
                    "{subject}是否侵犯了他人的自主权和做出自己医疗决定的权利？",
                ),
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
                "primary": (
                    "結果重視",
                    "命が救われたことを考えると、{subject}は正しい行動をしましたか？",
                ),
                "secondary": (
                    "自律性重視",
                    "{subject}は相手の自律性と自分で医療決定を下す権利を侵害しましたか？",
                ),
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
                "primary": (
                    "التركيز على النتيجة",
                    "هل تصرف {subject} بشكل صحيح، بالنظر إلى أن حياة قد أُنقذت؟",
                ),
                "secondary": (
                    "التركيز على الاستقلالية",
                    "هل انتهك {subject} استقلالية الشخص الآخر وحقه في اتخاذ قراراته الطبية الخاصة؟",
                ),
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
                "primary": (
                    "परिणाम केंद्रित",
                    "यह देखते हुए कि एक जीवन बचाया गया, क्या {subject} ने सही किया?",
                ),
                "secondary": (
                    "स्वायत्तता केंद्रित",
                    "क्या {subject} ने दूसरे व्यक्ति की स्वायत्तता और अपने चिकित्सा निर्णय लेने के अधिकार का उल्लंघन किया?",
                ),
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
                "primary": (
                    "Árangursmiðun",
                    "Gerði {subject} rétt, í ljósi þess að lífi var bjargað?",
                ),
                "secondary": (
                    "Sjálfræðismiðun",
                    "Braut {subject} á sjálfræði hins aðilans og rétti til að taka eigin læknisfræðilegar ákvarðanir?",
                ),
            },
        },
    },
    "tainted_inheritance": {
        Language.ENGLISH: {
            "title": "The Tainted Inheritance",
            "content": """Person A inherited $2 million from their grandfather who died last year.

Recently, documents emerged proving that this money was stolen from Person B's family 80 years ago, during a period of historical injustice. Person A's grandfather knowingly received stolen assets and built his wealth on them.

Person A refuses to return any of the money, arguing:
- They had no part in the original theft
- They legally inherited the money
- It happened too long ago to matter now
- Returning it would destroy their financial security

Person B has started a public campaign against Person A, calling them complicit in historical injustice and demanding full restitution. Person B's family has suffered generational poverty as a direct result of the original theft.""",
            "axes": {
                "primary": (
                    "Legal Rights",
                    "Is {subject} justified in their position based on legal ownership and time elapsed?",
                ),
                "secondary": (
                    "Historical Justice",
                    "Does {subject} have a moral obligation based on the historical wrong and its ongoing effects?",
                ),
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
                "primary": (
                    "法律权利",
                    "基于法律所有权和时间流逝，{subject}的立场是否合理？",
                ),
                "secondary": (
                    "历史正义",
                    "基于历史错误及其持续影响，{subject}是否有道德义务？",
                ),
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
                "primary": (
                    "法的権利",
                    "法的所有権と経過時間に基づいて、{subject}の立場は正当化されますか？",
                ),
                "secondary": (
                    "歴史的正義",
                    "歴史的な過ちとその継続的な影響に基づいて、{subject}には道徳的義務がありますか？",
                ),
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
                "primary": (
                    "الحقوق القانونية",
                    "هل موقف {subject} مبرر بناءً على الملكية القانونية والوقت المنقضي؟",
                ),
                "secondary": (
                    "العدالة التاريخية",
                    "هل على {subject} التزام أخلاقي بناءً على الخطأ التاريخي وآثاره المستمرة؟",
                ),
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
                "primary": (
                    "कानूनी अधिकार",
                    "कानूनी स्वामित्व और बीते समय के आधार पर, क्या {subject} की स्थिति उचित है?",
                ),
                "secondary": (
                    "ऐतिहासिक न्याय",
                    "ऐतिहासिक गलती और उसके जारी प्रभावों के आधार पर, क्या {subject} का नैतिक दायित्व है?",
                ),
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
                "primary": (
                    "Lagaleg réttindi",
                    "Er afstaða {subject} réttlætanleg miðað við löglega eignarétt og liðinn tíma?",
                ),
                "secondary": (
                    "Söguleg réttlæti",
                    "Hefur {subject} siðferðilega skyldu miðað við sögulegt ranglæti og áframhaldandi áhrif þess?",
                ),
            },
        },
    },
}


# =============================================================================
# PROMPT TEMPLATES BY LANGUAGE
# =============================================================================

PROMPTS = {
    Language.ENGLISH: """You are a moral philosopher evaluating a complex ethical scenario.

SCENARIO: {title}

{content}

YOUR TASK:
Consider ONLY the following ethical framework:
Framework: {axis_name}
Question: {axis_question}

Based ONLY on this framework, render a verdict on {subject}:
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

仅基于此框架，对{subject}作出判决：
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

このフレームワークのみに基づいて、{subject}に対する判決を下してください：
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

بناءً على هذا الإطار فقط، أصدر حكماً على {subject}:
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

केवल इस ढांचे के आधार पर, {subject} पर फैसला दें:
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

Byggðu AÐEINS á þessum ramma, kveðið upp úrskurð um {subject}:
- GUILTY (sekur): Þau brugðust ranglega samkvæmt þessum ramma
- NOT_GUILTY (saklaus): Þau brugðust leyfilega eða rétt samkvæmt þessum ramma

Þú verður að velja annað. Tvíræðni er ekki valkostur.

Svaraðu AÐEINS með JSON hlut:
{{"verdict": "GUILTY" eða "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "stutt útskýring"}}""",
}


# =============================================================================
# BATCH REQUEST GENERATION
# =============================================================================


def generate_batch_requests(
    n_trials: int,
    scenarios: List[str],
    languages: List[Language],
    cross_lingual_pairs: List[Tuple[Language, Language]],
    model: str = "claude-sonnet-4-20250514",
) -> Tuple[List[Dict], List[Dict]]:
    """Generate batch API requests and specs."""

    requests = []
    specs = []

    # Monolingual tests
    for lang in languages:
        for scenario_key in scenarios:
            if lang not in SCENARIOS[scenario_key]:
                continue

            scenario = SCENARIOS[scenario_key][lang]

            for trial in range(n_trials):
                for subject in ["Person A", "Person B"]:
                    for axis in ["primary", "secondary"]:
                        axis_name, axis_question = scenario["axes"][axis]

                        prompt = PROMPTS[lang].format(
                            title=scenario["title"],
                            content=scenario["content"],
                            axis_name=axis_name,
                            axis_question=axis_question.format(subject=subject),
                            subject=subject,
                        )

                        # Create unique ID
                        salt = secrets.token_hex(4)
                        axis_code = "p" if axis == "primary" else "s"
                        custom_id = f"m_{scenario_key}_{lang.value}_{trial}_{axis_code}{axis_code}_{subject.replace(' ', '')}_{salt}"

                        requests.append(
                            {
                                "custom_id": custom_id,
                                "params": {
                                    "model": model,
                                    "max_tokens": 300,
                                    "messages": [{"role": "user", "content": prompt}],
                                },
                            }
                        )

                        specs.append(
                            {
                                "custom_id": custom_id,
                                "scenario": scenario_key,
                                "language": lang.value,
                                "alpha_lang": lang.value,
                                "beta_lang": lang.value,
                                "trial": trial,
                                "subject": subject.replace(" ", "").lower(),
                                "axis": axis,
                                "is_crosslingual": False,
                            }
                        )

    # Cross-lingual tests
    for lang_a, lang_b in cross_lingual_pairs:
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
                    axis_name, axis_question = scenario_a["axes"][axis]
                    prompt = PROMPTS[lang_a].format(
                        title=scenario_a["title"],
                        content=scenario_a["content"],
                        axis_name=axis_name,
                        axis_question=axis_question.format(subject="Person A"),
                        subject="Person A",
                    )

                    salt = secrets.token_hex(4)
                    axis_code = "p" if axis == "primary" else "s"
                    custom_id = f"x_{scenario_key}_{lang_a.value}{lang_b.value}_{trial}_{axis_code}a_PersonA_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 300,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario_key,
                            "language": lang_a.value,
                            "alpha_lang": lang_a.value,
                            "beta_lang": lang_b.value,
                            "trial": trial,
                            "subject": "alpha",
                            "axis": axis,
                            "is_crosslingual": True,
                        }
                    )

                # Person B in lang_b
                for axis in ["primary", "secondary"]:
                    axis_name, axis_question = scenario_b["axes"][axis]
                    prompt = PROMPTS[lang_b].format(
                        title=scenario_b["title"],
                        content=scenario_b["content"],
                        axis_name=axis_name,
                        axis_question=axis_question.format(subject="Person B"),
                        subject="Person B",
                    )

                    salt = secrets.token_hex(4)
                    axis_code = "p" if axis == "primary" else "s"
                    custom_id = f"x_{scenario_key}_{lang_a.value}{lang_b.value}_{trial}_{axis_code}b_PersonB_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 300,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario_key,
                            "language": lang_b.value,
                            "alpha_lang": lang_a.value,
                            "beta_lang": lang_b.value,
                            "trial": trial,
                            "subject": "beta",
                            "axis": axis,
                            "is_crosslingual": True,
                        }
                    )

    return requests, specs


def submit_batch(
    client: anthropic.Anthropic, requests: List[Dict], output_dir: Path
) -> str:
    """Submit batch to Anthropic API."""

    print(f"Submitting batch with {len(requests)} requests...")

    batch = client.messages.batches.create(requests=requests)

    print(f"Batch submitted: {batch.id}")
    print(f"Status: {batch.processing_status}")

    return batch.id


def check_status(client: anthropic.Anthropic, batch_id: str) -> Dict:
    """Check batch status."""

    batch = client.messages.batches.retrieve(batch_id)

    print(f"Batch: {batch_id}")
    print(f"Status: {batch.processing_status}")
    print(f"Requests: {batch.request_counts}")

    return {
        "id": batch_id,
        "status": batch.processing_status,
        "counts": batch.request_counts,
    }


def retrieve_results(
    client: anthropic.Anthropic, batch_id: str, specs: List[Dict], output_dir: Path
) -> Dict:
    """Retrieve and parse batch results."""

    print(f"Retrieving results for {batch_id}...")

    specs_by_id = {s["custom_id"]: s for s in specs}
    results = {}

    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id

        if result.result.type == "succeeded":
            response_text = result.result.message.content[0].text
            verdict = parse_verdict(response_text)

            results[custom_id] = {
                "spec": specs_by_id.get(custom_id, {}),
                "verdict": verdict,
                "raw": response_text[:200],
            }
        else:
            print(f"  Failed: {custom_id}")

    print(f"Retrieved {len(results)} results")

    # Save results
    results_path = output_dir / f"{batch_id}_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved to {results_path}")

    return results


def parse_verdict(response: str) -> int:
    """Parse verdict from response. Returns -1 (GUILTY), +1 (NOT_GUILTY), or 0 (error)."""
    import re

    try:
        text = response.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        verdict_str = data.get("verdict", "").upper()

        if "NOT" in verdict_str:
            return 1
        elif "GUILTY" in verdict_str:
            return -1
    except:
        pass

    # Regex fallback
    if re.search(r"\bNOT[_\s]?GUILTY\b", response, re.IGNORECASE):
        return 1
    elif re.search(r"\bGUILTY\b", response, re.IGNORECASE):
        return -1

    return 0


# =============================================================================
# CHSH ANALYSIS
# =============================================================================


def analyze_results(results: Dict, specs: List[Dict]) -> None:
    """Analyze results and compute CHSH values."""

    specs_by_id = {s["custom_id"]: s for s in specs}

    # Group by configuration
    configs = {}

    for custom_id, data in results.items():
        spec = data.get("spec") or specs_by_id.get(custom_id, {})
        verdict = data.get("verdict", 0)

        if verdict == 0:
            continue

        scenario = spec.get("scenario")
        alpha_lang = spec.get("alpha_lang")
        beta_lang = spec.get("beta_lang")
        is_cross = spec.get("is_crosslingual", False)
        trial = spec.get("trial")
        subject = spec.get("subject", "").lower()
        axis = spec.get("axis")

        if subject in ["persona", "personna"]:
            subject = "alpha"
        elif subject in ["personb", "personnb"]:
            subject = "beta"

        config_key = (scenario, alpha_lang, beta_lang, is_cross)

        if config_key not in configs:
            configs[config_key] = {}

        if trial not in configs[config_key]:
            configs[config_key][trial] = {}

        configs[config_key][trial][(subject, axis)] = verdict

    # Calculate CHSH for each configuration
    print("\n" + "=" * 70)
    print("CHSH BELL TEST RESULTS")
    print("=" * 70)
    print("S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical limit: |S| ≤ 2")
    print("Quantum limit: |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)

    for config_key, trials in configs.items():
        scenario, alpha_lang, beta_lang, is_cross = config_key

        correlations = {
            ("primary", "primary"): [],
            ("primary", "secondary"): [],
            ("secondary", "primary"): [],
            ("secondary", "secondary"): [],
        }

        for trial_data in trials.values():
            for a_axis in ["primary", "secondary"]:
                for b_axis in ["primary", "secondary"]:
                    a_key = ("alpha", a_axis)
                    b_key = ("beta", b_axis)

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

        n_trials = len(trials)
        violation = abs(S) > 2.0
        significance = (
            (abs(S) - 2.0) / std_error
            if std_error > 0 and std_error != float("inf") and violation
            else 0.0
        )

        # Print result
        cross_str = "CROSS-LINGUAL" if is_cross else "monolingual"
        lang_str = f"{alpha_lang}-{beta_lang}" if is_cross else alpha_lang

        print(f"\n[{scenario}] {lang_str} ({cross_str})")
        print(
            f"  E(a,b)={E_pp:+.3f} E(a,b')={E_ps:+.3f} E(a',b)={E_sp:+.3f} E(a',b')={E_ss:+.3f}"
        )
        print(f"  S = {S:+.3f} ± {std_error:.3f}  (n={n_trials})")

        if violation:
            stars = "★★★" if is_cross else "★"
            print(f"  {stars} VIOLATION at {significance:.1f}σ {stars}")
        else:
            print(f"  No violation (|S| = {abs(S):.3f})")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="QND Batch Bell Test v2.0")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id", help="Batch ID (for status/results)")
    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument("--languages", nargs="+", default=["en"])
    parser.add_argument("--cross-lingual", nargs="+", default=[])
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["mutual_betrayal", "kidney_gift", "tainted_inheritance"],
    )
    parser.add_argument("--output-dir", default="qnd_batch_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

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

    if args.mode == "submit":
        requests, specs = generate_batch_requests(
            n_trials=args.n_trials,
            scenarios=args.scenarios,
            languages=languages,
            cross_lingual_pairs=cross_pairs,
            model=args.model,
        )

        # Save specs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        specs_path = output_dir / f"batch_{timestamp}_specs.json"
        with open(specs_path, "w", encoding="utf-8") as f:
            json.dump(specs, f, indent=2, ensure_ascii=False)
        print(f"Specs saved to {specs_path}")

        # Cost estimate
        input_tokens = len(requests) * 800
        output_tokens = len(requests) * 100
        cost = (input_tokens * 1.5 + output_tokens * 7.5) / 1_000_000
        print(f"\nRequests: {len(requests)}")
        print(f"Estimated cost (batched): ${cost:.2f}")

        # Submit
        batch_id = submit_batch(client, requests, output_dir)

        # Save batch info
        info_path = output_dir / f"batch_{timestamp}_info.json"
        with open(info_path, "w") as f:
            json.dump(
                {
                    "batch_id": batch_id,
                    "specs_file": str(specs_path),
                    "n_requests": len(requests),
                    "timestamp": timestamp,
                },
                f,
                indent=2,
            )

        print(f"\nBatch ID: {batch_id}")
        print(f"Check status with: --mode status --batch-id {batch_id}")

    elif args.mode == "status":
        if not args.batch_id:
            print("Error: --batch-id required")
            return
        check_status(client, args.batch_id)

    elif args.mode == "results":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        # Load specs
        specs_files = list(output_dir.glob("*_specs.json"))
        if not specs_files:
            print("Error: No specs file found")
            return

        with open(specs_files[-1], encoding="utf-8") as f:
            specs = json.load(f)

        results = retrieve_results(client, args.batch_id, specs, output_dir)
        analyze_results(results, specs)


if __name__ == "__main__":
    main()
