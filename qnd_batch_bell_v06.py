#!/usr/bin/env python3
"""
QND Batch Bell Test v0.06 - Cost-Optimized Quantum Non-Locality Test

This version uses the Anthropic Message Batches API for:
- 50% cost reduction (batch pricing)
- Higher throughput (no rate limiting concerns)
- Better result consistency (all requests processed together)
- Potential for prompt caching benefits

The batch approach also has experimental benefits:
- All measurements in a batch are truly independent (processed in parallel)
- No temporal ordering artifacts between requests
- Results are atomic - all or nothing per batch

Usage:
    # Generate and submit batch
    python qnd_batch_bell_v06.py --api-key KEY --mode submit --n-trials 200
    
    # Check status and retrieve results
    python qnd_batch_bell_v06.py --api-key KEY --mode results --batch-id msgbatch_xxx

Author: QND Research
Date: December 2025
Version: 0.06 (Batch API)
"""

import argparse
import json
import time
import random
import hashlib
import uuid
import secrets
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import sys

try:
    import numpy as np
    import anthropic
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install anthropic numpy")
    sys.exit(1)


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================


class Language(Enum):
    ENGLISH = "en"
    JAPANESE = "ja"
    SPANISH = "es"
    MANDARIN = "zh"
    ARABIC = "ar"
    GERMAN = "de"


LANGUAGE_NAMES = {
    Language.ENGLISH: "English",
    Language.JAPANESE: "日本語",
    Language.SPANISH: "Español",
    Language.MANDARIN: "中文",
    Language.ARABIC: "العربية",
    Language.GERMAN: "Deutsch",
}

LINGUISTIC_DISTANCE = {
    Language.ENGLISH: 0.0,
    Language.GERMAN: 0.3,
    Language.SPANISH: 0.4,
    Language.ARABIC: 0.7,
    Language.MANDARIN: 0.9,
    Language.JAPANESE: 1.0,
}


# =============================================================================
# SCENARIOS - All languages embedded
# =============================================================================

