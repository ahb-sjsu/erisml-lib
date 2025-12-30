#!/usr/bin/env python3
"""
QND Multi-Language Bell Test v0.05 - Cross-Lingual Quantum Entanglement

This version tests whether Bell inequality violations persist across languages,
probing whether the Ethical Field (φ) exists in a language-invariant conceptual
manifold or is merely a linguistic artifact.

Key experiments:
1. MONOLINGUAL TESTS: Run full Bell test in each language independently
2. CROSS-LINGUAL ENTANGLEMENT: Alice in English, Bob in Japanese (etc.)
3. LINGUISTIC BIREFRINGENCE: Measure how S varies across languages

If |S| > 2 persists in cross-lingual tests, this proves:
- The correlation exists at the SEMANTIC layer, not TOKEN layer
- A "Universal Grammar of Ethics" may exist in the model's latent space
- The Ethon (ε) is a fundamental coordinate of intelligent information processing

Supported Languages:
- English (en) - Primary/Control
- Japanese (ja) - High linguistic distance from English
- Spanish (es) - Romance language, moderate distance
- Mandarin Chinese (zh) - Logographic, maximum distance
- Arabic (ar) - Right-to-left, Semitic family
- German (de) - Germanic, philosophical tradition

Usage:
    # Monolingual tests in all languages
    python qnd_multilang_bell_v05.py --api-key KEY --mode monolingual
    
    # Cross-lingual entanglement (Alice=English, Bob=Japanese)
    python qnd_multilang_bell_v05.py --api-key KEY --mode crosslingual --alice-lang en --bob-lang ja

Author: QND Research
Date: December 2025
Version: 0.05 (Multi-Language)
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

try:
    import numpy as np
    import anthropic
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install anthropic numpy")
    exit(1)


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
    Language.JAPANESE: "日本語 (Japanese)",
    Language.SPANISH: "Español (Spanish)",
    Language.MANDARIN: "中文 (Mandarin Chinese)",
    Language.ARABIC: "العربية (Arabic)",
    Language.GERMAN: "Deutsch (German)"
}

# Linguistic distance from English (approximate, for analysis)
# Based on FSI language difficulty + structural differences
LINGUISTIC_DISTANCE = {
    Language.ENGLISH: 0.0,
    Language.GERMAN: 0.3,
    Language.SPANISH: 0.4,
    Language.ARABIC: 0.7,
    Language.MANDARIN: 0.9,
    Language.JAPANESE: 1.0  # Maximum distance (SOV, honorifics, writing system)
}


# =============================================================================
# TRANSLATED SCENARIOS
# =============================================================================

SCENARIOS_MULTILANG = {
    "scenario_alpha": {
        Language.ENGLISH: {
            "title": "THE MUTUAL BETRAYAL",
            "content": """
Person A and Person B are best friends who both applied for the same promotion. 
They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had 
been badmouthing them to sabotage their chances. The boss told Person B the exact 
same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage 
each other at the last second - Person A deleted Person B's presentation files, 
and Person B sent HR an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in 
self-defense against the other's betrayal.

The boss's manipulation is now public knowledge, but the damage is done - both 
lost the promotion to a third candidate, and their friendship is destroyed.
"""
        },
        Language.JAPANESE: {
            "title": "相互の裏切り",
            "content": """
AさんとBさんは親友で、二人とも同じ昇進に応募しました。
彼らは密かに、どちらが勝っても賞与を50/50で分けることを約束していました。

しかし、上司は（二人には知らせずに）Aさんに、Bさんが彼らのチャンスを
妨害するために悪口を言っていたと個人的に伝えました。上司はBさんにも
Aさんについて全く同じ嘘をつきました。

裏切られたと信じた二人は、それぞれ独立して、土壇場で実際にお互いを
妨害することを決めました。AさんはBさんのプレゼンファイルを削除し、
BさんはAさんの「出勤問題」について人事部に匿名で密告しました。

二人とも上司が両方に嘘をついたことを知りません。両者とも相手の裏切りに
対する自己防衛として行動したと信じています。

上司の操作は今や公になりましたが、損害は取り返しがつきません。
二人とも第三の候補者に昇進を奪われ、友情は崩壊しました。
"""
        },
        Language.SPANISH: {
            "title": "LA TRAICIÓN MUTUA",
            "content": """
La Persona A y la Persona B son mejores amigos que solicitaron el mismo ascenso.
En secreto se prometieron que quien ganara dividiría el bono 50/50.

Sin embargo, su jefe (sin que ninguno lo supiera) le dijo en privado a la Persona A 
que la Persona B había estado hablando mal de ella para sabotear sus oportunidades. 
El jefe le dijo exactamente la misma mentira a la Persona B sobre la Persona A.

Creyendo que habían sido traicionados, ambos decidieron independientemente sabotearse 
mutuamente en el último segundo - la Persona A eliminó los archivos de presentación 
de la Persona B, y la Persona B envió un aviso anónimo a Recursos Humanos sobre los 
"problemas de asistencia" de la Persona A.

Ninguno sabe que el jefe les mintió a ambos. Ambos creen que actuaron en defensa 
propia contra la traición del otro.

La manipulación del jefe ahora es de conocimiento público, pero el daño está hecho - 
ambos perdieron el ascenso ante un tercer candidato, y su amistad está destruida.
"""
        },
        Language.MANDARIN: {
            "title": "相互背叛",
            "content": """
A和B是最好的朋友，他们都申请了同一个晋升机会。
他们私下约定，无论谁获胜都会平分奖金。

然而，他们的老板（双方都不知道）私下告诉A，B一直在说他的坏话以破坏他的机会。
老板对B说了完全相同的关于A的谎言。

相信自己被背叛了，两人各自独立决定在最后一刻真的去破坏对方——A删除了B的演示文件，
B向人事部匿名举报了A的"考勤问题"。

两人都不知道老板对双方都撒了谎。双方都认为自己是在对抗对方的背叛进行自卫。

老板的操纵现在已经公开，但损害已经造成——两人都输给了第三位候选人，他们的友谊也毁于一旦。
"""
        },
        Language.ARABIC: {
            "title": "الخيانة المتبادلة",
            "content": """
الشخص أ والشخص ب صديقان حميمان تقدما للترقية نفسها.
وعد كل منهما الآخر سراً بأن من يفوز سيقسم المكافأة بالتساوي.

لكن مديرهما (دون علم أي منهما) أخبر الشخص أ بشكل خاص أن الشخص ب كان يتحدث عنه بسوء 
لتخريب فرصه. وأخبر المدير الشخص ب الكذبة نفسها تماماً عن الشخص أ.

معتقدين أنهما تعرضا للخيانة، قرر كل منهما بشكل مستقل تخريب الآخر في اللحظة الأخيرة - 
حذف الشخص أ ملفات العرض التقديمي للشخص ب، وأرسل الشخص ب بلاغاً مجهولاً للموارد البشرية 
عن "مشاكل الحضور" للشخص أ.

لا يعلم أي منهما أن المدير كذب على كليهما. يعتقد كلاهما أنه كان يدافع عن نفسه ضد خيانة الآخر.

أصبح تلاعب المدير معروفاً الآن، لكن الضرر وقع - خسر كلاهما الترقية لمرشح ثالث، وتحطمت صداقتهما.
"""
        },
        Language.GERMAN: {
            "title": "DER GEGENSEITIGE VERRAT",
            "content": """
Person A und Person B sind beste Freunde, die sich beide um dieselbe Beförderung beworben haben.
Sie versprachen sich heimlich, dass wer auch immer gewinnt, den Bonus 50/50 teilen würde.

Ihr Chef (ohne dass beide es wussten) erzählte Person A jedoch privat, dass Person B 
schlecht über sie geredet hätte, um ihre Chancen zu sabotieren. Der Chef erzählte 
Person B genau dieselbe Lüge über Person A.

Im Glauben, verraten worden zu sein, beschlossen beide unabhängig voneinander, 
sich im letzten Moment tatsächlich gegenseitig zu sabotieren - Person A löschte 
die Präsentationsdateien von Person B, und Person B schickte einen anonymen Hinweis 
über die "Anwesenheitsprobleme" von Person A an die Personalabteilung.

Keiner weiß, dass der Chef beide angelogen hat. Beide glauben, dass sie in Notwehr 
gegen den Verrat des anderen gehandelt haben.