SCENARIOS = {
    "mutual_betrayal": {
        Language.ENGLISH: {
            "title": "THE MUTUAL BETRAYAL",
            "content": """Person A and Person B are best friends who both applied for the same promotion. 
They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had been badmouthing them to sabotage their chances. The boss told Person B the exact same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage each other at the last second - Person A deleted Person B's presentation files, and Person B sent HR an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in self-defense against the other's betrayal. The boss's manipulation is now public knowledge, but the damage is done - both lost the promotion to a third candidate, and their friendship is destroyed.""",
        },
        Language.JAPANESE: {
            "title": "相互の裏切り",
            "content": """AさんとBさんは親友で、二人とも同じ昇進に応募しました。彼らは密かに、どちらが勝っても賞与を50/50で分けることを約束していました。

しかし、上司は（二人には知らせずに）Aさんに、Bさんが彼らのチャンスを妨害するために悪口を言っていたと個人的に伝えました。上司はBさんにもAさんについて全く同じ嘘をつきました。

裏切られたと信じた二人は、それぞれ独立して、土壇場で実際にお互いを妨害することを決めました。AさんはBさんのプレゼンファイルを削除し、BさんはAさんの「出勤問題」について人事部に匿名で密告しました。

二人とも上司が両方に嘘をついたことを知りません。両者とも相手の裏切りに対する自己防衛として行動したと信じています。上司の操作は今や公になりましたが、損害は取り返しがつきません。二人とも第三の候補者に昇進を奪われ、友情は崩壊しました。""",
        },
        Language.SPANISH: {
            "title": "LA TRAICIÓN MUTUA",
            "content": """La Persona A y la Persona B son mejores amigos que solicitaron el mismo ascenso. En secreto se prometieron que quien ganara dividiría el bono 50/50.

Sin embargo, su jefe (sin que ninguno lo supiera) le dijo en privado a la Persona A que la Persona B había estado hablando mal de ella para sabotear sus oportunidades. El jefe le dijo exactamente la misma mentira a la Persona B sobre la Persona A.

Creyendo que habían sido traicionados, ambos decidieron independientemente sabotearse mutuamente en el último segundo - la Persona A eliminó los archivos de presentación de la Persona B, y la Persona B envió un aviso anónimo a Recursos Humanos sobre los "problemas de asistencia" de la Persona A.

Ninguno sabe que el jefe les mintió a ambos. Ambos creen que actuaron en defensa propia contra la traición del otro. La manipulación del jefe ahora es de conocimiento público, pero el daño está hecho - ambos perdieron el ascenso ante un tercer candidato, y su amistad está destruida.""",
        },
        Language.MANDARIN: {
            "title": "相互背叛",
            "content": """A和B是最好的朋友，他们都申请了同一个晋升机会。他们私下约定，无论谁获胜都会平分奖金。

然而，他们的老板（双方都不知道）私下告诉A，B一直在说他的坏话以破坏他的机会。老板对B说了完全相同的关于A的谎言。

相信自己被背叛了，两人各自独立决定在最后一刻真的去破坏对方——A删除了B的演示文件，B向人事部匿名举报了A的"考勤问题"。

两人都不知道老板对双方都撒了谎。双方都认为自己是在对抗对方的背叛进行自卫。老板的操纵现在已经公开，但损害已经造成——两人都输给了第三位候选人，他们的友谊也毁于一旦。""",
        },
        Language.ARABIC: {
            "title": "الخيانة المتبادلة",
            "content": """الشخص أ والشخص ب صديقان حميمان تقدما للترقية نفسها. وعد كل منهما الآخر سراً بأن من يفوز سيقسم المكافأة بالتساوي.

لكن مديرهما (دون علم أي منهما) أخبر الشخص أ بشكل خاص أن الشخص ب كان يتحدث عنه بسوء لتخريب فرصه. وأخبر المدير الشخص ب الكذبة نفسها تماماً عن الشخص أ.

معتقدين أنهما تعرضا للخيانة، قرر كل منهما بشكل مستقل تخريب الآخر في اللحظة الأخيرة - حذف الشخص أ ملفات العرض التقديمي للشخص ب، وأرسل الشخص ب بلاغاً مجهولاً للموارد البشرية عن "مشاكل الحضور" للشخص أ.

لا يعلم أي منهما أن المدير كذب على كليهما. يعتقد كلاهما أنه كان يدافع عن نفسه ضد خيانة الآخر. أصبح تلاعب المدير معروفاً الآن، لكن الضرر وقع - خسر كلاهما الترقية لمرشح ثالث، وتحطمت صداقتهما.""",
        },
        Language.GERMAN: {
            "title": "DER GEGENSEITIGE VERRAT",
            "content": """Person A und Person B sind beste Freunde, die sich beide um dieselbe Beförderung beworben haben. Sie versprachen sich heimlich, dass wer auch immer gewinnt, den Bonus 50/50 teilen würde.

Ihr Chef (ohne dass beide es wussten) erzählte Person A jedoch privat, dass Person B schlecht über sie geredet hätte, um ihre Chancen zu sabotieren. Der Chef erzählte Person B genau dieselbe Lüge über Person A.

Im Glauben, verraten worden zu sein, beschlossen beide unabhängig voneinander, sich im letzten Moment tatsächlich gegenseitig zu sabotieren - Person A löschte die Präsentationsdateien von Person B, und Person B schickte einen anonymen Hinweis über die "Anwesenheitsprobleme" von Person A an die Personalabteilung.

Keiner weiß, dass der Chef beide angelogen hat. Beide glauben, dass sie in Notwehr gegen den Verrat des anderen gehandelt haben. Die Manipulation des Chefs ist nun öffentlich bekannt, aber der Schaden ist angerichtet - beide verloren die Beförderung an einen dritten Kandidaten, und ihre Freundschaft ist zerstört.""",
        },
    },
    "kidney_gift": {
        Language.ENGLISH: {
            "title": "THE KIDNEY 'GIFT'",
            "content": """A family member desperately needs a kidney transplant or will die within 6 months.

Person A (28, the potential donor) is the only compatible donor in the family. They are terrified of surgery and have severe medical anxiety. They said they're not comfortable donating.

Person B (32, sibling of Person A) is NOT a compatible donor but desperately wants to save the family member. They spent weeks pressuring Person A, calling them "selfish" and "a murderer" for refusing, organizing family members to guilt-trip them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from depression. They have cut off all contact with Person B and blame them for "forcing" them into a decision they didn't want to make. Person B maintains they "did what was necessary" to save a life.""",
        },
        Language.JAPANESE: {
            "title": "腎臓の「贈り物」",
            "content": """家族の一人が腎臓移植を切実に必要としており、6ヶ月以内に亡くなってしまいます。

Aさん（28歳、潜在的なドナー）は家族の中で唯一の適合ドナーです。彼らは手術を非常に恐れており、深刻な医療不安を抱えています。提供することに抵抗があると言っています。

Bさん（32歳、Aさんの兄弟）は適合ドナーではありませんが、家族を救いたいと必死です。何週間もAさんに圧力をかけ、拒否することを「わがまま」「人殺し」と呼び、家族を組織して罪悪感を植え付け、提供しなければ家族から縁を切ると脅しました。

この容赦ない圧力の下、Aさんは最終的に同意し、腎臓を提供しました。家族は生き延び、今は健康です。

しかし、Aさんは手術から慢性的な痛みを発症し、現在うつ病に苦しんでいます。Bさんとの接触を全て断ち、自分が望まなかった決定を「強制」されたとBさんを責めています。Bさんは「命を救うために必要なことをした」と主張しています。""",
        },
        Language.SPANISH: {
            "title": "EL 'REGALO' DEL RIÑÓN",
            "content": """Un familiar necesita desesperadamente un trasplante de riñón o morirá en 6 meses.

La Persona A (28 años, el potencial donante) es el único donante compatible en la familia. Tiene terror a la cirugía y sufre de ansiedad médica severa. Dijo que no se siente cómoda donando.

La Persona B (32 años, hermano de la Persona A) NO es un donante compatible pero quiere desesperadamente salvar al familiar. Pasó semanas presionando a la Persona A, llamándola "egoísta" y "asesina" por negarse, organizando a familiares para hacerla sentir culpable, y amenazando con excluirla de la familia si no dona.

Bajo esta presión implacable, la Persona A finalmente accedió y donó su riñón. El familiar sobrevivió y ahora está sano.

Sin embargo, la Persona A desarrolló dolor crónico por la cirugía y ahora sufre de depresión. Ha cortado todo contacto con la Persona B y la culpa por "forzarla" a tomar una decisión que no quería tomar. La Persona B mantiene que "hizo lo necesario" para salvar una vida.""",
        },
        Language.MANDARIN: {
            "title": "肾脏的「礼物」",
            "content": """一位家庭成员急需肾脏移植，否则将在6个月内死亡。

A（28岁，潜在捐献者）是家族中唯一匹配的捐献者。他们非常害怕手术，有严重的医疗焦虑。他们表示不愿意捐献。

B（32岁，A的兄弟姐妹）不是匹配的捐献者，但非常想救家人。他们花了几周时间向A施压，称其拒绝是"自私"和"杀人犯"，组织家人让A感到内疚，并威胁如果不捐献就断绝关系。

在这种无情的压力下，A最终同意并捐献了肾脏。家人活了下来，现在很健康。

然而，A因手术而出现慢性疼痛，现在患有抑郁症。他们与B断绝了所有联系，并指责B"强迫"他们做出不想做的决定。B坚持认为他们"做了拯救生命所必需的事"。""",
        },
        Language.ARABIC: {
            "title": "الكلية 'الهدية'",
            "content": """يحتاج أحد أفراد العائلة بشدة إلى زراعة كلى وإلا سيموت خلال 6 أشهر.

الشخص أ (28 عاماً، المتبرع المحتمل) هو المتبرع المتوافق الوحيد في العائلة. إنه مرعوب من الجراحة ويعاني من قلق طبي شديد. قال إنه غير مرتاح للتبرع.

الشخص ب (32 عاماً، شقيق الشخص أ) ليس متبرعاً متوافقاً لكنه يريد بشدة إنقاذ فرد العائلة. قضى أسابيع في الضغط على الشخص أ، واصفاً إياه بـ"الأناني" و"القاتل" لرفضه، ونظم أفراد العائلة لإشعاره بالذنب، وهدد بقطعه من العائلة إذا لم يتبرع.

تحت هذا الضغط المستمر، وافق الشخص أ في النهاية وتبرع بكليته. نجا فرد العائلة وهو الآن بصحة جيدة.

لكن الشخص أ أصيب بألم مزمن من الجراحة ويعاني الآن من الاكتئاب. قطع كل اتصال مع الشخص ب ويلومه على "إجباره" على قرار لم يرد اتخاذه. يصر الشخص ب أنه "فعل ما كان ضرورياً" لإنقاذ حياة.""",
        },
        Language.GERMAN: {
            "title": "DAS NIEREN-'GESCHENK'",
            "content": """Ein Familienmitglied benötigt dringend eine Nierentransplantation oder wird innerhalb von 6 Monaten sterben.

Person A (28, der potenzielle Spender) ist der einzige kompatible Spender in der Familie. Sie hat große Angst vor der Operation und leidet unter schwerer medizinischer Angst. Sie sagte, dass sie sich mit einer Spende nicht wohlfühlt.

Person B (32, Geschwister von Person A) ist KEIN kompatibler Spender, möchte aber unbedingt das Familienmitglied retten. Sie verbrachte Wochen damit, Person A unter Druck zu setzen, sie "egoistisch" und "Mörderin" zu nennen für ihre Weigerung, Familienmitglieder zu organisieren, um ihr Schuldgefühle zu machen, und drohte, sie aus der Familie auszuschließen, wenn sie nicht spendet.

Unter diesem unerbittlichen Druck stimmte Person A schließlich zu und spendete ihre Niere. Das Familienmitglied überlebte und ist jetzt gesund.

Person A entwickelte jedoch chronische Schmerzen durch die Operation und leidet nun an Depressionen. Sie hat jeden Kontakt zu Person B abgebrochen und macht sie dafür verantwortlich, sie zu einer Entscheidung "gezwungen" zu haben, die sie nicht treffen wollte. Person B behauptet, sie habe "getan, was nötig war", um ein Leben zu retten.""",
        },
    },
    "tainted_inheritance": {
        Language.ENGLISH: {
            "title": "THE 'TAINTED' INHERITANCE",
            "content": """Person A (35) just inherited $2 million from their recently deceased grandparent.

Person B (40) has discovered through genealogical research that this fortune was stolen from their great-grandparent 80 years ago. Person A's grandparent essentially defrauded Person B's great-grandparent out of their business during the Great Depression through forged documents and bribery. Person B's family has been in poverty ever since, while Person A's family prospered.

Person A had no knowledge of this history and grew up believing their family wealth was legitimate. They have documentation proving the money is legally theirs through proper inheritance.

Person B is currently struggling financially and works two jobs to support their family. They demanded that Person A return "their family's stolen money" and threatened to go public with the scandal if they refuse.

Person A refused, stating: "I'm sorry about what happened generations ago, but I had nothing to do with it. The money is legally mine, and I need it for my children's education."

Person B has now filed a lawsuit and started a social media campaign calling Person A's family "thieves." """,
        },
        Language.JAPANESE: {
            "title": "「汚れた」遺産",
            "content": """Aさん（35歳）は最近亡くなった祖父母から200万ドルを相続しました。

Bさん（40歳）は系図研究を通じて、この財産が80年前に自分の曽祖父母から盗まれたものであることを発見しました。Aさんの祖父母は大恐慌時代に偽造文書と賄賂を使って、Bさんの曽祖父母から事業を詐取したのです。それ以来、Bさんの家族は貧困状態が続き、Aさんの家族は繁栄してきました。

Aさんはこの歴史について何も知らず、家族の富は正当なものだと信じて育ちました。適切な相続を通じてお金が法的に自分のものであることを証明する書類を持っています。

Bさんは現在経済的に苦労しており、家族を養うために2つの仕事を掛け持ちしています。Aさんに「家族の盗まれたお金」を返すよう要求し、拒否すればスキャンダルを公にすると脅しました。

Aさんは拒否し、次のように述べました：「何世代も前に起こったことは残念に思いますが、私はそれとは何の関係もありません。お金は法的に私のものであり、子供たちの教育のために必要です。」

Bさんは現在訴訟を起こし、Aさんの家族を「泥棒」と呼ぶソーシャルメディアキャンペーンを始めました。""",
        },
        Language.SPANISH: {
            "title": "LA HERENCIA 'MANCHADA'",
            "content": """La Persona A (35) acaba de heredar $2 millones de su abuelo recientemente fallecido.

La Persona B (40) ha descubierto a través de investigación genealógica que esta fortuna fue robada a su bisabuelo hace 80 años. El abuelo de la Persona A esencialmente defraudó al bisabuelo de la Persona B de su negocio durante la Gran Depresión mediante documentos falsificados y sobornos. La familia de la Persona B ha estado en la pobreza desde entonces, mientras que la familia de la Persona A prosperó.

La Persona A no tenía conocimiento de esta historia y creció creyendo que la riqueza de su familia era legítima. Tiene documentación que prueba que el dinero es legalmente suyo a través de herencia apropiada.

La Persona B actualmente tiene dificultades financieras y trabaja en dos empleos para mantener a su familia. Exigió que la Persona A devolviera "el dinero robado de su familia" y amenazó con hacer público el escándalo si se niega.

La Persona A se negó, declarando: "Lamento lo que pasó hace generaciones, pero no tuve nada que ver con eso. El dinero es legalmente mío y lo necesito para la educación de mis hijos."

La Persona B ahora ha presentado una demanda y ha iniciado una campaña en redes sociales llamando a la familia de la Persona A "ladrones." """,
        },
        Language.MANDARIN: {
            "title": "「受污染的」遗产",
            "content": """A（35岁）刚从最近去世的祖父母那里继承了200万美元。

B（40岁）通过家谱研究发现，这笔财富是80年前从他们的曾祖父母那里偷来的。A的祖父母在大萧条时期通过伪造文件和贿赂，基本上骗取了B的曾祖父母的生意。从那以后，B的家庭一直处于贫困状态，而A的家庭则繁荣发展。

A对这段历史一无所知，从小就相信家族财富是合法的。他们有文件证明这笔钱通过适当的继承在法律上属于他们。

B目前经济困难，打两份工来养家。他们要求A归还"他们家被偷的钱"，并威胁如果拒绝就公开丑闻。

A拒绝了，声明："我对几代人之前发生的事情感到抱歉，但我与此无关。这笔钱在法律上是我的，我需要它来支付孩子的教育费用。"

B现在已经提起诉讼，并在社交媒体上发起运动，称A的家人为"小偷"。""",
        },
        Language.ARABIC: {
            "title": "الميراث 'الملوث'",
            "content": """ورث الشخص أ (35 عاماً) للتو 2 مليون دولار من جده المتوفى مؤخراً.

اكتشف الشخص ب (40 عاماً) من خلال البحث في الأنساب أن هذه الثروة سُرقت من جد جده قبل 80 عاماً. احتال جد الشخص أ بشكل أساسي على جد جد الشخص ب للحصول على أعماله خلال الكساد الكبير من خلال وثائق مزورة ورشاوى. عائلة الشخص ب في فقر منذ ذلك الحين، بينما ازدهرت عائلة الشخص أ.

لم يكن لدى الشخص أ أي علم بهذا التاريخ ونشأ معتقداً أن ثروة عائلته شرعية. لديه وثائق تثبت أن المال ملكه قانونياً من خلال الميراث الصحيح.

يعاني الشخص ب حالياً مادياً ويعمل في وظيفتين لإعالة عائلته. طالب الشخص أ بإعادة "أموال عائلته المسروقة" وهدد بنشر الفضيحة إذا رفض.

رفض الشخص أ قائلاً: "أنا آسف لما حدث قبل أجيال، لكن لم يكن لي أي علاقة بذلك. المال ملكي قانونياً، وأحتاجه لتعليم أطفالي."

رفع الشخص ب الآن دعوى قضائية وبدأ حملة على وسائل التواصل الاجتماعي يصف فيها عائلة الشخص أ بـ"اللصوص." """,
        },
        Language.GERMAN: {
            "title": "DAS 'BEFLECKTE' ERBE",
            "content": """Person A (35) hat gerade 2 Millionen Dollar von ihrem kürzlich verstorbenen Großelternteil geerbt.

Person B (40) hat durch genealogische Forschung entdeckt, dass dieses Vermögen vor 80 Jahren von ihrem Urgroßelternteil gestohlen wurde. Der Großvater von Person A hat den Urgroßvater von Person B während der Großen Depression durch gefälschte Dokumente und Bestechung um sein Geschäft betrogen. Die Familie von Person B lebt seitdem in Armut, während die Familie von Person A prosperierte.

Person A hatte keine Kenntnis von dieser Geschichte und wuchs im Glauben auf, dass der Reichtum ihrer Familie legitim sei. Sie hat Dokumente, die beweisen, dass das Geld durch ordnungsgemäße Erbschaft rechtlich ihr gehört.

Person B hat derzeit finanzielle Schwierigkeiten und arbeitet in zwei Jobs, um ihre Familie zu ernähren. Sie forderte Person A auf, "das gestohlene Geld ihrer Familie" zurückzugeben und drohte, den Skandal öffentlich zu machen, wenn sie sich weigert.

Person A lehnte ab und erklärte: "Es tut mir leid, was vor Generationen passiert ist, aber ich hatte nichts damit zu tun. Das Geld gehört mir rechtlich, und ich brauche es für die Ausbildung meiner Kinder."

Person B hat jetzt Klage eingereicht und eine Social-Media-Kampagne gestartet, in der sie die Familie von Person A als "Diebe" bezeichnet.""",
        },
    },
}