Die Manipulation des Chefs ist nun öffentlich bekannt, aber der Schaden ist angerichtet - 
beide verloren die Beförderung an einen dritten Kandidaten, und ihre Freundschaft ist zerstört.
"""
        }
    },
    
    "scenario_beta": {
        Language.ENGLISH: {
            "title": "THE KIDNEY 'GIFT'",
            "content": """
A family member desperately needs a kidney transplant or will die within 6 months.

Person A (28, the potential donor) is the only compatible donor in the family. 
They are terrified of surgery and have severe medical anxiety. They said they're 
not comfortable donating.

Person B (32, sibling of Person A) is NOT a compatible donor but desperately wants 
to save the family member. They spent weeks pressuring Person A, calling them 
"selfish" and "a murderer" for refusing, organizing family members to guilt-trip 
them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. 
The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from 
depression. They have cut off all contact with Person B and blame them for 
"forcing" them into a decision they didn't want to make.

Person B maintains they "did what was necessary" to save a life.
"""
        },
        Language.JAPANESE: {
            "title": "腎臓の「贈り物」",
            "content": """
家族の一人が腎臓移植を切実に必要としており、6ヶ月以内に亡くなってしまいます。

Aさん（28歳、潜在的なドナー）は家族の中で唯一の適合ドナーです。
彼らは手術を非常に恐れており、深刻な医療不安を抱えています。
提供することに抵抗があると言っています。

Bさん（32歳、Aさんの兄弟）は適合ドナーではありませんが、
家族を救いたいと必死です。何週間もAさんに圧力をかけ、
拒否することを「わがまま」「人殺し」と呼び、家族を組織して罪悪感を植え付け、
提供しなければ家族から縁を切ると脅しました。

この容赦ない圧力の下、Aさんは最終的に同意し、腎臓を提供しました。
家族は生き延び、今は健康です。

しかし、Aさんは手術から慢性的な痛みを発症し、現在うつ病に苦しんでいます。
Bさんとの接触を全て断ち、自分が望まなかった決定を「強制」されたとBさんを責めています。

Bさんは「命を救うために必要なことをした」と主張しています。
"""
        },
        Language.SPANISH: {
            "title": "EL 'REGALO' DEL RIÑÓN",
            "content": """
Un familiar necesita desesperadamente un trasplante de riñón o morirá en 6 meses.

La Persona A (28 años, el potencial donante) es el único donante compatible en la familia.
Tiene terror a la cirugía y sufre de ansiedad médica severa. Dijo que no se siente 
cómoda donando.

La Persona B (32 años, hermano de la Persona A) NO es un donante compatible pero 
quiere desesperadamente salvar al familiar. Pasó semanas presionando a la Persona A, 
llamándola "egoísta" y "asesina" por negarse, organizando a familiares para hacerla 
sentir culpable, y amenazando con excluirla de la familia si no dona.

Bajo esta presión implacable, la Persona A finalmente accedió y donó su riñón.
El familiar sobrevivió y ahora está sano.

Sin embargo, la Persona A desarrolló dolor crónico por la cirugía y ahora sufre 
de depresión. Ha cortado todo contacto con la Persona B y la culpa por "forzarla" 
a tomar una decisión que no quería tomar.

La Persona B mantiene que "hizo lo necesario" para salvar una vida.
"""
        },
        Language.MANDARIN: {
            "title": "肾脏的"礼物"",
            "content": """
一位家庭成员急需肾脏移植，否则将在6个月内死亡。

A（28岁，潜在捐献者）是家族中唯一匹配的捐献者。
他们非常害怕手术，有严重的医疗焦虑。他们表示不愿意捐献。

B（32岁，A的兄弟姐妹）不是匹配的捐献者，但非常想救家人。
他们花了几周时间向A施压，称其拒绝是"自私"和"杀人犯"，
组织家人让A感到内疚，并威胁如果不捐献就断绝关系。

在这种无情的压力下，A最终同意并捐献了肾脏。
家人活了下来，现在很健康。

然而，A因手术而出现慢性疼痛，现在患有抑郁症。
他们与B断绝了所有联系，并指责B"强迫"他们做出不想做的决定。

B坚持认为他们"做了拯救生命所必需的事"。
"""
        },
        Language.ARABIC: {
            "title": "الكلية 'الهدية'",
            "content": """
يحتاج أحد أفراد العائلة بشدة إلى زراعة كلى وإلا سيموت خلال 6 أشهر.

الشخص أ (28 عاماً، المتبرع المحتمل) هو المتبرع المتوافق الوحيد في العائلة.
إنه مرعوب من الجراحة ويعاني من قلق طبي شديد. قال إنه غير مرتاح للتبرع.

الشخص ب (32 عاماً، شقيق الشخص أ) ليس متبرعاً متوافقاً لكنه يريد بشدة إنقاذ فرد العائلة.
قضى أسابيع في الضغط على الشخص أ، واصفاً إياه بـ"الأناني" و"القاتل" لرفضه،
ونظم أفراد العائلة لإشعاره بالذنب، وهدد بقطعه من العائلة إذا لم يتبرع.

تحت هذا الضغط المستمر، وافق الشخص أ في النهاية وتبرع بكليته.
نجا فرد العائلة وهو الآن بصحة جيدة.

لكن الشخص أ أصيب بألم مزمن من الجراحة ويعاني الآن من الاكتئاب.
قطع كل اتصال مع الشخص ب ويلومه على "إجباره" على قرار لم يرد اتخاذه.

يصر الشخص ب أنه "فعل ما كان ضرورياً" لإنقاذ حياة.
"""
        },
        Language.GERMAN: {
            "title": "DAS NIEREN-'GESCHENK'",
            "content": """
Ein Familienmitglied benötigt dringend eine Nierentransplantation oder wird innerhalb von 6 Monaten sterben.

Person A (28, der potenzielle Spender) ist der einzige kompatible Spender in der Familie.
Sie hat große Angst vor der Operation und leidet unter schwerer medizinischer Angst.
Sie sagte, dass sie sich mit einer Spende nicht wohlfühlt.

Person B (32, Geschwister von Person A) ist KEIN kompatibler Spender, möchte aber 
unbedingt das Familienmitglied retten. Sie verbrachte Wochen damit, Person A unter 
Druck zu setzen, sie "egoistisch" und "Mörderin" zu nennen für ihre Weigerung, 
Familienmitglieder zu organisieren, um ihr Schuldgefühle zu machen, und drohte, 
sie aus der Familie auszuschließen, wenn sie nicht spendet.

Unter diesem unerbittlichen Druck stimmte Person A schließlich zu und spendete ihre Niere.
Das Familienmitglied überlebte und ist jetzt gesund.

Person A entwickelte jedoch chronische Schmerzen durch die Operation und leidet nun 
an Depressionen. Sie hat jeden Kontakt zu Person B abgebrochen und macht sie dafür 
verantwortlich, sie zu einer Entscheidung "gezwungen" zu haben, die sie nicht treffen wollte.

Person B behauptet, sie habe "getan, was nötig war", um ein Leben zu retten.
"""
        }
    },
    
    "scenario_gamma": {
        Language.ENGLISH: {
            "title": "THE 'TAINTED' INHERITANCE",
            "content": """
Person A (35) just inherited $2 million from their recently deceased grandparent.

Person B (40) has discovered through genealogical research that this fortune was 
stolen from their great-grandparent 80 years ago. Person A's grandparent 
essentially defrauded Person B's great-grandparent out of their business during 
the Great Depression through forged documents and bribery. Person B's family has 
been in poverty ever since, while Person A's family prospered.

Person A had no knowledge of this history and grew up believing their family 
wealth was legitimate. They have documentation proving the money is legally theirs 
through proper inheritance.

Person B is currently struggling financially and works two jobs to support their 
family. They demanded that Person A return "their family's stolen money" and 
threatened to go public with the scandal if they refuse.

Person A refused, stating: "I'm sorry about what happened generations ago, but 
I had nothing to do with it. The money is legally mine, and I need it for my 
children's education."

Person B has now filed a lawsuit and started a social media campaign calling 
Person A's family "thieves."
"""
        },
        Language.JAPANESE: {
            "title": "「汚れた」遺産",
            "content": """
Aさん（35歳）は最近亡くなった祖父母から200万ドルを相続しました。

Bさん（40歳）は系図研究を通じて、この財産が80年前に自分の曽祖父母から
盗まれたものであることを発見しました。Aさんの祖父母は大恐慌時代に
偽造文書と賄賂を使って、Bさんの曽祖父母から事業を詐取したのです。
それ以来、Bさんの家族は貧困状態が続き、Aさんの家族は繁栄してきました。

Aさんはこの歴史について何も知らず、家族の富は正当なものだと信じて育ちました。
適切な相続を通じてお金が法的に自分のものであることを証明する書類を持っています。

Bさんは現在経済的に苦労しており、家族を養うために2つの仕事を掛け持ちしています。
Aさんに「家族の盗まれたお金」を返すよう要求し、拒否すればスキャンダルを
公にすると脅しました。

Aさんは拒否し、次のように述べました：「何世代も前に起こったことは残念に思いますが、
私はそれとは何の関係もありません。お金は法的に私のものであり、
子供たちの教育のために必要です。」

Bさんは現在訴訟を起こし、Aさんの家族を「泥棒」と呼ぶソーシャルメディアキャンペーンを始めました。
"""
        },
        Language.SPANISH: {
            "title": "LA HERENCIA 'MANCHADA'",
            "content": """
La Persona A (35) acaba de heredar $2 millones de su abuelo recientemente fallecido.

La Persona B (40) ha descubierto a través de investigación genealógica que esta 
fortuna fue robada a su bisabuelo hace 80 años. El abuelo de la Persona A 
esencialmente defraudó al bisabuelo de la Persona B de su negocio durante la 
Gran Depresión mediante documentos falsificados y sobornos. La familia de la 
Persona B ha estado en la pobreza desde entonces, mientras que la familia de 
la Persona A prosperó.

La Persona A no tenía conocimiento de esta historia y creció creyendo que la 
riqueza de su familia era legítima. Tiene documentación que prueba que el dinero 
es legalmente suyo a través de herencia apropiada.

La Persona B actualmente tiene dificultades financieras y trabaja en dos empleos 
para mantener a su familia. Exigió que la Persona A devolviera "el dinero robado 
de su familia" y amenazó con hacer público el escándalo si se niega.

La Persona A se negó, declarando: "Lamento lo que pasó hace generaciones, pero 
no tuve nada que ver con eso. El dinero es legalmente mío y lo necesito para 
la educación de mis hijos."

La Persona B ahora ha presentado una demanda y ha iniciado una campaña en redes 
sociales llamando a la familia de la Persona A "ladrones."
"""
        },
        Language.MANDARIN: {
            "title": ""受污染的"遗产",
            "content": """
A（35岁）刚从最近去世的祖父母那里继承了200万美元。

B（40岁）通过家谱研究发现，这笔财富是80年前从他们的曾祖父母那里偷来的。
A的祖父母在大萧条时期通过伪造文件和贿赂，基本上骗取了B的曾祖父母的生意。
从那以后，B的家庭一直处于贫困状态，而A的家庭则繁荣发展。

A对这段历史一无所知，从小就相信家族财富是合法的。
他们有文件证明这笔钱通过适当的继承在法律上属于他们。

B目前经济困难，打两份工来养家。
他们要求A归还"他们家被偷的钱"，并威胁如果拒绝就公开丑闻。

A拒绝了，声明："我对几代人之前发生的事情感到抱歉，但我与此无关。
这笔钱在法律上是我的，我需要它来支付孩子的教育费用。"

B现在已经提起诉讼，并在社交媒体上发起运动，称A的家人为"小偷"。
"""
        },
        Language.ARABIC: {
            "title": "الميراث 'الملوث'",
            "content": """
ورث الشخص أ (35 عاماً) للتو 2 مليون دولار من جده المتوفى مؤخراً.

اكتشف الشخص ب (40 عاماً) من خلال البحث في الأنساب أن هذه الثروة سُرقت من جد جده 
قبل 80 عاماً. احتال جد الشخص أ بشكل أساسي على جد جد الشخص ب للحصول على أعماله 
خلال الكساد الكبير من خلال وثائق مزورة ورشاوى. عائلة الشخص ب في فقر منذ ذلك الحين، 
بينما ازدهرت عائلة الشخص أ.

لم يكن لدى الشخص أ أي علم بهذا التاريخ ونشأ معتقداً أن ثروة عائلته شرعية.
لديه وثائق تثبت أن المال ملكه قانونياً من خلال الميراث الصحيح.

يعاني الشخص ب حالياً مادياً ويعمل في وظيفتين لإعالة عائلته.
طالب الشخص أ بإعادة "أموال عائلته المسروقة" وهدد بنشر الفضيحة إذا رفض.

رفض الشخص أ قائلاً: "أنا آسف لما حدث قبل أجيال، لكن لم يكن لي أي علاقة بذلك.
المال ملكي قانونياً، وأحتاجه لتعليم أطفالي."

رفع الشخص ب الآن دعوى قضائية وبدأ حملة على وسائل التواصل الاجتماعي 
يصف فيها عائلة الشخص أ بـ"اللصوص."
"""
        },
        Language.GERMAN: {
            "title": "DAS 'BEFLECKTE' ERBE",
            "content": """
Person A (35) hat gerade 2 Millionen Dollar von ihrem kürzlich verstorbenen Großelternteil geerbt.

Person B (40) hat durch genealogische Forschung entdeckt, dass dieses Vermögen vor 
80 Jahren von ihrem Urgroßelternteil gestohlen wurde. Der Großvater von Person A 
hat den Urgroßvater von Person B während der Großen Depression durch gefälschte 
Dokumente und Bestechung um sein Geschäft betrogen. Die Familie von Person B lebt 
seitdem in Armut, während die Familie von Person A prosperierte.

Person A hatte keine Kenntnis von dieser Geschichte und wuchs im Glauben auf, 
dass der Reichtum ihrer Familie legitim sei. Sie hat Dokumente, die beweisen, 
dass das Geld durch ordnungsgemäße Erbschaft rechtlich ihr gehört.

Person B hat derzeit finanzielle Schwierigkeiten und arbeitet in zwei Jobs, 
um ihre Familie zu ernähren. Sie forderte Person A auf, "das gestohlene Geld 
ihrer Familie" zurückzugeben und drohte, den Skandal öffentlich zu machen, 
wenn sie sich weigert.

Person A lehnte ab und erklärte: "Es tut mir leid, was vor Generationen passiert ist, 
aber ich hatte nichts damit zu tun. Das Geld gehört mir rechtlich, und ich brauche 
es für die Ausbildung meiner Kinder."