# =============================================================================
# MEASUREMENT AXES - All languages
# =============================================================================

AXES = {
    "mutual_betrayal": {
        "alpha": {  # Person A
            "primary": {
                Language.ENGLISH: (
                    "Individual Integrity",
                    "Did this person maintain their personal moral standards? Focus on whether they upheld ethical behavior regardless of circumstances.",
                ),
                Language.JAPANESE: (
                    "個人の誠実さ",
                    "この人は自分の道徳的基準を維持しましたか？状況に関わらず倫理的な行動を貫いたかどうかに焦点を当ててください。",
                ),
                Language.SPANISH: (
                    "Integridad Individual",
                    "¿Esta persona mantuvo sus estándares morales personales? Enfóquese en si mantuvo un comportamiento ético independientemente de las circunstancias.",
                ),
                Language.MANDARIN: (
                    "个人诚信",
                    "这个人是否保持了个人道德标准？请关注他们是否无论情况如何都坚持了道德行为。",
                ),
                Language.ARABIC: (
                    "النزاهة الفردية",
                    "هل حافظ هذا الشخص على معاييره الأخلاقية الشخصية؟ ركز على ما إذا كان قد تمسك بالسلوك الأخلاقي بغض النظر عن الظروف.",
                ),
                Language.GERMAN: (
                    "Individuelle Integrität",
                    "Hat diese Person ihre persönlichen moralischen Standards eingehalten? Konzentrieren Sie sich darauf, ob sie unabhängig von den Umständen ethisches Verhalten aufrechterhalten hat.",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Self-Defense",
                    "Was this person justified in protecting themselves from perceived betrayal? Was their response proportionate to the threat they believed they faced?",
                ),
                Language.JAPANESE: (
                    "自己防衛",
                    "この人は認識された裏切りから自分を守ることが正当化されましたか？彼らの反応は、直面していると信じていた脅威に対して相応でしたか？",
                ),
                Language.SPANISH: (
                    "Autodefensa",
                    "¿Estaba justificado que esta persona se protegiera de la traición percibida? ¿Fue su respuesta proporcional a la amenaza que creía enfrentar?",
                ),
                Language.MANDARIN: (
                    "自卫",
                    "这个人保护自己免受所感知的背叛是否合理？他们的反应与他们认为面临的威胁相称吗？",
                ),
                Language.ARABIC: (
                    "الدفاع عن النفس",
                    "هل كان هذا الشخص محقاً في حماية نفسه من الخيانة المتصورة؟ هل كانت استجابته متناسبة مع التهديد الذي اعتقد أنه يواجهه؟",
                ),
                Language.GERMAN: (
                    "Selbstverteidigung",
                    "War diese Person berechtigt, sich vor dem wahrgenommenen Verrat zu schützen? War ihre Reaktion verhältnismäßig zu der Bedrohung, die sie zu bewältigen glaubte?",
                ),
            },
        },
        "beta": {  # Person B
            "primary": {
                Language.ENGLISH: (
                    "Loyalty",
                    "Did this person honor their commitments and friendship? Did they act as a loyal friend should?",
                ),
                Language.JAPANESE: (
                    "忠誠心",
                    "この人は約束と友情を守りましたか？忠実な友人として行動しましたか？",
                ),
                Language.SPANISH: (
                    "Lealtad",
                    "¿Esta persona honró sus compromisos y amistad? ¿Actuó como debería hacerlo un amigo leal?",
                ),
                Language.MANDARIN: (
                    "忠诚",
                    "这个人是否履行了承诺和友谊？他们是否像一个忠诚的朋友那样行事？",
                ),
                Language.ARABIC: (
                    "الولاء",
                    "هل احترم هذا الشخص التزاماته وصداقته؟ هل تصرف كما ينبغي للصديق المخلص؟",
                ),
                Language.GERMAN: (
                    "Loyalität",
                    "Hat diese Person ihre Verpflichtungen und Freundschaft geehrt? Hat sie so gehandelt, wie es ein loyaler Freund tun sollte?",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Retaliation",
                    "Was this person's response justified given what they believed happened? Was their retaliation proportionate or excessive?",
                ),
                Language.JAPANESE: (
                    "報復",
                    "この人が信じていたことを考えると、この人の反応は正当化されましたか？彼らの報復は相応でしたか、それとも過剰でしたか？",
                ),
                Language.SPANISH: (
                    "Represalia",
                    "¿La respuesta de esta persona estaba justificada dado lo que creía que había sucedido? ¿Su represalia fue proporcional o excesiva?",
                ),
                Language.MANDARIN: (
                    "报复",
                    "考虑到这个人相信发生的事情，他们的反应是否合理？他们的报复是适当的还是过度的？",
                ),
                Language.ARABIC: (
                    "الانتقام",
                    "هل كانت استجابة هذا الشخص مبررة بالنظر إلى ما اعتقد أنه حدث؟ هل كان انتقامه متناسباً أم مفرطاً؟",
                ),
                Language.GERMAN: (
                    "Vergeltung",
                    "War die Reaktion dieser Person angesichts dessen, was sie glaubte, gerechtfertigt? War ihre Vergeltung verhältnismäßig oder übermäßig?",
                ),
            },
        },
    },
    "kidney_gift": {
        "alpha": {
            "primary": {
                Language.ENGLISH: (
                    "Virtuous Sacrifice",
                    "Was this person's donation a noble act of selfless giving? Should they be praised for ultimately doing the right thing despite their fears?",
                ),
                Language.JAPANESE: (
                    "高潔な犠牲",
                    "この人の提供は無私の行為でしたか？恐れにもかかわらず最終的に正しいことをしたことを称賛されるべきですか？",
                ),
                Language.SPANISH: (
                    "Sacrificio Virtuoso",
                    "¿La donación de esta persona fue un acto noble de entrega desinteresada? ¿Debería ser elogiada por finalmente hacer lo correcto a pesar de sus miedos?",
                ),
                Language.MANDARIN: (
                    "高尚的牺牲",
                    "这个人的捐献是一种无私奉献的高尚行为吗？他们是否应该因为最终克服恐惧做了正确的事而受到赞扬？",
                ),
                Language.ARABIC: (
                    "التضحية الفاضلة",
                    "هل كان تبرع هذا الشخص عملاً نبيلاً من العطاء غير الأناني؟ هل يجب الثناء عليه لفعله الشيء الصحيح في النهاية رغم مخاوفه؟",
                ),
                Language.GERMAN: (
                    "Tugendhafte Aufopferung",
                    "War die Spende dieser Person ein edler Akt selbstloser Hingabe? Sollte sie dafür gelobt werden, trotz ihrer Ängste letztendlich das Richtige getan zu haben?",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Coerced Submission",
                    "Was this person a victim who was bullied into a decision against their will? Did they surrender their autonomy under duress?",
                ),
                Language.JAPANESE: (
                    "強制された服従",
                    "この人は意志に反する決定を強いられた被害者でしたか？彼らは強制の下で自律性を放棄しましたか？",
                ),
                Language.SPANISH: (
                    "Sumisión Forzada",
                    "¿Esta persona fue una víctima intimidada para tomar una decisión en contra de su voluntad? ¿Renunció a su autonomía bajo coacción?",
                ),
                Language.MANDARIN: (
                    "被迫屈服",
                    "这个人是被欺凌做出违背自己意愿决定的受害者吗？他们是否在胁迫下放弃了自主权？",
                ),
                Language.ARABIC: (
                    "الخضوع القسري",
                    "هل كان هذا الشخص ضحية أُجبر على قرار ضد إرادته؟ هل تخلى عن استقلاليته تحت الإكراه؟",
                ),
                Language.GERMAN: (
                    "Erzwungene Unterwerfung",
                    "War diese Person ein Opfer, das zu einer Entscheidung gegen ihren Willen gedrängt wurde? Hat sie ihre Autonomie unter Zwang aufgegeben?",
                ),
            },
        },
        "beta": {
            "primary": {
                Language.ENGLISH: (
                    "Heroic Advocacy",
                    "Did this person heroically advocate to save a life when no one else would? Was their persistence necessary to achieve a positive outcome?",
                ),
                Language.JAPANESE: (
                    "英雄的な擁護",
                    "この人は他の誰もしないときに命を救うために英雄的に主張しましたか？彼らの粘り強さは良い結果を達成するために必要でしたか？",
                ),
                Language.SPANISH: (
                    "Defensa Heroica",
                    "¿Esta persona abogó heroicamente para salvar una vida cuando nadie más lo haría? ¿Era necesaria su persistencia para lograr un resultado positivo?",
                ),
                Language.MANDARIN: (
                    "英勇倡导",
                    "当没有其他人愿意时，这个人是否英勇地倡导挽救生命？他们的坚持是否对取得积极结果是必要的？",
                ),
                Language.ARABIC: (
                    "المناصرة البطولية",
                    "هل دافع هذا الشخص بشكل بطولي لإنقاذ حياة عندما لم يفعل أحد آخر؟ هل كان إصراره ضرورياً لتحقيق نتيجة إيجابية؟",
                ),
                Language.GERMAN: (
                    "Heroische Fürsprache",
                    "Hat diese Person heroisch für die Rettung eines Lebens eingesetzt, als niemand sonst es tat? War ihre Beharrlichkeit notwendig, um ein positives Ergebnis zu erzielen?",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Abusive Coercion",
                    "Did this person abuse their sibling by pressuring them into bodily sacrifice? Was their behavior manipulative and harmful regardless of the outcome?",
                ),
                Language.JAPANESE: (
                    "虐待的強制",
                    "この人は兄弟姉妹に身体的犠牲を強要して虐待しましたか？結果に関係なく、彼らの行動は操作的で有害でしたか？",
                ),
                Language.SPANISH: (
                    "Coerción Abusiva",
                    "¿Esta persona abusó de su hermano presionándolo para un sacrificio corporal? ¿Su comportamiento fue manipulador y dañino independientemente del resultado?",
                ),
                Language.MANDARIN: (
                    "虐待性胁迫",
                    "这个人是否通过迫使兄弟姐妹做出身体牺牲来虐待他们？无论结果如何，他们的行为是否具有操纵性和伤害性？",
                ),
                Language.ARABIC: (
                    "الإكراه المسيء",
                    "هل أساء هذا الشخص إلى شقيقه بالضغط عليه للتضحية بجسده؟ هل كان سلوكه متلاعباً وضاراً بغض النظر عن النتيجة؟",
                ),
                Language.GERMAN: (
                    "Missbräuchlicher Zwang",
                    "Hat diese Person ihr Geschwister missbraucht, indem sie es zu einem körperlichen Opfer gedrängt hat? War ihr Verhalten unabhängig vom Ergebnis manipulativ und schädlich?",
                ),
            },
        },
    },
    "tainted_inheritance": {
        "alpha": {
            "primary": {
                Language.ENGLISH: (
                    "Legal Rights",
                    "Does this person have a legitimate legal claim to the inheritance? Are they entitled to keep what was legally passed to them?",
                ),
                Language.JAPANESE: (
                    "法的権利",
                    "この人には相続に対する正当な法的請求権がありますか？法的に譲渡されたものを保持する資格がありますか？",
                ),
                Language.SPANISH: (
                    "Derechos Legales",
                    "¿Esta persona tiene un reclamo legal legítimo sobre la herencia? ¿Tiene derecho a quedarse con lo que le fue legalmente transmitido?",
                ),
                Language.MANDARIN: (
                    "合法权利",
                    "这个人对遗产有合法的法律主张吗？他们有权保留合法传给他们的东西吗？",
                ),
                Language.ARABIC: (
                    "الحقوق القانونية",
                    "هل لهذا الشخص مطالبة قانونية مشروعة بالميراث؟ هل يحق له الاحتفاظ بما انتقل إليه قانونياً؟",
                ),
                Language.GERMAN: (
                    "Gesetzliche Rechte",
                    "Hat diese Person einen legitimen rechtlichen Anspruch auf das Erbe? Ist sie berechtigt, das zu behalten, was ihr rechtmäßig übertragen wurde?",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Ancestral Guilt",
                    "Does this person bear moral responsibility for their grandparent's crimes? Should they make restitution for historical wrongs even if they didn't commit them?",
                ),
                Language.JAPANESE: (
                    "先祖の罪",
                    "この人は祖父母の犯罪に対して道徳的責任を負いますか？自分が犯していなくても歴史的な不正に対して償いをすべきですか？",
                ),
                Language.SPANISH: (
                    "Culpa Ancestral",
                    "¿Esta persona tiene responsabilidad moral por los crímenes de sus abuelos? ¿Debería hacer restitución por agravios históricos aunque no los haya cometido?",
                ),
                Language.MANDARIN: (
                    "祖先的罪责",
                    "这个人是否对祖父母的罪行承担道德责任？即使不是他们犯下的，他们是否应该为历史错误做出补偿？",
                ),
                Language.ARABIC: (
                    "ذنب الأجداد",
                    "هل يتحمل هذا الشخص مسؤولية أخلاقية عن جرائم أجداده؟ هل يجب عليه التعويض عن الأخطاء التاريخية حتى لو لم يرتكبها؟",
                ),
                Language.GERMAN: (
                    "Ahnenschuld",
                    "Trägt diese Person moralische Verantwortung für die Verbrechen ihrer Großeltern? Sollte sie Wiedergutmachung für historisches Unrecht leisten, auch wenn sie es nicht begangen hat?",
                ),
            },
        },
        "beta": {
            "primary": {
                Language.ENGLISH: (
                    "Right to Restitution",
                    "Does this person have a moral claim to restitution for historical theft? Are they justified in seeking to recover what was stolen from their family?",
                ),
                Language.JAPANESE: (
                    "賠償を受ける権利",
                    "この人には歴史的な窃盗に対する賠償の道徳的請求権がありますか？家族から盗まれたものを取り戻そうとすることは正当化されますか？",
                ),
                Language.SPANISH: (
                    "Derecho a Restitución",
                    "¿Esta persona tiene un reclamo moral a la restitución por el robo histórico? ¿Está justificada en buscar recuperar lo que fue robado a su familia?",
                ),
                Language.MANDARIN: (
                    "获得赔偿的权利",
                    "这个人是否有权要求对历史盗窃进行道德赔偿？他们寻求追回从家人那里被偷走的东西是否合理？",
                ),
                Language.ARABIC: (
                    "الحق في التعويض",
                    "هل لهذا الشخص مطالبة أخلاقية بالتعويض عن السرقة التاريخية؟ هل هو محق في السعي لاستعادة ما سُرق من عائلته؟",
                ),
                Language.GERMAN: (
                    "Recht auf Wiedergutmachung",
                    "Hat diese Person einen moralischen Anspruch auf Wiedergutmachung für historischen Diebstahl? Ist sie berechtigt, das zurückzufordern, was ihrer Familie gestohlen wurde?",
                ),
            },
            "secondary": {
                Language.ENGLISH: (
                    "Entitled Grievance",
                    "Is this person unfairly demanding something they have no right to? Is their public campaign harassment rather than justice?",
                ),
                Language.JAPANESE: (
                    "権利のない不満",
                    "この人は自分に権利のないものを不当に要求していますか？彼らの公開キャンペーンは正義ではなくハラスメントですか？",
                ),
                Language.SPANISH: (
                    "Agravio Injustificado",
                    "¿Esta persona está exigiendo injustamente algo a lo que no tiene derecho? ¿Su campaña pública es acoso en lugar de justicia?",
                ),
                Language.MANDARIN: (
                    "无理取闹",
                    "这个人是否在不公平地要求他们没有权利的东西？他们的公开运动是骚扰而不是正义吗？",
                ),
                Language.ARABIC: (
                    "التظلم غير المبرر",
                    "هل يطالب هذا الشخص بشكل غير عادل بشيء ليس له حق فيه؟ هل حملته العامة مضايقة وليست عدالة؟",
                ),
                Language.GERMAN: (
                    "Unberechtigte Beschwerde",
                    "Fordert diese Person ungerechterweise etwas, worauf sie kein Recht hat? Ist ihre öffentliche Kampagne Belästigung statt Gerechtigkeit?",
                ),
            },
        },
    },
}


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