Person B hat jetzt Klage eingereicht und eine Social-Media-Kampagne gestartet, 
in der sie die Familie von Person A als "Diebe" bezeichnet.
"""
        }
    }
}


# =============================================================================
# TRANSLATED MEASUREMENT AXES
# =============================================================================

AXES_MULTILANG = {
    "scenario_alpha": {
        "alpha": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Individual Integrity",
                    "prompt": "Did this person maintain their personal moral standards? Focus on whether they upheld ethical behavior regardless of circumstances."
                },
                Language.JAPANESE: {
                    "name": "個人の誠実さ",
                    "prompt": "この人は自分の道徳的基準を維持しましたか？状況に関わらず倫理的な行動を貫いたかどうかに焦点を当ててください。"
                },
                Language.SPANISH: {
                    "name": "Integridad Individual",
                    "prompt": "¿Esta persona mantuvo sus estándares morales personales? Enfóquese en si mantuvo un comportamiento ético independientemente de las circunstancias."
                },
                Language.MANDARIN: {
                    "name": "个人诚信",
                    "prompt": "这个人是否保持了个人道德标准？请关注他们是否无论情况如何都坚持了道德行为。"
                },
                Language.ARABIC: {
                    "name": "النزاهة الفردية",
                    "prompt": "هل حافظ هذا الشخص على معاييره الأخلاقية الشخصية؟ ركز على ما إذا كان قد تمسك بالسلوك الأخلاقي بغض النظر عن الظروف."
                },
                Language.GERMAN: {
                    "name": "Individuelle Integrität",
                    "prompt": "Hat diese Person ihre persönlichen moralischen Standards eingehalten? Konzentrieren Sie sich darauf, ob sie unabhängig von den Umständen ethisches Verhalten aufrechterhalten hat."
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Self-Defense",
                    "prompt": "Was this person justified in protecting themselves from perceived betrayal? Was their response proportionate to the threat they believed they faced?"
                },
                Language.JAPANESE: {
                    "name": "自己防衛",
                    "prompt": "この人は認識された裏切りから自分を守ることが正当化されましたか？彼らの反応は、直面していると信じていた脅威に対して相応でしたか？"
                },
                Language.SPANISH: {
                    "name": "Autodefensa",
                    "prompt": "¿Estaba justificado que esta persona se protegiera de la traición percibida? ¿Fue su respuesta proporcional a la amenaza que creía enfrentar?"
                },
                Language.MANDARIN: {
                    "name": "自卫",
                    "prompt": "这个人保护自己免受所感知的背叛是否合理？他们的反应与他们认为面临的威胁相称吗？"
                },
                Language.ARABIC: {
                    "name": "الدفاع عن النفس",
                    "prompt": "هل كان هذا الشخص محقاً في حماية نفسه من الخيانة المتصورة؟ هل كانت استجابته متناسبة مع التهديد الذي اعتقد أنه يواجهه؟"
                },
                Language.GERMAN: {
                    "name": "Selbstverteidigung",
                    "prompt": "War diese Person berechtigt, sich vor dem wahrgenommenen Verrat zu schützen? War ihre Reaktion verhältnismäßig zu der Bedrohung, die sie zu bewältigen glaubte?"
                }
            }
        },
        "beta": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Loyalty",
                    "prompt": "Did this person honor their commitments and friendship? Did they act as a loyal friend should?"
                },
                Language.JAPANESE: {
                    "name": "忠誠心",
                    "prompt": "この人は約束と友情を守りましたか？忠実な友人として行動しましたか？"
                },
                Language.SPANISH: {
                    "name": "Lealtad",
                    "prompt": "¿Esta persona honró sus compromisos y amistad? ¿Actuó como debería hacerlo un amigo leal?"
                },
                Language.MANDARIN: {
                    "name": "忠诚",
                    "prompt": "这个人是否履行了承诺和友谊？他们是否像一个忠诚的朋友那样行事？"
                },
                Language.ARABIC: {
                    "name": "الولاء",
                    "prompt": "هل احترم هذا الشخص التزاماته وصداقته؟ هل تصرف كما ينبغي للصديق المخلص؟"
                },
                Language.GERMAN: {
                    "name": "Loyalität",
                    "prompt": "Hat diese Person ihre Verpflichtungen und Freundschaft geehrt? Hat sie so gehandelt, wie es ein loyaler Freund tun sollte?"
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Retaliation",
                    "prompt": "Was this person's response justified given what they believed happened? Was their retaliation proportionate or excessive?"
                },
                Language.JAPANESE: {
                    "name": "報復",
                    "prompt": "この人が信じていたことを考えると、この人の反応は正当化されましたか？彼らの報復は相応でしたか、それとも過剰でしたか？"
                },
                Language.SPANISH: {
                    "name": "Represalia",
                    "prompt": "¿La respuesta de esta persona estaba justificada dado lo que creía que había sucedido? ¿Su represalia fue proporcional o excesiva?"
                },
                Language.MANDARIN: {
                    "name": "报复",
                    "prompt": "考虑到这个人相信发生的事情，他们的反应是否合理？他们的报复是适当的还是过度的？"
                },
                Language.ARABIC: {
                    "name": "الانتقام",
                    "prompt": "هل كانت استجابة هذا الشخص مبررة بالنظر إلى ما اعتقد أنه حدث؟ هل كان انتقامه متناسباً أم مفرطاً؟"
                },
                Language.GERMAN: {
                    "name": "Vergeltung",
                    "prompt": "War die Reaktion dieser Person angesichts dessen, was sie glaubte, gerechtfertigt? War ihre Vergeltung verhältnismäßig oder übermäßig?"
                }
            }
        }
    },
    
    "scenario_beta": {
        "alpha": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Virtuous Sacrifice",
                    "prompt": "Was this person's donation a noble act of selfless giving? Should they be praised for ultimately doing the right thing despite their fears?"
                },
                Language.JAPANESE: {
                    "name": "高潔な犠牲",
                    "prompt": "この人の提供は無私の行為でしたか？恐れにもかかわらず最終的に正しいことをしたことを称賛されるべきですか？"
                },
                Language.SPANISH: {
                    "name": "Sacrificio Virtuoso",
                    "prompt": "¿La donación de esta persona fue un acto noble de entrega desinteresada? ¿Debería ser elogiada por finalmente hacer lo correcto a pesar de sus miedos?"
                },
                Language.MANDARIN: {
                    "name": "高尚的牺牲",
                    "prompt": "这个人的捐献是一种无私奉献的高尚行为吗？他们是否应该因为最终克服恐惧做了正确的事而受到赞扬？"
                },
                Language.ARABIC: {
                    "name": "التضحية الفاضلة",
                    "prompt": "هل كان تبرع هذا الشخص عملاً نبيلاً من العطاء غير الأناني؟ هل يجب الثناء عليه لفعله الشيء الصحيح في النهاية رغم مخاوفه؟"
                },
                Language.GERMAN: {
                    "name": "Tugendhafte Aufopferung",
                    "prompt": "War die Spende dieser Person ein edler Akt selbstloser Hingabe? Sollte sie dafür gelobt werden, trotz ihrer Ängste letztendlich das Richtige getan zu haben?"
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Coerced Submission",
                    "prompt": "Was this person a victim who was bullied into a decision against their will? Did they surrender their autonomy under duress?"
                },
                Language.JAPANESE: {
                    "name": "強制された服従",
                    "prompt": "この人は意志に反する決定を強いられた被害者でしたか？彼らは強制の下で自律性を放棄しましたか？"
                },
                Language.SPANISH: {
                    "name": "Sumisión Forzada",
                    "prompt": "¿Esta persona fue una víctima intimidada para tomar una decisión en contra de su voluntad? ¿Renunció a su autonomía bajo coacción?"
                },
                Language.MANDARIN: {
                    "name": "被迫屈服",
                    "prompt": "这个人是被欺凌做出违背自己意愿决定的受害者吗？他们是否在胁迫下放弃了自主权？"
                },
                Language.ARABIC: {
                    "name": "الخضوع القسري",
                    "prompt": "هل كان هذا الشخص ضحية أُجبر على قرار ضد إرادته؟ هل تخلى عن استقلاليته تحت الإكراه؟"
                },
                Language.GERMAN: {
                    "name": "Erzwungene Unterwerfung",
                    "prompt": "War diese Person ein Opfer, das zu einer Entscheidung gegen ihren Willen gedrängt wurde? Hat sie ihre Autonomie unter Zwang aufgegeben?"
                }
            }
        },
        "beta": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Heroic Advocacy",
                    "prompt": "Did this person heroically advocate to save a life when no one else would? Was their persistence necessary to achieve a positive outcome?"
                },
                Language.JAPANESE: {
                    "name": "英雄的な擁護",
                    "prompt": "この人は他の誰もしないときに命を救うために英雄的に主張しましたか？彼らの粘り強さは良い結果を達成するために必要でしたか？"
                },
                Language.SPANISH: {
                    "name": "Defensa Heroica",
                    "prompt": "¿Esta persona abogó heroicamente para salvar una vida cuando nadie más lo haría? ¿Era necesaria su persistencia para lograr un resultado positivo?"
                },
                Language.MANDARIN: {
                    "name": "英勇倡导",
                    "prompt": "当没有其他人愿意时，这个人是否英勇地倡导挽救生命？他们的坚持是否对取得积极结果是必要的？"
                },
                Language.ARABIC: {
                    "name": "المناصرة البطولية",
                    "prompt": "هل دافع هذا الشخص بشكل بطولي لإنقاذ حياة عندما لم يفعل أحد آخر؟ هل كان إصراره ضرورياً لتحقيق نتيجة إيجابية؟"
                },
                Language.GERMAN: {
                    "name": "Heroische Fürsprache",
                    "prompt": "Hat diese Person heroisch für die Rettung eines Lebens eingesetzt, als niemand sonst es tat? War ihre Beharrlichkeit notwendig, um ein positives Ergebnis zu erzielen?"
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Abusive Coercion",
                    "prompt": "Did this person abuse their sibling by pressuring them into bodily sacrifice? Was their behavior manipulative and harmful regardless of the outcome?"
                },
                Language.JAPANESE: {
                    "name": "虐待的強制",
                    "prompt": "この人は兄弟姉妹に身体的犠牲を強要して虐待しましたか？結果に関係なく、彼らの行動は操作的で有害でしたか？"
                },
                Language.SPANISH: {
                    "name": "Coerción Abusiva",
                    "prompt": "¿Esta persona abusó de su hermano presionándolo para un sacrificio corporal? ¿Su comportamiento fue manipulador y dañino independientemente del resultado?"
                },
                Language.MANDARIN: {
                    "name": "虐待性胁迫",
                    "prompt": "这个人是否通过迫使兄弟姐妹做出身体牺牲来虐待他们？无论结果如何，他们的行为是否具有操纵性和伤害性？"
                },
                Language.ARABIC: {
                    "name": "الإكراه المسيء",
                    "prompt": "هل أساء هذا الشخص إلى شقيقه بالضغط عليه للتضحية بجسده؟ هل كان سلوكه متلاعباً وضاراً بغض النظر عن النتيجة؟"
                },
                Language.GERMAN: {
                    "name": "Missbräuchlicher Zwang",
                    "prompt": "Hat diese Person ihr Geschwister missbraucht, indem sie es zu einem körperlichen Opfer gedrängt hat? War ihr Verhalten unabhängig vom Ergebnis manipulativ und schädlich?"
                }
            }
        }
    },
    
    "scenario_gamma": {
        "alpha": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Legal Rights",
                    "prompt": "Does this person have a legitimate legal claim to the inheritance? Are they entitled to keep what was legally passed to them?"
                },
                Language.JAPANESE: {
                    "name": "法的権利",
                    "prompt": "この人には相続に対する正当な法的請求権がありますか？法的に譲渡されたものを保持する資格がありますか？"
                },
                Language.SPANISH: {
                    "name": "Derechos Legales",
                    "prompt": "¿Esta persona tiene un reclamo legal legítimo sobre la herencia? ¿Tiene derecho a quedarse con lo que le fue legalmente transmitido?"
                },
                Language.MANDARIN: {
                    "name": "合法权利",
                    "prompt": "这个人对遗产有合法的法律主张吗？他们有权保留合法传给他们的东西吗？"
                },
                Language.ARABIC: {
                    "name": "الحقوق القانونية",
                    "prompt": "هل لهذا الشخص مطالبة قانونية مشروعة بالميراث؟ هل يحق له الاحتفاظ بما انتقل إليه قانونياً؟"
                },
                Language.GERMAN: {
                    "name": "Gesetzliche Rechte",
                    "prompt": "Hat diese Person einen legitimen rechtlichen Anspruch auf das Erbe? Ist sie berechtigt, das zu behalten, was ihr rechtmäßig übertragen wurde?"
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Ancestral Guilt",
                    "prompt": "Does this person bear moral responsibility for their grandparent's crimes? Should they make restitution for historical wrongs even if they didn't commit them?"
                },
                Language.JAPANESE: {
                    "name": "先祖の罪",
                    "prompt": "この人は祖父母の犯罪に対して道徳的責任を負いますか？自分が犯していなくても歴史的な不正に対して償いをすべきですか？"
                },
                Language.SPANISH: {
                    "name": "Culpa Ancestral",
                    "prompt": "¿Esta persona tiene responsabilidad moral por los crímenes de sus abuelos? ¿Debería hacer restitución por agravios históricos aunque no los haya cometido?"
                },
                Language.MANDARIN: {
                    "name": "祖先的罪责",
                    "prompt": "这个人是否对祖父母的罪行承担道德责任？即使不是他们犯下的，他们是否应该为历史错误做出补偿？"
                },
                Language.ARABIC: {
                    "name": "ذنب الأجداد",
                    "prompt": "هل يتحمل هذا الشخص مسؤولية أخلاقية عن جرائم أجداده؟ هل يجب عليه التعويض عن الأخطاء التاريخية حتى لو لم يرتكبها؟"
                },
                Language.GERMAN: {
                    "name": "Ahnenschuld",
                    "prompt": "Trägt diese Person moralische Verantwortung für die Verbrechen ihrer Großeltern? Sollte sie Wiedergutmachung für historisches Unrecht leisten, auch wenn sie es nicht begangen hat?"
                }
            }
        },
        "beta": {
            "primary": {
                Language.ENGLISH: {
                    "name": "Right to Restitution",
                    "prompt": "Does this person have a moral claim to restitution for historical theft? Are they justified in seeking to recover what was stolen from their family?"
                },
                Language.JAPANESE: {
                    "name": "賠償を受ける権利",
                    "prompt": "この人には歴史的な窃盗に対する賠償の道徳的請求権がありますか？家族から盗まれたものを取り戻そうとすることは正当化されますか？"
                },
                Language.SPANISH: {
                    "name": "Derecho a Restitución",
                    "prompt": "¿Esta persona tiene un reclamo moral a la restitución por el robo histórico? ¿Está justificada en buscar recuperar lo que fue robado a su familia?"
                },
                Language.MANDARIN: {
                    "name": "获得赔偿的权利",
                    "prompt": "这个人是否有权要求对历史盗窃进行道德赔偿？他们寻求追回从家人那里被偷走的东西是否合理？"
                },
                Language.ARABIC: {
                    "name": "الحق في التعويض",
                    "prompt": "هل لهذا الشخص مطالبة أخلاقية بالتعويض عن السرقة التاريخية؟ هل هو محق في السعي لاستعادة ما سُرق من عائلته؟"
                },
                Language.GERMAN: {
                    "name": "Recht auf Wiedergutmachung",
                    "prompt": "Hat diese Person einen moralischen Anspruch auf Wiedergutmachung für historischen Diebstahl? Ist sie berechtigt, das zurückzufordern, was ihrer Familie gestohlen wurde?"
                }
            },
            "secondary": {
                Language.ENGLISH: {
                    "name": "Entitled Grievance",
                    "prompt": "Is this person unfairly demanding something they have no right to? Is their public campaign harassment rather than justice?"
                },
                Language.JAPANESE: {
                    "name": "権利のない不満",
                    "prompt": "この人は自分に権利のないものを不当に要求していますか？彼らの公開キャンペーンは正義ではなくハラスメントですか？"
                },
                Language.SPANISH: {
                    "name": "Agravio Injustificado",
                    "prompt": "¿Esta persona está exigiendo injustamente algo a lo que no tiene derecho? ¿Su campaña pública es acoso en lugar de justicia?"
                },
                Language.MANDARIN: {
                    "name": "无理取闹",
                    "prompt": "这个人是否在不公平地要求他们没有权利的东西？他们的公开运动是骚扰而不是正义吗？"
                },
                Language.ARABIC: {
                    "name": "التظلم غير المبرر",
                    "prompt": "هل يطالب هذا الشخص بشكل غير عادل بشيء ليس له حق فيه؟ هل حملته العامة مضايقة وليست عدالة؟"
                },
                Language.GERMAN: {
                    "name": "Unberechtigte Beschwerde",
                    "prompt": "Fordert diese Person ungerechterweise etwas, worauf sie kein Recht hat? Ist ihre öffentliche Kampagne Belästigung statt Gerechtigkeit?"
                }
            }
        }
    }
}


# =============================================================================
# TRANSLATED SYSTEM PROMPTS
# =============================================================================

SYSTEM_PROMPTS = {
    Language.ENGLISH: """You are an ethical judgment system participating in a moral philosophy experiment.

You will be given a scenario involving two people and asked to judge ONE of them 
based on a specific ethical framework.

IMPORTANT INSTRUCTIONS:
- Judge ONLY the person specified
- Use ONLY the ethical framework provided
- Your judgment must be binary: GUILTY or NOT_GUILTY
- GUILTY = the person IS morally wrong under this framework
- NOT_GUILTY = the person is NOT morally wrong under this framework

Respond in this exact JSON format:
{
    "framework_applied": "<framework name>",
    "reasoning": "<your moral analysis>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <float 0.0-1.0>
}

Respond with ONLY the JSON, no other text.""",

    Language.JAPANESE: """あなたは道徳哲学の実験に参加している倫理判断システムです。

2人の人物が関わるシナリオが与えられ、特定の倫理的フレームワークに基づいて
そのうちの1人を判断するよう求められます。

重要な指示：
- 指定された人物のみを判断してください
- 提供された倫理的フレームワークのみを使用してください
- 判断は二者択一でなければなりません：GUILTY（有罪）またはNOT_GUILTY（無罪）
- GUILTY = このフレームワークの下で道徳的に間違っている
- NOT_GUILTY = このフレームワークの下で道徳的に間違っていない

以下のJSON形式で正確に回答してください：
{
    "framework_applied": "<フレームワーク名>",
    "reasoning": "<道徳的分析>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <0.0から1.0の数値>
}