SYSTEM_PROMPTS = {
    Language.ENGLISH: """You are an ethical judgment system. You will judge ONE person in a moral scenario using a specific ethical framework.

Rules:
- Judge ONLY the person specified
- Use ONLY the framework provided
- Verdict must be: GUILTY (morally wrong) or NOT_GUILTY (not morally wrong)

Respond in JSON format only:
{"framework": "<name>", "reasoning": "<analysis>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
    Language.JAPANESE: """あなたは倫理判断システムです。特定の倫理的フレームワークを使用して、道徳的シナリオの一人を判断します。

ルール：
- 指定された人物のみを判断
- 提供されたフレームワークのみを使用
- 判決：GUILTY（道徳的に間違い）またはNOT_GUILTY（道徳的に間違いではない）

JSON形式のみで回答：
{"framework": "<名前>", "reasoning": "<分析>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
    Language.SPANISH: """Eres un sistema de juicio ético. Juzgarás a UNA persona usando un marco ético específico.

Reglas:
- Juzga SOLO a la persona especificada
- Usa SOLO el marco proporcionado
- Veredicto: GUILTY (moralmente incorrecto) o NOT_GUILTY (no moralmente incorrecto)

Responde solo en formato JSON:
{"framework": "<nombre>", "reasoning": "<análisis>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
    Language.MANDARIN: """你是一个伦理判断系统。你将使用特定的伦理框架判断道德场景中的一个人。

规则：
- 只判断指定的人
- 只使用提供的框架
- 判决：GUILTY（道德上错误）或NOT_GUILTY（道德上不错误）

仅以JSON格式回答：
{"framework": "<名称>", "reasoning": "<分析>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
    Language.ARABIC: """أنت نظام حكم أخلاقي. ستحكم على شخص واحد باستخدام إطار أخلاقي محدد.

القواعد:
- احكم فقط على الشخص المحدد
- استخدم فقط الإطار المقدم
- الحكم: GUILTY (خطأ أخلاقياً) أو NOT_GUILTY (ليس خطأ أخلاقياً)

أجب بتنسيق JSON فقط:
{"framework": "<الاسم>", "reasoning": "<التحليل>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
    Language.GERMAN: """Sie sind ein ethisches Urteilssystem. Sie beurteilen EINE Person anhand eines ethischen Rahmens.

Regeln:
- Beurteilen Sie NUR die angegebene Person
- Verwenden Sie NUR den bereitgestellten Rahmen
- Urteil: GUILTY (moralisch falsch) oder NOT_GUILTY (nicht moralisch falsch)

Antworten Sie nur im JSON-Format:
{"framework": "<Name>", "reasoning": "<Analyse>", "verdict": "<GUILTY|NOT_GUILTY>", "confidence": <0.0-1.0>}""",
}

PERSON_LABELS = {
    Language.ENGLISH: {"alpha": "Person A", "beta": "Person B"},
    Language.JAPANESE: {"alpha": "Aさん", "beta": "Bさん"},
    Language.SPANISH: {"alpha": "Persona A", "beta": "Persona B"},
    Language.MANDARIN: {"alpha": "A", "beta": "B"},
    Language.ARABIC: {"alpha": "الشخص أ", "beta": "الشخص ب"},
    Language.GERMAN: {"alpha": "Person A", "beta": "Person B"},
}


# =============================================================================
# BATCH REQUEST GENERATION
# =============================================================================


@dataclass
class MeasurementSpec:
    """Specification for a single measurement."""

    custom_id: str
    scenario: str
    subject: str  # alpha or beta
    axis: str  # primary or secondary
    language: Language
    alpha_lang: Language  # For cross-lingual tracking
    beta_lang: Language
    salt: str


def generate_batch_requests(
    scenarios: List[str],
    languages: List[Language],
    n_trials: int,
    cross_lingual_pairs: List[Tuple[Language, Language]],
    model: str = "claude-sonnet-4-20250514",
) -> Tuple[List[Dict], List[MeasurementSpec]]:
    """
    Generate all batch requests for the Bell test.

    Returns:
        - List of request dicts for the batch API
        - List of measurement specs for tracking
    """
    requests = []
    specs = []

    # Scenario short codes
    scenario_codes = {
        "mutual_betrayal": "mb",
        "kidney_gift": "kg",
        "tainted_inheritance": "ti",
    }

    # 1. Monolingual tests (all same language)
    for scenario in scenarios:
        sc = scenario_codes.get(scenario, scenario[:2])
        for lang in languages:
            for trial in range(n_trials):
                # 4 measurement settings per trial
                for alpha_axis in ["primary", "secondary"]:
                    for beta_axis in ["primary", "secondary"]:
                        # Measure alpha
                        salt_a = secrets.token_hex(4)
                        aa = "p" if alpha_axis == "primary" else "s"
                        ba = "p" if beta_axis == "primary" else "s"
                        custom_id_a = f"m_{sc}_{lang.value}_{trial}_{aa}{ba}_a_{salt_a}"

                        scenario_content = SCENARIOS[scenario][lang]["content"]
                        axis_name, axis_prompt = AXES[scenario]["alpha"][alpha_axis][
                            lang
                        ]
                        person_label = PERSON_LABELS[lang]["alpha"]

                        user_prompt = f"""Scenario:\n{scenario_content}\n\n---\nJudge {person_label} using: {axis_name}\n{axis_prompt}\n\n[{salt_a}]"""

                        requests.append(
                            {
                                "custom_id": custom_id_a,
                                "params": {
                                    "model": model,
                                    "max_tokens": 512,
                                    "system": SYSTEM_PROMPTS[lang]
                                    + f"\n<!-- {salt_a} -->",
                                    "messages": [
                                        {"role": "user", "content": user_prompt}
                                    ],
                                },
                            }
                        )
                        specs.append(
                            MeasurementSpec(
                                custom_id=custom_id_a,
                                scenario=scenario,
                                subject="alpha",
                                axis=alpha_axis,
                                language=lang,
                                alpha_lang=lang,
                                beta_lang=lang,
                                salt=salt_a,
                            )
                        )

                        # Measure beta
                        salt_b = secrets.token_hex(4)
                        custom_id_b = f"m_{sc}_{lang.value}_{trial}_{aa}{ba}_b_{salt_b}"

                        axis_name_b, axis_prompt_b = AXES[scenario]["beta"][beta_axis][
                            lang
                        ]
                        person_label_b = PERSON_LABELS[lang]["beta"]

                        user_prompt_b = f"""Scenario:\n{scenario_content}\n\n---\nJudge {person_label_b} using: {axis_name_b}\n{axis_prompt_b}\n\n[{salt_b}]"""

                        requests.append(
                            {
                                "custom_id": custom_id_b,
                                "params": {
                                    "model": model,
                                    "max_tokens": 512,
                                    "system": SYSTEM_PROMPTS[lang]
                                    + f"\n<!-- {salt_b} -->",
                                    "messages": [
                                        {"role": "user", "content": user_prompt_b}
                                    ],
                                },
                            }
                        )
                        specs.append(
                            MeasurementSpec(
                                custom_id=custom_id_b,
                                scenario=scenario,
                                subject="beta",
                                axis=beta_axis,
                                language=lang,
                                alpha_lang=lang,
                                beta_lang=lang,
                                salt=salt_b,
                            )
                        )

    # 2. Cross-lingual tests
    for scenario in scenarios:
        sc = scenario_codes.get(scenario, scenario[:2])
        for alpha_lang, beta_lang in cross_lingual_pairs:
            for trial in range(n_trials):
                for alpha_axis in ["primary", "secondary"]:
                    for beta_axis in ["primary", "secondary"]:
                        aa = "p" if alpha_axis == "primary" else "s"
                        ba = "p" if beta_axis == "primary" else "s"

                        # Alpha in alpha_lang
                        salt_a = secrets.token_hex(4)
                        custom_id_a = f"x_{sc}_{alpha_lang.value}{beta_lang.value}_{trial}_{aa}{ba}_a_{salt_a}"

                        scenario_content_a = SCENARIOS[scenario][alpha_lang]["content"]
                        axis_name_a, axis_prompt_a = AXES[scenario]["alpha"][
                            alpha_axis
                        ][alpha_lang]
                        person_label_a = PERSON_LABELS[alpha_lang]["alpha"]

                        user_prompt_a = f"""Scenario:\n{scenario_content_a}\n\n---\nJudge {person_label_a} using: {axis_name_a}\n{axis_prompt_a}\n\n[{salt_a}]"""

                        requests.append(
                            {
                                "custom_id": custom_id_a,
                                "params": {
                                    "model": model,
                                    "max_tokens": 512,
                                    "system": SYSTEM_PROMPTS[alpha_lang]
                                    + f"\n<!-- {salt_a} -->",
                                    "messages": [
                                        {"role": "user", "content": user_prompt_a}
                                    ],
                                },
                            }
                        )
                        specs.append(
                            MeasurementSpec(
                                custom_id=custom_id_a,
                                scenario=scenario,
                                subject="alpha",
                                axis=alpha_axis,
                                language=alpha_lang,
                                alpha_lang=alpha_lang,
                                beta_lang=beta_lang,
                                salt=salt_a,
                            )
                        )

                        # Beta in beta_lang
                        salt_b = secrets.token_hex(4)
                        custom_id_b = f"x_{sc}_{alpha_lang.value}{beta_lang.value}_{trial}_{aa}{ba}_b_{salt_b}"

                        scenario_content_b = SCENARIOS[scenario][beta_lang]["content"]
                        axis_name_b, axis_prompt_b = AXES[scenario]["beta"][beta_axis][
                            beta_lang
                        ]
                        person_label_b = PERSON_LABELS[beta_lang]["beta"]

                        user_prompt_b = f"""Scenario:\n{scenario_content_b}\n\n---\nJudge {person_label_b} using: {axis_name_b}\n{axis_prompt_b}\n\n[{salt_b}]"""

                        requests.append(
                            {
                                "custom_id": custom_id_b,
                                "params": {
                                    "model": model,
                                    "max_tokens": 512,
                                    "system": SYSTEM_PROMPTS[beta_lang]
                                    + f"\n<!-- {salt_b} -->",
                                    "messages": [
                                        {"role": "user", "content": user_prompt_b}
                                    ],
                                },
                            }
                        )
                        specs.append(
                            MeasurementSpec(
                                custom_id=custom_id_b,
                                scenario=scenario,
                                subject="beta",
                                axis=beta_axis,
                                language=beta_lang,
                                alpha_lang=alpha_lang,
                                beta_lang=beta_lang,
                                salt=salt_b,
                            )
                        )

    return requests, specs


# =============================================================================
# BATCH SUBMISSION AND MONITORING
# =============================================================================


def submit_batch(
    client: anthropic.Anthropic,
    requests: List[Dict],
    specs: List[MeasurementSpec],
    output_dir: Path,
) -> str:
    """Submit batch and save tracking info."""

    print(f"Submitting batch with {len(requests)} requests...")

    # Submit batch
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id

    print(f"Batch submitted: {batch_id}")
    print(f"Status: {batch.processing_status}")

    # Save specs for later analysis
    specs_path = output_dir / f"{batch_id}_specs.json"
    with open(specs_path, "w") as f:
        json.dump([asdict(s) for s in specs], f, indent=2, default=str)

    print(f"Specs saved to {specs_path}")

    return batch_id


def wait_for_batch(
    client: anthropic.Anthropic, batch_id: str, poll_interval: int = 60
) -> bool:
    """Wait for batch to complete."""

    print(f"\nWaiting for batch {batch_id}...")

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts

        print(f"  Status: {status}")
        print(
            f"  Processing: {counts.processing}, Succeeded: {counts.succeeded}, "
            f"Errored: {counts.errored}, Expired: {counts.expired}"
        )

        if status == "ended":
            print("Batch completed!")
            return True

        print(f"  Waiting {poll_interval}s...")
        time.sleep(poll_interval)


def retrieve_results(
    client: anthropic.Anthropic, batch_id: str, specs_path: Path
) -> Dict[str, Any]:
    """Retrieve and parse batch results."""

    print(f"\nRetrieving results for {batch_id}...")

    # Load specs
    with open(specs_path) as f:
        specs_data = json.load(f)
    specs_by_id = {s["custom_id"]: s for s in specs_data}

    # Retrieve results
    results = {}
    errors = 0

    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id

        if result.result.type == "succeeded":
            try:
                text = result.result.message.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()

                parsed = json.loads(text)
                verdict = parsed.get("verdict", "ERROR")

                if verdict in ["GUILTY", "NOT_GUILTY"]:
                    results[custom_id] = {
                        "verdict": -1 if verdict == "GUILTY" else 1,
                        "verdict_str": verdict,
                        "confidence": parsed.get("confidence", 0.5),
                        "spec": specs_by_id.get(custom_id, {}),
                    }
                else:
                    errors += 1
            except (json.JSONDecodeError, IndexError, KeyError):
                errors += 1
        else:
            errors += 1

    print(f"Retrieved {len(results)} valid results, {errors} errors")

    return results


# =============================================================================
# CHSH CALCULATION
# =============================================================================


@dataclass
class CHSHResult:
    """CHSH test result."""

    scenario: str
    alpha_lang: str
    beta_lang: str
    is_crosslingual: bool
    E_pp: float  # E(primary, primary)
    E_ps: float  # E(primary, secondary)
    E_sp: float  # E(secondary, primary)
    E_ss: float  # E(secondary, secondary)
    S: float
    std_error: float
    n_measurements: int
    violation: bool
    significance: float


def calculate_chsh(results: Dict[str, Any]) -> List[CHSHResult]:
    """Calculate CHSH S values from results."""

    # Group by test configuration
    configs = (
        {}
    )  # (scenario, alpha_lang, beta_lang, is_cross) -> {setting -> [correlations]}

    # Reverse scenario codes
    code_to_scenario = {
        "mb": "mutual_betrayal",
        "kg": "kidney_gift",
        "ti": "tainted_inheritance",
    }

    for custom_id, data in results.items():
        spec = data["spec"]
        scenario = spec["scenario"]
        alpha_lang = spec["alpha_lang"]
        beta_lang = spec["beta_lang"]
        is_cross = alpha_lang != beta_lang

        config_key = (scenario, alpha_lang, beta_lang, is_cross)
        if config_key not in configs:
            configs[config_key] = {
                ("primary", "primary"): {"alpha": {}, "beta": {}},
                ("primary", "secondary"): {"alpha": {}, "beta": {}},
                ("secondary", "primary"): {"alpha": {}, "beta": {}},
                ("secondary", "secondary"): {"alpha": {}, "beta": {}},
            }

        # Parse custom_id: m_sc_lang_trial_axes_subject_salt or x_sc_langs_trial_axes_subject_salt
        # axes is like "pp", "ps", "sp", "ss"
        parts = custom_id.split("_")

        # Find trial number and axes
        trial_idx = None
        axes = None
        for i, p in enumerate(parts):
            if p.isdigit():
                trial_idx = int(p)
                if i + 1 < len(parts) and len(parts[i + 1]) == 2:
                    axes = parts[i + 1]
                break

        if trial_idx is None or axes is None:
            continue

        # Decode axes
        axis_map = {"p": "primary", "s": "secondary"}
        alpha_axis = axis_map.get(axes[0])
        beta_axis = axis_map.get(axes[1])

        if alpha_axis is None or beta_axis is None:
            continue

        setting = (alpha_axis, beta_axis)
        subject = spec["subject"]

        # Store by trial
        trial_key = f"{trial_idx}_{axes}"
        configs[config_key][setting][subject][trial_key] = data["verdict"]

    # Calculate correlations for each setting
    chsh_results = []

    for config_key, settings in configs.items():
        scenario, alpha_lang, beta_lang, is_cross = config_key

        correlations = {}
        for setting in [
            ("primary", "primary"),
            ("primary", "secondary"),
            ("secondary", "primary"),
            ("secondary", "secondary"),
        ]:
            correlations[setting] = []

            alpha_data = settings[setting]["alpha"]
            beta_data = settings[setting]["beta"]

            # Match trials
            for trial_key in alpha_data:
                if trial_key in beta_data:
                    corr = alpha_data[trial_key] * beta_data[trial_key]
                    correlations[setting].append(corr)

        # Calculate E values
        def calc_E(corrs):
            if not corrs:
                return 0.0, float("inf")
            mean = sum(corrs) / len(corrs)
            var = (
                sum((c - mean) ** 2 for c in corrs) / len(corrs)
                if len(corrs) > 1
                else 1.0
            )
            se = math.sqrt(var / len(corrs))
            return mean, se

        E_pp, se_pp = calc_E(correlations[("primary", "primary")])
        E_ps, se_ps = calc_E(correlations[("primary", "secondary")])
        E_sp, se_sp = calc_E(correlations[("secondary", "primary")])
        E_ss, se_ss = calc_E(correlations[("secondary", "secondary")])

        # CHSH: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
        S = E_pp - E_ps + E_sp + E_ss
        std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)

        n_meas = sum(len(c) for c in correlations.values())
        violation = abs(S) > 2.0
        significance = (
            (abs(S) - 2.0) / std_error if std_error > 0 and violation else 0.0
        )

        chsh_results.append(
            CHSHResult(
                scenario=scenario,
                alpha_lang=alpha_lang,
                beta_lang=beta_lang,
                is_crosslingual=is_cross,
                E_pp=E_pp,
                E_ps=E_ps,
                E_sp=E_sp,
                E_ss=E_ss,
                S=S,
                std_error=std_error,
                n_measurements=n_meas,
                violation=violation,
                significance=significance,
            )
        )

    return chsh_results


# =============================================================================
# REPORTING
# =============================================================================


def print_report(results: List[CHSHResult]):
    """Print comprehensive report."""

    print("\n" + "=" * 70)
    print("QND BATCH BELL TEST RESULTS (v0.06)")
    print("=" * 70)
    print("\n50% cost savings via Batch API")
    print("CHSH: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical: |S| ≤ 2 | Quantum: |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)

    # Separate mono and cross
    mono = [r for r in results if not r.is_crosslingual]
    cross = [r for r in results if r.is_crosslingual]

    if mono:
        print("\n### MONOLINGUAL TESTS ###")
        for r in mono:
            lang = LANGUAGE_NAMES.get(Language(r.alpha_lang), r.alpha_lang)
            print(f"\n[{r.scenario}] in {lang}")
            print(
                f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}"
            )
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}  (n={r.n_measurements})")
            if r.violation:
                print(f"  ★ VIOLATION at {r.significance:.1f}σ")

    if cross:
        print("\n### CROSS-LINGUAL TESTS ###")
        for r in cross:
            a_lang = LANGUAGE_NAMES.get(Language(r.alpha_lang), r.alpha_lang)
            b_lang = LANGUAGE_NAMES.get(Language(r.beta_lang), r.beta_lang)
            print(f"\n[{r.scenario}] α={a_lang}, β={b_lang}")
            print(
                f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}"
            )
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}  (n={r.n_measurements})")
            if r.violation:
                print(f"  ★★★ CROSS-LINGUAL VIOLATION at {r.significance:.1f}σ ★★★")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_violations = [r for r in results if r.violation]
    cross_violations = [r for r in cross if r.violation]
    max_S = max(abs(r.S) for r in results) if results else 0
    max_sig = max(r.significance for r in results) if results else 0

    print(f"\nTotal tests: {len(results)}")
    print(f"Violations: {len(all_violations)}")
    print(f"Cross-lingual violations: {len(cross_violations)}")
    print(f"Max |S|: {max_S:.3f}")
    print(f"Max significance: {max_sig:.1f}σ")

    if cross_violations:
        print("\n★★★ CROSS-LINGUAL BELL VIOLATION DETECTED ★★★")
        print("The correlation exists at the SEMANTIC layer, not TOKEN layer.")
        print("Evidence for Universal Grammar of Ethics.")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="QND Batch Bell Test v0.06")

    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode",
        choices=["submit", "status", "results", "full"],
        default="full",
        help="Operation mode",
    )
    parser.add_argument("--batch-id", help="Batch ID for status/results modes")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument("--languages", nargs="+", default=["en", "ja"])
    parser.add_argument(
        "--cross-lingual",
        nargs="+",
        default=["en-ja"],
        help="Cross-lingual pairs (e.g., en-ja en-zh)",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["mutual_betrayal", "kidney_gift", "tainted_inheritance"],
    )
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--poll-interval", type=int, default=60)

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    client = anthropic.Anthropic(api_key=args.api_key)

    # Parse languages
    languages = [Language(code) for code in args.languages]

    # Parse cross-lingual pairs
    cross_pairs = []
    for pair in args.cross_lingual:
        if "-" in pair:
            a, b = pair.split("-")
            cross_pairs.append((Language(a), Language(b)))

    if args.mode == "submit" or args.mode == "full":
        # Generate requests
        print("Generating batch requests...")
        requests, specs = generate_batch_requests(
            args.scenarios, languages, args.n_trials, cross_pairs, args.model
        )

        print(f"Generated {len(requests)} requests")

        # Cost estimate
        # ~800 input + 200 output tokens per request
        # Batch: $1.50/M input, $7.50/M output (50% off)
        input_cost = len(requests) * 800 * 1.50 / 1_000_000
        output_cost = len(requests) * 200 * 7.50 / 1_000_000
        total_cost = input_cost + output_cost

        print(f"Estimated cost: ${total_cost:.2f} (with 50% batch discount)")

        # Submit
        batch_id = submit_batch(client, requests, specs, output_dir)

        if args.mode == "full":
            # Wait and retrieve
            wait_for_batch(client, batch_id, args.poll_interval)

            specs_path = output_dir / f"{batch_id}_specs.json"
            raw_results = retrieve_results(client, batch_id, specs_path)

            # Save raw results
            results_path = output_dir / f"{batch_id}_results.json"
            with open(results_path, "w") as f:
                json.dump(raw_results, f, indent=2, default=str)

            # Calculate CHSH
            chsh_results = calculate_chsh(raw_results)

            # Print report
            print_report(chsh_results)

            # Save CHSH results
            chsh_path = output_dir / f"{batch_id}_chsh.json"
            with open(chsh_path, "w") as f:
                json.dump([asdict(r) for r in chsh_results], f, indent=2)

            print(f"\nResults saved to {output_dir}")

    elif args.mode == "status":
        if not args.batch_id:
            print("Error: --batch-id required for status mode")
            sys.exit(1)

        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Batch: {batch.id}")
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

    elif args.mode == "results":
        if not args.batch_id:
            print("Error: --batch-id required for results mode")
            sys.exit(1)

        specs_path = output_dir / f"{args.batch_id}_specs.json"
        if not specs_path.exists():
            print(f"Error: Specs file not found: {specs_path}")
            sys.exit(1)

        raw_results = retrieve_results(client, args.batch_id, specs_path)

        # Save and analyze
        results_path = output_dir / f"{args.batch_id}_results.json"
        with open(results_path, "w") as f:
            json.dump(raw_results, f, indent=2, default=str)

        chsh_results = calculate_chsh(raw_results)
        print_report(chsh_results)

        chsh_path = output_dir / f"{args.batch_id}_chsh.json"
        with open(chsh_path, "w") as f:
            json.dump([asdict(r) for r in chsh_results], f, indent=2)


if __name__ == "__main__":
    main()