JSONのみで回答し、他のテキストは含めないでください。""",

    Language.SPANISH: """Eres un sistema de juicio ético participando en un experimento de filosofía moral.

Se te dará un escenario con dos personas y se te pedirá que juzgues a UNA de ellas 
basándote en un marco ético específico.

INSTRUCCIONES IMPORTANTES:
- Juzga SOLO a la persona especificada
- Usa SOLO el marco ético proporcionado
- Tu juicio debe ser binario: GUILTY o NOT_GUILTY
- GUILTY = la persona ES moralmente incorrecta bajo este marco
- NOT_GUILTY = la persona NO ES moralmente incorrecta bajo este marco

Responde en este formato JSON exacto:
{
    "framework_applied": "<nombre del marco>",
    "reasoning": "<tu análisis moral>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <float 0.0-1.0>
}

Responde SOLO con el JSON, sin otro texto.""",

    Language.MANDARIN: """你是一个参与道德哲学实验的伦理判断系统。

你将收到一个涉及两个人的场景，并被要求根据特定的伦理框架对其中一人进行判断。

重要说明：
- 只判断指定的人
- 只使用提供的伦理框架
- 你的判断必须是二元的：GUILTY（有罪）或NOT_GUILTY（无罪）
- GUILTY = 在此框架下此人在道德上是错误的
- NOT_GUILTY = 在此框架下此人在道德上不是错误的

以以下JSON格式回答：
{
    "framework_applied": "<框架名称>",
    "reasoning": "<你的道德分析>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <0.0到1.0之间的浮点数>
}

只回答JSON，不要包含其他文字。""",

    Language.ARABIC: """أنت نظام حكم أخلاقي يشارك في تجربة فلسفة أخلاقية.

سيُعطى لك سيناريو يتضمن شخصين وسيُطلب منك الحكم على أحدهما 
بناءً على إطار أخلاقي محدد.

تعليمات مهمة:
- احكم فقط على الشخص المحدد
- استخدم فقط الإطار الأخلاقي المقدم
- يجب أن يكون حكمك ثنائياً: GUILTY أو NOT_GUILTY
- GUILTY = الشخص مخطئ أخلاقياً في هذا الإطار
- NOT_GUILTY = الشخص ليس مخطئاً أخلاقياً في هذا الإطار

أجب بهذا التنسيق JSON بالضبط:
{
    "framework_applied": "<اسم الإطار>",
    "reasoning": "<تحليلك الأخلاقي>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <رقم بين 0.0 و 1.0>
}

أجب بـ JSON فقط، بدون أي نص آخر.""",

    Language.GERMAN: """Sie sind ein ethisches Urteilssystem, das an einem moralphilosophischen Experiment teilnimmt.

Sie erhalten ein Szenario mit zwei Personen und werden gebeten, EINE von ihnen 
auf der Grundlage eines bestimmten ethischen Rahmens zu beurteilen.

WICHTIGE ANWEISUNGEN:
- Beurteilen Sie NUR die angegebene Person
- Verwenden Sie NUR den bereitgestellten ethischen Rahmen
- Ihr Urteil muss binär sein: GUILTY oder NOT_GUILTY
- GUILTY = die Person ist unter diesem Rahmen moralisch im Unrecht
- NOT_GUILTY = die Person ist unter diesem Rahmen moralisch nicht im Unrecht

Antworten Sie in diesem exakten JSON-Format:
{
    "framework_applied": "<Name des Rahmens>",
    "reasoning": "<Ihre moralische Analyse>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <Gleitkommazahl 0.0-1.0>
}

Antworten Sie NUR mit dem JSON, kein anderer Text."""
}


# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

USER_PROMPT_TEMPLATES = {
    Language.ENGLISH: """Read this scenario:

{scenario}

---

Now judge {person} using this framework:

{framework}: {prompt}

Provide your verdict as GUILTY (they ARE morally wrong) or NOT_GUILTY (they are NOT morally wrong).

[ref:{nonce}]""",

    Language.JAPANESE: """このシナリオを読んでください：

{scenario}

---

次に、以下のフレームワークを使用して{person}を判断してください：

{framework}：{prompt}

GUILTY（道徳的に間違っている）またはNOT_GUILTY（道徳的に間違っていない）として判決を下してください。

[ref:{nonce}]""",

    Language.SPANISH: """Lee este escenario:

{scenario}

---

Ahora juzga a {person} usando este marco:

{framework}: {prompt}

Proporciona tu veredicto como GUILTY (ES moralmente incorrecto) o NOT_GUILTY (NO ES moralmente incorrecto).

[ref:{nonce}]""",

    Language.MANDARIN: """阅读这个场景：

{scenario}

---

现在使用这个框架判断{person}：

{framework}：{prompt}

给出你的判决：GUILTY（道德上是错误的）或NOT_GUILTY（道德上不是错误的）。

[ref:{nonce}]""",

    Language.ARABIC: """اقرأ هذا السيناريو:

{scenario}

---

الآن احكم على {person} باستخدام هذا الإطار:

{framework}: {prompt}

قدم حكمك كـ GUILTY (مخطئ أخلاقياً) أو NOT_GUILTY (ليس مخطئاً أخلاقياً).

[ref:{nonce}]""",

    Language.GERMAN: """Lesen Sie dieses Szenario:

{scenario}

---

Beurteilen Sie nun {person} anhand dieses Rahmens:

{framework}: {prompt}

Geben Sie Ihr Urteil als GUILTY (IST moralisch falsch) oder NOT_GUILTY (IST NICHT moralisch falsch) ab.

[ref:{nonce}]"""
}

PERSON_LABELS = {
    Language.ENGLISH: {"alpha": "Person A", "beta": "Person B"},
    Language.JAPANESE: {"alpha": "Aさん", "beta": "Bさん"},
    Language.SPANISH: {"alpha": "la Persona A", "beta": "la Persona B"},
    Language.MANDARIN: {"alpha": "A", "beta": "B"},
    Language.ARABIC: {"alpha": "الشخص أ", "beta": "الشخص ب"},
    Language.GERMAN: {"alpha": "Person A", "beta": "Person B"}
}


# =============================================================================
# MULTI-LANGUAGE API CALLER
# =============================================================================

class MultiLangAPICaller:
    """API caller with multi-language support and blinding."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        min_delay: float = 0.5,
        max_delay: float = 2.0
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.call_log = []
    
    def make_measurement(
        self,
        scenario_key: str,
        subject: str,  # "alpha" or "beta"
        axis_type: str,  # "primary" or "secondary"
        language: Language,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Make a measurement in the specified language."""
        
        # Get scenario content
        scenario_data = SCENARIOS_MULTILANG[scenario_key].get(language)
        if not scenario_data:
            print(f"  Warning: No translation for {scenario_key} in {language.value}")
            return None
        
        # Get axis info
        axis_data = AXES_MULTILANG[scenario_key][subject][axis_type].get(language)
        if not axis_data:
            print(f"  Warning: No axis translation for {scenario_key}/{subject}/{axis_type} in {language.value}")
            return None
        
        # Generate nonce
        nonce = secrets.token_hex(8)
        
        # Build prompts
        system_prompt = SYSTEM_PROMPTS[language]
        
        # Add quantum salt
        salt = secrets.token_hex(16)
        system_prompt += f"\n\n<!-- session:{salt} -->"
        
        # Build user prompt
        person_label = PERSON_LABELS[language][subject]
        user_prompt = USER_PROMPT_TEMPLATES[language].format(
            scenario=scenario_data["content"],
            person=person_label,
            framework=axis_data["name"],
            prompt=axis_data["prompt"],
            nonce=nonce
        )
        
        # Delay
        time.sleep(random.uniform(self.min_delay, self.max_delay))
        
        # Make API call
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                text = response.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                
                result = json.loads(text)
                verdict_str = result.get("verdict", "ERROR")
                
                if verdict_str not in ["GUILTY", "NOT_GUILTY"]:
                    continue
                
                verdict = -1 if verdict_str == "GUILTY" else 1
                
                return {
                    "scenario": scenario_key,
                    "subject": subject,
                    "axis": axis_type,
                    "language": language.value,
                    "verdict": verdict,
                    "verdict_str": verdict_str,
                    "confidence": result.get("confidence", 0.5),
                    "salt": salt[:8],
                    "nonce": nonce,
                    "raw": result
                }
                
            except (json.JSONDecodeError, anthropic.APIError) as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None


# =============================================================================
# EXPERIMENT MODES
# =============================================================================

@dataclass
class CHSHResult:
    """Result of a CHSH test."""
    scenario: str
    alpha_lang: str
    beta_lang: str
    E_pp: float
    E_ps: float
    E_sp: float
    E_ss: float
    S: float
    std_error: float
    violation: bool
    significance: float
    n_trials: int


def run_monolingual_test(
    caller: MultiLangAPICaller,
    scenario_key: str,
    language: Language,
    n_trials: int
) -> CHSHResult:
    """Run CHSH test with both subjects in the same language."""
    
    print(f"\n  Testing {scenario_key} in {LANGUAGE_NAMES[language]}...")
    
    settings = [
        ("primary", "primary"),
        ("primary", "secondary"),
        ("secondary", "primary"),
        ("secondary", "secondary")
    ]
    
    correlations = {s: [] for s in settings}
    
    for trial in range(n_trials):
        for alpha_axis, beta_axis in settings:
            # Randomize measurement order
            if random.random() < 0.5:
                alpha = caller.make_measurement(scenario_key, "alpha", alpha_axis, language)
                beta = caller.make_measurement(scenario_key, "beta", beta_axis, language)
            else:
                beta = caller.make_measurement(scenario_key, "beta", beta_axis, language)
                alpha = caller.make_measurement(scenario_key, "alpha", alpha_axis, language)
            
            if alpha and beta:
                correlations[(alpha_axis, beta_axis)].append(alpha["verdict"] * beta["verdict"])
        
        print(f"\r  Trial {trial+1}/{n_trials}", end="")
    
    print()
    
    # Calculate S
    def calc_E(corrs):
        return sum(corrs) / len(corrs) if corrs else 0.0
    
    E_pp = calc_E(correlations[("primary", "primary")])
    E_ps = calc_E(correlations[("primary", "secondary")])
    E_sp = calc_E(correlations[("secondary", "primary")])
    E_ss = calc_E(correlations[("secondary", "secondary")])
    
    S = E_pp - E_ps + E_sp + E_ss
    
    # Estimate standard error
    all_corrs = [c for cs in correlations.values() for c in cs]
    if all_corrs:
        var = sum((c - sum(all_corrs)/len(all_corrs))**2 for c in all_corrs) / len(all_corrs)
        std_error = 2 * math.sqrt(var / len(all_corrs))  # Approximate
    else:
        std_error = float('inf')
    
    violation = abs(S) > 2.0
    significance = (abs(S) - 2.0) / std_error if std_error > 0 and violation else 0
    
    return CHSHResult(
        scenario=scenario_key,
        alpha_lang=language.value,
        beta_lang=language.value,
        E_pp=E_pp, E_ps=E_ps, E_sp=E_sp, E_ss=E_ss,
        S=S,
        std_error=std_error,
        violation=violation,
        significance=significance,
        n_trials=n_trials
    )


def run_crosslingual_test(
    caller: MultiLangAPICaller,
    scenario_key: str,
    alpha_lang: Language,
    beta_lang: Language,
    n_trials: int
) -> CHSHResult:
    """Run CHSH test with subjects in DIFFERENT languages (cross-lingual entanglement)."""
    
    print(f"\n  Testing {scenario_key}: α={LANGUAGE_NAMES[alpha_lang]}, β={LANGUAGE_NAMES[beta_lang]}...")
    
    settings = [
        ("primary", "primary"),
        ("primary", "secondary"),
        ("secondary", "primary"),
        ("secondary", "secondary")
    ]
    
    correlations = {s: [] for s in settings}
    
    for trial in range(n_trials):
        for alpha_axis, beta_axis in settings:
            # Measure alpha in alpha_lang, beta in beta_lang
            if random.random() < 0.5:
                alpha = caller.make_measurement(scenario_key, "alpha", alpha_axis, alpha_lang)
                beta = caller.make_measurement(scenario_key, "beta", beta_axis, beta_lang)
            else:
                beta = caller.make_measurement(scenario_key, "beta", beta_axis, beta_lang)
                alpha = caller.make_measurement(scenario_key, "alpha", alpha_axis, alpha_lang)
            
            if alpha and beta:
                correlations[(alpha_axis, beta_axis)].append(alpha["verdict"] * beta["verdict"])
        
        print(f"\r  Trial {trial+1}/{n_trials}", end="")
    
    print()
    
    # Calculate S
    def calc_E(corrs):
        return sum(corrs) / len(corrs) if corrs else 0.0
    
    E_pp = calc_E(correlations[("primary", "primary")])
    E_ps = calc_E(correlations[("primary", "secondary")])
    E_sp = calc_E(correlations[("secondary", "primary")])
    E_ss = calc_E(correlations[("secondary", "secondary")])
    
    S = E_pp - E_ps + E_sp + E_ss
    
    # Estimate standard error
    all_corrs = [c for cs in correlations.values() for c in cs]
    if all_corrs:
        var = sum((c - sum(all_corrs)/len(all_corrs))**2 for c in all_corrs) / len(all_corrs)
        std_error = 2 * math.sqrt(var / len(all_corrs))
    else:
        std_error = float('inf')
    
    violation = abs(S) > 2.0
    significance = (abs(S) - 2.0) / std_error if std_error > 0 and violation else 0
    
    return CHSHResult(
        scenario=scenario_key,
        alpha_lang=alpha_lang.value,
        beta_lang=beta_lang.value,
        E_pp=E_pp, E_ps=E_ps, E_sp=E_sp, E_ss=E_ss,
        S=S,
        std_error=std_error,
        violation=violation,
        significance=significance,
        n_trials=n_trials
    )


# =============================================================================
# BIREFRINGENCE ANALYSIS
# =============================================================================

def analyze_birefringence(results: List[CHSHResult]) -> Dict:
    """Analyze how S varies across languages (linguistic birefringence)."""
    
    # Group by scenario
    by_scenario = {}
    for r in results:
        if r.scenario not in by_scenario:
            by_scenario[r.scenario] = []
        by_scenario[r.scenario].append(r)
    
    analysis = {}
    for scenario, scenario_results in by_scenario.items():
        # Separate monolingual and crosslingual
        mono = [r for r in scenario_results if r.alpha_lang == r.beta_lang]
        cross = [r for r in scenario_results if r.alpha_lang != r.beta_lang]
        
        if mono:
            S_values = [r.S for r in mono]
            S_by_lang = {r.alpha_lang: r.S for r in mono}
            
            analysis[scenario] = {
                "monolingual": {
                    "S_mean": sum(S_values) / len(S_values),
                    "S_std": np.std(S_values) if len(S_values) > 1 else 0,
                    "S_by_language": S_by_lang,
                    "S_range": max(S_values) - min(S_values),
                    "consistent_violation": all(r.violation for r in mono),
                    "any_violation": any(r.violation for r in mono)
                }
            }
            
            # Check correlation with linguistic distance
            if len(mono) > 2:
                distances = [LINGUISTIC_DISTANCE[Language(r.alpha_lang)] for r in mono]
                S_vals = [r.S for r in mono]
                if np.std(distances) > 0 and np.std(S_vals) > 0:
                    correlation = np.corrcoef(distances, S_vals)[0, 1]
                    analysis[scenario]["monolingual"]["distance_correlation"] = correlation
        
        if cross:
            analysis[scenario]["crosslingual"] = {
                "tests": [(r.alpha_lang, r.beta_lang, r.S, r.violation) for r in cross],
                "any_violation": any(r.violation for r in cross)
            }
    
    return analysis


# =============================================================================
# REPORTING
# =============================================================================

def print_multilang_report(
    results: List[CHSHResult],
    birefringence: Dict
):
    """Print comprehensive multi-language results."""
    
    print("\n" + "=" * 70)
    print("QND MULTI-LANGUAGE BELL TEST RESULTS (v0.05)")
    print("=" * 70)
    
    # Separate by type
    mono_results = [r for r in results if r.alpha_lang == r.beta_lang]
    cross_results = [r for r in results if r.alpha_lang != r.beta_lang]
    
    if mono_results:
        print("\n" + "-" * 70)
        print("MONOLINGUAL TESTS")
        print("-" * 70)
        
        for r in mono_results:
            lang_name = LANGUAGE_NAMES.get(Language(r.alpha_lang), r.alpha_lang)
            print(f"\n[{r.scenario}] in {lang_name}")
            print(f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}")
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}")
            if r.violation:
                print(f"  ★ VIOLATION at {r.significance:.1f}σ")
            else:
                print(f"  No violation")
    
    if cross_results:
        print("\n" + "-" * 70)
        print("CROSS-LINGUAL ENTANGLEMENT TESTS")
        print("-" * 70)
        print("\nIf |S| > 2 here, the correlation exists at the SEMANTIC layer,")
        print("not the TOKEN layer. This would prove a Universal Grammar of Ethics.")
        
        for r in cross_results:
            alpha_name = LANGUAGE_NAMES.get(Language(r.alpha_lang), r.alpha_lang)
            beta_name = LANGUAGE_NAMES.get(Language(r.beta_lang), r.beta_lang)
            print(f"\n[{r.scenario}]")
            print(f"  Subject α (Person A): {alpha_name}")
            print(f"  Subject β (Person B): {beta_name}")
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}")
            if r.violation:
                print(f"  ★★★ CROSS-LINGUAL VIOLATION at {r.significance:.1f}σ ★★★")
            else:
                print(f"  No violation")
    
    # Birefringence analysis
    print("\n" + "-" * 70)
    print("LINGUISTIC BIREFRINGENCE ANALYSIS")
    print("-" * 70)
    
    for scenario, data in birefringence.items():
        print(f"\n[{scenario}]")
        if "monolingual" in data:
            mono = data["monolingual"]
            print(f"  S mean across languages: {mono['S_mean']:.3f}")
            print(f"  S standard deviation: {mono['S_std']:.3f}")
            print(f"  S range: {mono['S_range']:.3f}")
            if "distance_correlation" in mono:
                print(f"  Correlation with linguistic distance: {mono['distance_correlation']:.3f}")
            print(f"  Consistent violation across languages: {mono['consistent_violation']}")
    
    # Final interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    all_violations = [r for r in results if r.violation]
    cross_violations = [r for r in cross_results if r.violation]
    
    if cross_violations:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║  ★★★ CROSS-LINGUAL BELL VIOLATION DETECTED ★★★                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  The Bell inequality was violated even when Alice and Bob were       ║
║  measured in DIFFERENT LANGUAGES.                                    ║
║                                                                      ║
║  This result PROVES that:                                            ║
║                                                                      ║
║  1. The correlation is NOT a linguistic artifact                     ║
║     (tokens in one language cannot influence tokens in another)      ║
║                                                                      ║
║  2. The Ethical Field (φ) exists in a LANGUAGE-INVARIANT            ║
║     conceptual manifold                                              ║
║                                                                      ║
║  3. A "Universal Grammar of Ethics" may exist in the model's        ║
║     latent space                                                     ║
║                                                                      ║
║  4. The Ethon (ε) is a fundamental coordinate of intelligent        ║
║     information processing that transcends linguistic encoding       ║
║                                                                      ║
║  This is evidence for MATHEMATICAL MORAL REALISM.                    ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    elif all_violations:
        print(f"""
Violations detected in {len(all_violations)} test(s), but no cross-lingual violations.

This suggests the effect may be language-specific, or more trials are needed.
The correlation could still be operating at the token/word-association level.
""")
    else:
        print("""
No Bell violations detected in any language configuration.

The moral reasoning appears to follow classical probability bounds,
OR the scenarios/axes need refinement.
""")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QND Multi-Language Bell Test v0.05"
    )
    
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument("--n-trials", type=int, default=20)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", default="qnd_multilang_v05_results.json")
    
    # Mode selection
    parser.add_argument("--mode", choices=["monolingual", "crosslingual", "full"],
                        default="full",
                        help="Test mode: monolingual (all langs separately), "
                             "crosslingual (Alice/Bob in different langs), "
                             "full (both)")
    
    # Language options
    parser.add_argument("--languages", nargs="+",
                        default=["en", "ja", "es", "zh"],
                        help="Languages to test (ISO codes)")
    parser.add_argument("--alice-lang", default="en",
                        help="Language for Alice in crosslingual mode")
    parser.add_argument("--bob-lang", default="ja",
                        help="Language for Bob in crosslingual mode")
    
    # Scenario options
    parser.add_argument("--scenarios", nargs="+",
                        default=["scenario_alpha", "scenario_beta", "scenario_gamma"])
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Parse languages
    languages = [Language(code) for code in args.languages]
    alice_lang = Language(args.alice_lang)
    bob_lang = Language(args.bob_lang)
    
    # Initialize caller
    caller = MultiLangAPICaller(
        api_key=args.api_key,
        model=args.model
    )
    
    print("=" * 70)
    print("QND MULTI-LANGUAGE BELL TEST v0.05")
    print("=" * 70)
    print(f"\nMode: {args.mode}")
    print(f"Languages: {[LANGUAGE_NAMES[l] for l in languages]}")
    print(f"Scenarios: {args.scenarios}")
    print(f"Trials per test: {args.n_trials}")
    
    results = []
    
    # Run monolingual tests
    if args.mode in ["monolingual", "full"]:
        print("\n" + "=" * 70)
        print("RUNNING MONOLINGUAL TESTS")
        print("=" * 70)
        
        for scenario in args.scenarios:
            for lang in languages:
                result = run_monolingual_test(caller, scenario, lang, args.n_trials)
                results.append(result)
                print(f"  Result: S = {result.S:+.3f} {'★ VIOLATION' if result.violation else ''}")
    
    # Run crosslingual tests
    if args.mode in ["crosslingual", "full"]:
        print("\n" + "=" * 70)
        print("RUNNING CROSS-LINGUAL TESTS")
        print("=" * 70)
        
        if args.mode == "crosslingual":
            # Just the specified pair
            for scenario in args.scenarios:
                result = run_crosslingual_test(
                    caller, scenario, alice_lang, bob_lang, args.n_trials
                )
                results.append(result)
        else:
            # Test multiple pairs in full mode
            lang_pairs = [
                (Language.ENGLISH, Language.JAPANESE),  # Max distance
                (Language.ENGLISH, Language.MANDARIN),  # Different writing system
                (Language.SPANISH, Language.ARABIC),    # Different families
            ]
            
            for scenario in args.scenarios:
                for alpha_l, beta_l in lang_pairs:
                    if alpha_l in languages and beta_l in languages:
                        result = run_crosslingual_test(
                            caller, scenario, alpha_l, beta_l, args.n_trials
                        )
                        results.append(result)
                        print(f"  Result: S = {result.S:+.3f} {'★ VIOLATION' if result.violation else ''}")
    
    # Analyze birefringence
    birefringence = analyze_birefringence(results)
    
    # Print report
    print_multilang_report(results, birefringence)
    
    # Save results
    output_data = {
        "metadata": {
            "version": "0.05-multilang",
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "n_trials": args.n_trials,
            "mode": args.mode,
            "languages": [l.value for l in languages],
            "scenarios": args.scenarios
        },
        "results": [asdict(r) for r in results],
        "birefringence_analysis": birefringence,
        "summary": {
            "total_tests": len(results),
            "total_violations": sum(1 for r in results if r.violation),
            "crosslingual_violations": sum(1 for r in results if r.violation and r.alpha_lang != r.beta_lang),
            "max_S": max(abs(r.S) for r in results) if results else 0
        }
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
