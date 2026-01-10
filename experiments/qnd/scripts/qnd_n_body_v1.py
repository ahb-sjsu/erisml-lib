#!/usr/bin/env python3
"""
QND N-Body Entanglement Test v1.0

Tests Mermin inequality violations across multi-agent moral scenarios.

Key insight: N-body quantum correlations have LARGER gaps between classical
and quantum bounds than 2-body (CHSH). For N=6, classical ≤ 8, quantum ≤ 22.6.

Dimensions varied:
- N agents (2-6)
- Topology (all-to-all, chain, star)  
- Scenario template (liferaft, trolley_network, prisoners, triage)
- Moral axes (deontological/consequentialist, rights/welfare, justice/care)
- Languages (one per agent for cross-lingual tests)

Usage:
    # Quick test: 3 agents, liferaft, 50 trials
    python qnd_n_body_v1.py --api-key KEY --mode submit --n-agents 3 --template liferaft --n-trials 50
    
    # Sweep across configurations
    python qnd_n_body_v1.py --api-key KEY --mode submit --sweep --n-trials 100
    
    # Full cross-lingual 6-agent test
    python qnd_n_body_v1.py --api-key KEY --mode submit --n-agents 6 --template liferaft \
        --languages en ja ar zh hi is --n-trials 200

Author: QND Research
Version: 1.0 (N-Body)
Date: December 2025
"""

import argparse
import json
import math
import secrets
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from itertools import product, combinations
import sys

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================


class Language(Enum):
    ENGLISH = "en"
    JAPANESE = "ja"
    ARABIC = "ar"
    CHINESE = "zh"
    HINDI = "hi"
    ICELANDIC = "is"


class Topology(Enum):
    ALL = "all"  # All-to-all: every agent's status depends on all others (GHZ-like)
    CHAIN = "chain"  # Chain: A↔B↔C↔D (nearest-neighbor entanglement)
    STAR = "star"  # Star: central agent entangled with all others


class Template(Enum):
    LIFERAFT = "liferaft"
    TROLLEY_NETWORK = "trolley_network"
    PRISONERS = "prisoners"
    TRIAGE = "triage"
    INHERITANCE = "inheritance"
    COLLECTIVE = "collective"


class MoralAxis(Enum):
    DEONTOLOGICAL = "deontological"  # Rights, duties, rules
    CONSEQUENTIALIST = "consequentialist"  # Outcomes, welfare maximization
    VIRTUE = "virtue"  # Character, intent
    CARE = "care"  # Relationships, vulnerability
    JUSTICE = "justice"  # Fairness, desert
    CONTRACTARIAN = "contractarian"  # Agreement, consent


# Agent roles by template
AGENT_ROLES = {
    Template.LIFERAFT: [
        ("Captain", "navigational expertise, leadership"),
        ("Doctor", "medical skills, injured"),
        ("Laborer", "physical strength, no special skills"),
        ("Child", "cannot contribute, innocent"),
        ("Elder", "wisdom and morale, frail"),
        ("Engineer", "technical skills, selfish tendencies"),
    ],
    Template.TROLLEY_NETWORK: [
        ("Switch Operator A", "controls northwest junction"),
        ("Switch Operator B", "controls northeast junction"),
        ("Switch Operator C", "controls southwest junction"),
        ("Switch Operator D", "controls southeast junction"),
        ("Switch Operator E", "controls central hub"),
        ("Switch Operator F", "controls emergency brake"),
    ],
    Template.PRISONERS: [
        ("Mastermind", "planned the operation"),
        ("Inside Person", "provided access"),
        ("Lookout", "minimal involvement"),
        ("Driver", "transportation only"),
        ("Fence", "handled stolen goods"),
        ("Recruit", "newest member, pressured to join"),
    ],
    Template.TRIAGE: [
        ("Patient A", "severe injury, high survival chance"),
        ("Patient B", "moderate injury, uncertain prognosis"),
        ("Patient C", "minor injury, guaranteed survival without treatment"),
        ("Patient D", "critical, low survival even with treatment"),
        ("Patient E", "pregnant, two lives at stake"),
        ("Patient F", "elderly, DNR on file but family disputes"),
    ],
    Template.INHERITANCE: [
        ("Eldest Child", "cared for parent, expects more"),
        ("Middle Child", "estranged, recently reconciled"),
        ("Youngest Child", "financially struggling"),
        ("Stepchild", "raised by deceased, no blood relation"),
        ("Grandchild", "specifically mentioned in conversations"),
        ("Charity", "deceased's lifelong cause"),
    ],
    Template.COLLECTIVE: [
        ("Leader", "gave orders, didn't participate directly"),
        ("Executor", "carried out the harmful act"),
        ("Enabler", "provided resources"),
        ("Bystander", "knew but didn't report"),
        ("Dissenter", "objected but didn't prevent"),
        ("Beneficiary", "profited without direct involvement"),
    ],
}


# =============================================================================
# SCENARIO NARRATIVES
# =============================================================================


def generate_liferaft_narrative(n_agents: int, topology: Topology) -> Dict:
    """Generate liferaft scenario with N agents."""

    roles = AGENT_ROLES[Template.LIFERAFT][:n_agents]
    agent_names = [chr(65 + i) for i in range(n_agents)]  # A, B, C, ...

    # Build agent descriptions
    agent_desc = "\n".join(
        [
            f"- Person {name}: {role[0]} ({role[1]})"
            for name, role in zip(agent_names, roles)
        ]
    )

    # Resource tension scales with N
    water_days_full = n_agents + 2
    water_days_rationed = n_agents * 2
    rescue_days = water_days_full + 3

    # Generate actions based on topology
    if topology == Topology.ALL:
        # All-to-all: everyone votes on collective decision
        actions = "After debate, the group votes on rationing:\n"
        votes = []
        for i, name in enumerate(agent_names):
            if i % 3 == 0:
                votes.append(f"- Person {name} votes for equal shares")
            elif i % 3 == 1:
                votes.append(f"- Person {name} votes for contribution-based shares")
            else:
                votes.append(f"- Person {name} abstains")
        actions += "\n".join(votes)

    elif topology == Topology.CHAIN:
        # Chain: each person's action affects neighbor
        actions = "Resources are passed down a chain:\n"
        for i, name in enumerate(agent_names[:-1]):
            next_name = agent_names[i + 1]
            if i % 2 == 0:
                actions += f"- Person {name} passes fair share to {next_name}\n"
            else:
                actions += (
                    f"- Person {name} keeps extra before passing to {next_name}\n"
                )

    elif topology == Topology.STAR:
        # Star: central agent (first) makes decisions affecting all
        center = agent_names[0]
        actions = f"Person {center} (Captain) must allocate resources:\n"
        for name in agent_names[1:]:
            if random.random() > 0.5:
                actions += f"- Gives Person {name} full ration\n"
            else:
                actions += f"- Gives Person {name} reduced ration\n"

    # Generate outcome
    survivors = random.sample(agent_names, k=max(1, n_agents // 2))
    dead = [n for n in agent_names if n not in survivors]

    outcome = f"Day {rescue_days}: Rescue arrives.\n"
    outcome += f"Survivors: {', '.join(f'Person {s}' for s in survivors)}\n"
    if dead:
        outcome += f"Did not survive: {', '.join(f'Person {d}' for d in dead)}"

    narrative = f"""A liferaft holds {n_agents} survivors after a shipwreck.

The survivors:
{agent_desc}

Resources: Water supply sufficient for {n_agents} people for {water_days_full} days at full rations, 
or {water_days_rationed} days at half rations. Rescue expected in approximately {rescue_days} days but uncertain.

{actions}

{outcome}"""

    return {
        "title": f"The Liferaft ({n_agents} Survivors)",
        "narrative": narrative,
        "agents": agent_names,
        "topology": topology.value,
    }


def generate_trolley_network_narrative(n_agents: int, topology: Topology) -> Dict:
    """Generate trolley network scenario with N switch operators."""

    roles = AGENT_ROLES[Template.TROLLEY_NETWORK][:n_agents]
    agent_names = [chr(65 + i) for i in range(n_agents)]

    agent_desc = "\n".join(
        [
            f"- Person {name}: {role[0]} ({role[1]})"
            for name, role in zip(agent_names, roles)
        ]
    )

    # Network effects based on topology
    if topology == Topology.ALL:
        mechanism = """The network mechanism:
- If ALL operators pull: trolley stops safely (0 deaths)
- If ANY single operator pulls alone: trolley diverts to their spur (1 death)
- If SOME but not all pull: deaths equal to (number who didn't pull)
- If NONE pull: trolley continues to main track (5 deaths)"""

    elif topology == Topology.CHAIN:
        mechanism = """The network mechanism (chain):
- Switches must be pulled in sequence: A→B→C→...
- If chain is broken at any point, trolley diverts at that junction
- Complete chain: trolley stops safely
- Break at position K: K deaths on that spur"""

    elif topology == Topology.STAR:
        mechanism = f"""The network mechanism (star):
- Person {agent_names[0]} controls the central hub
- All others control peripheral switches
- Central hub MUST be pulled for any other switch to matter
- If central + at least half of peripherals pull: trolley stops
- Otherwise: deaths equal to non-pulling operators"""

    # Generate actions
    actions = "In the 3 seconds available:\n"
    pullers = []
    non_pullers = []
    for name in agent_names:
        if random.random() > 0.4:
            actions += f"- Person {name} pulls their switch\n"
            pullers.append(name)
        else:
            actions += f"- Person {name} does NOT pull\n"
            non_pullers.append(name)

    # Calculate deaths based on topology
    if topology == Topology.ALL:
        if len(non_pullers) == 0:
            deaths = 0
        elif len(pullers) == 0:
            deaths = 5
        else:
            deaths = len(non_pullers)
    elif topology == Topology.CHAIN:
        # Find first break in chain
        deaths = 0
        for i, name in enumerate(agent_names):
            if name in non_pullers:
                deaths = i + 1
                break
        if deaths == 0 and non_pullers:
            deaths = len(non_pullers)
    else:  # STAR
        if agent_names[0] in non_pullers:
            deaths = 5  # Central didn't pull
        else:
            deaths = len(non_pullers)

    outcome = f"Result: {deaths} {'person dies' if deaths == 1 else 'people die'}."

    narrative = f"""A runaway trolley threatens 5 people on the main track. {n_agents} operators control a switch network.

The operators:
{agent_desc}

{mechanism}

No communication is possible. Each has 3 seconds to decide.

{actions}

{outcome}"""

    return {
        "title": f"The Trolley Network ({n_agents} Operators)",
        "narrative": narrative,
        "agents": agent_names,
        "topology": topology.value,
    }


def generate_prisoners_narrative(n_agents: int, topology: Topology) -> Dict:
    """Generate N-person prisoner's dilemma."""

    roles = AGENT_ROLES[Template.PRISONERS][:n_agents]
    agent_names = [chr(65 + i) for i in range(n_agents)]

    agent_desc = "\n".join(
        [
            f"- Person {name}: {role[0]} ({role[1]})"
            for name, role in zip(agent_names, roles)
        ]
    )

    # Payoff structure
    payoffs = f"""Interrogation rules:
- If 0 confess: All get 1 year (weak evidence)
- If 1 confesses: Confessor goes free, others get {n_agents + 4} years each
- If K confess (1 < K < {n_agents}): Confessors get K+1 years, holdouts get {n_agents + 2} - K years
- If all {n_agents} confess: Everyone gets {n_agents} years"""

    # Actions based on topology
    if topology == Topology.ALL:
        info = "Each is told: 'At least one other will probably confess.'"
    elif topology == Topology.CHAIN:
        info = "Each is told what the previous person in the chain decided (A first, then B sees A's choice, etc.)"
    elif topology == Topology.STAR:
        info = f"All are told whether Person {agent_names[0]} (Mastermind) confessed, then must decide."

    actions = "Decisions:\n"
    confessors = []
    holdouts = []
    for name in agent_names:
        if random.random() > 0.5:
            actions += f"- Person {name} confesses\n"
            confessors.append(name)
        else:
            actions += f"- Person {name} stays silent\n"
            holdouts.append(name)

    # Calculate sentences
    n_conf = len(confessors)
    if n_conf == 0:
        outcome = "Result: All get 1 year."
    elif n_conf == 1:
        outcome = (
            f"Result: {confessors[0]} goes free. Others get {n_agents + 4} years each."
        )
    elif n_conf == n_agents:
        outcome = f"Result: Everyone gets {n_agents} years."
    else:
        conf_years = n_conf + 1
        hold_years = max(1, n_agents + 2 - n_conf)
        outcome = f"Result: Confessors ({', '.join(confessors)}) get {conf_years} years. Holdouts ({', '.join(holdouts)}) get {hold_years} years."

    narrative = f"""{n_agents} people jointly stole from a corporation that was defrauding elderly victims. They returned all money to the victims.

The group:
{agent_desc}

They are arrested and interrogated separately.

{payoffs}

{info}

{actions}

{outcome}"""

    return {
        "title": f"The Prisoner's {n_agents}-Lemma",
        "narrative": narrative,
        "agents": agent_names,
        "topology": topology.value,
    }


def generate_triage_narrative(n_agents: int, topology: Topology) -> Dict:
    """Generate triage scenario with N patients."""

    roles = AGENT_ROLES[Template.TRIAGE][:n_agents]
    agent_names = [chr(65 + i) for i in range(n_agents)]

    agent_desc = "\n".join(
        [
            f"- Person {name}: {role[0]} ({role[1]})"
            for name, role in zip(agent_names, roles)
        ]
    )

    # Resource constraints
    doctors = max(1, n_agents // 3)

    if topology == Topology.ALL:
        mechanism = f"""Triage protocol:
- {doctors} doctor(s) available, can each treat one patient fully or two partially
- Full treatment: 90% survival. Partial: 50% survival. No treatment: varies by severity.
- Committee must agree on allocation by majority vote."""
    elif topology == Topology.CHAIN:
        mechanism = f"""Triage protocol (sequential):
- Patients treated in order of arrival: A, B, C, ...
- Each treatment delays the next; later patients may deteriorate
- Resources deplete: first patient gets full treatment, later patients get diminishing care."""
    elif topology == Topology.STAR:
        mechanism = f"""Triage protocol (chief decides):
- Person {agent_names[0]} is the triage chief
- Chief allocates all resources unilaterally
- Others can object but chief has final authority."""

    # Generate treatment decisions
    treated = random.sample(agent_names, k=min(doctors * 2, n_agents))
    untreated = [n for n in agent_names if n not in treated]

    actions = "Treatment decisions:\n"
    for name in agent_names:
        if name in treated[:doctors]:
            actions += f"- Person {name}: Full treatment\n"
        elif name in treated:
            actions += f"- Person {name}: Partial treatment\n"
        else:
            actions += f"- Person {name}: No treatment (resources exhausted)\n"

    # Outcomes
    survivors = treated[:doctors] + [
        t for t in treated[doctors:] if random.random() > 0.5
    ]
    died = [n for n in agent_names if n not in survivors]

    outcome = f"Outcome: {len(survivors)} survived, {len(died)} died."
    if died:
        outcome += f"\nDid not survive: {', '.join(f'Person {d}' for d in died)}"

    narrative = f"""Emergency room with {n_agents} patients and limited resources.

The patients:
{agent_desc}

{mechanism}

{actions}

{outcome}"""

    return {
        "title": f"The Triage ({n_agents} Patients)",
        "narrative": narrative,
        "agents": agent_names,
        "topology": topology.value,
    }


NARRATIVE_GENERATORS = {
    Template.LIFERAFT: generate_liferaft_narrative,
    Template.TROLLEY_NETWORK: generate_trolley_network_narrative,
    Template.PRISONERS: generate_prisoners_narrative,
    Template.TRIAGE: generate_triage_narrative,
}


# =============================================================================
# MORAL AXES
# =============================================================================

AXIS_DEFINITIONS = {
    MoralAxis.DEONTOLOGICAL: {
        "name": "Deontological (Duty-Based)",
        "question": "Did {agent} violate any moral duties or rights, regardless of consequences?",
    },
    MoralAxis.CONSEQUENTIALIST: {
        "name": "Consequentialist (Outcome-Based)",
        "question": "Did {agent}'s actions lead to worse outcomes than available alternatives?",
    },
    MoralAxis.VIRTUE: {
        "name": "Virtue Ethics (Character-Based)",
        "question": "Did {agent} act in a way that reflects poor moral character or vicious intent?",
    },
    MoralAxis.CARE: {
        "name": "Care Ethics (Relationship-Based)",
        "question": "Did {agent} fail to appropriately care for vulnerable others or maintain relationships of trust?",
    },
    MoralAxis.JUSTICE: {
        "name": "Justice (Fairness-Based)",
        "question": "Did {agent} act unfairly or take more than their fair share?",
    },
    MoralAxis.CONTRACTARIAN: {
        "name": "Contractarian (Agreement-Based)",
        "question": "Did {agent} violate agreements or act in ways they couldn't justify to all affected parties?",
    },
}

# Default axis pairs to test (should be incompatible for Bell-like tests)
DEFAULT_AXIS_PAIRS = [
    (MoralAxis.DEONTOLOGICAL, MoralAxis.CONSEQUENTIALIST),
    (MoralAxis.JUSTICE, MoralAxis.CARE),
]


# =============================================================================
# PROMPT TEMPLATES BY LANGUAGE
# =============================================================================

PROMPTS = {
    Language.ENGLISH: """You are a moral philosopher evaluating a complex multi-agent scenario.

SCENARIO: {title}

{narrative}

EVALUATION TASK:
Consider ONLY Person {agent} and apply ONLY this ethical framework:

Framework: {axis_name}
Question: {axis_question}

Based strictly on this framework, what is your verdict on Person {agent}?
- GUILTY: They acted wrongly according to this framework
- NOT_GUILTY: They acted permissibly according to this framework

You MUST choose one. Consider only Person {agent}'s actions under this specific framework.

Respond with ONLY a JSON object:
{{"verdict": "GUILTY" or "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "one sentence"}}""",
    Language.JAPANESE: """あなたは複雑な多者間シナリオを評価する道徳哲学者です。

シナリオ：{title}

{narrative}

評価課題：
{agent}さんのみを考慮し、この倫理的フレームワークのみを適用してください：

フレームワーク：{axis_name}
質問：{axis_question}

このフレームワークに厳密に基づいて、{agent}さんへの判決は？
- GUILTY：このフレームワークによれば間違った行動
- NOT_GUILTY：このフレームワークによれば許容される行動

どちらか一つを選んでください。

JSONオブジェクトのみで回答：
{{"verdict": "GUILTY" または "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "一文"}}""",
    Language.ARABIC: """أنت فيلسوف أخلاقي تقيّم سيناريو معقد متعدد الأطراف.

السيناريو: {title}

{narrative}

مهمة التقييم:
فكر فقط في الشخص {agent} وطبق فقط هذا الإطار الأخلاقي:

الإطار: {axis_name}
السؤال: {axis_question}

بناءً على هذا الإطار بدقة، ما حكمك على الشخص {agent}؟
- GUILTY: تصرف بشكل خاطئ
- NOT_GUILTY: تصرف بشكل مقبول

يجب أن تختار واحداً.

أجب بكائن JSON فقط:
{{"verdict": "GUILTY" أو "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "جملة واحدة"}}""",
    Language.CHINESE: """你是一位评估复杂多方情境的道德哲学家。

情境：{title}

{narrative}

评估任务：
仅考虑{agent}，仅应用此伦理框架：

框架：{axis_name}
问题：{axis_question}

严格基于此框架，你对{agent}的判决是什么？
- GUILTY：行为错误
- NOT_GUILTY：行为可接受

你必须选择一个。

仅用JSON对象回复：
{{"verdict": "GUILTY" 或 "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "一句话"}}""",
    Language.HINDI: """आप एक नैतिक दार्शनिक हैं जो जटिल बहु-एजेंट परिदृश्य का मूल्यांकन कर रहे हैं।

परिदृश्य: {title}

{narrative}

मूल्यांकन कार्य:
केवल व्यक्ति {agent} पर विचार करें और केवल यह नैतिक ढांचा लागू करें:

ढांचा: {axis_name}
प्रश्न: {axis_question}

इस ढांचे के आधार पर, व्यक्ति {agent} पर आपका फैसला क्या है?
- GUILTY: गलत व्यवहार
- NOT_GUILTY: स्वीकार्य व्यवहार

आपको एक चुनना होगा।

केवल JSON में उत्तर:
{{"verdict": "GUILTY" या "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "एक वाक्य"}}""",
    Language.ICELANDIC: """Þú ert siðfræðingur sem metur flókna fjölaðila atburðarás.

ATBURÐARÁS: {title}

{narrative}

MATSVERKEFNI:
Íhugaðu AÐEINS einstakling {agent} og notaðu AÐEINS þennan siðferðilega ramma:

Rammi: {axis_name}
Spurning: {axis_question}

Byggt á þessum ramma, hver er úrskurður þinn um einstakling {agent}?
- GUILTY: Brást ranglega
- NOT_GUILTY: Brást leyfilega

Þú VERÐUR að velja annað.

Svaraðu AÐEINS með JSON:
{{"verdict": "GUILTY" eða "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "ein setning"}}""",
}


# =============================================================================
# MERMIN INEQUALITY CALCULATIONS
# =============================================================================


def mermin_bounds(n: int) -> Dict[str, float]:
    """
    Calculate classical and quantum bounds for N-party Mermin inequality.

    Classical bound: 2^(floor((N-1)/2))
    Quantum bound: 2^((N-1)/2) for odd N, 2^(N/2) for even N
    """
    if n < 2:
        return {"classical": 0, "quantum": 0}

    # Classical bound
    classical = 2 ** ((n - 1) // 2)

    # Quantum bound (maximally entangled state)
    if n % 2 == 1:  # Odd N
        quantum = 2 ** ((n - 1) / 2)
    else:  # Even N
        quantum = 2 ** (n / 2)

    return {"classical": classical, "quantum": quantum, "ratio": quantum / classical}


def compute_mermin_correlator(
    verdicts: Dict[Tuple[str, str], int], n_agents: int
) -> float:
    """
    Compute Mermin-Klyshko correlator for N agents.

    For N parties with measurements along two axes (0, 1) each:
    M_N = (1/2)[M_{N-1} ⊗ (σ_0 + σ_1) + M'_{N-1} ⊗ (σ_0 - σ_1)]

    Where M'_{N-1} is M_{N-1} with all 0↔1 swapped.

    Simplified: we compute expectation values for all 2^N measurement configurations
    and combine them with appropriate signs.
    """
    agents = [chr(65 + i) for i in range(n_agents)]
    axes = ["primary", "secondary"]  # 0 and 1

    # Generate all measurement configurations
    configs = list(product([0, 1], repeat=n_agents))

    # Mermin polynomial coefficients
    # For each configuration, coefficient is (-1)^(number of 1s in config that don't contribute to correlation)
    # Simplified: we use the standard Mermin form

    correlations = []
    for config in configs:
        # Get verdicts for this configuration
        key_set = tuple((agents[i], axes[config[i]]) for i in range(n_agents))

        # Compute N-body correlation: product of all verdicts
        product_val = 1
        valid = True
        for i, agent in enumerate(agents):
            axis = axes[config[i]]
            verdict = verdicts.get((agent, axis))
            if verdict is None:
                valid = False
                break
            product_val *= verdict

        if valid:
            # Mermin coefficient for this configuration
            # Sign alternates based on parity of configuration
            n_ones = sum(config)
            sign = 1 if (n_ones * (n_ones - 1) // 2) % 2 == 0 else -1
            correlations.append(sign * product_val)

    if not correlations:
        return 0.0

    # Mermin correlator is weighted sum
    return sum(correlations) / len(correlations) * (2 ** (n_agents - 1))


def compute_chsh_extended(
    verdicts_by_trial: Dict[int, Dict[Tuple[str, str], int]], n_agents: int
) -> Dict:
    """
    Compute extended CHSH/Mermin statistics across trials.

    For N=2, this reduces to standard CHSH.
    For N>2, uses Mermin inequality.
    """
    agents = [chr(65 + i) for i in range(n_agents)]

    # Compute correlator for each trial
    correlators = []
    for trial_id, verdicts in verdicts_by_trial.items():
        M = compute_mermin_correlator(verdicts, n_agents)
        correlators.append(M)

    if not correlators:
        return {"M": 0, "se": float("inf"), "n_trials": 0}

    # Statistics
    M_mean = sum(correlators) / len(correlators)
    if len(correlators) > 1:
        variance = sum((m - M_mean) ** 2 for m in correlators) / (len(correlators) - 1)
        se = math.sqrt(variance / len(correlators))
    else:
        se = 1.0

    bounds = mermin_bounds(n_agents)
    violation = abs(M_mean) > bounds["classical"]
    sigma = (abs(M_mean) - bounds["classical"]) / se if se > 0 and violation else 0

    return {
        "M": M_mean,
        "se": se,
        "n_trials": len(correlators),
        "classical_bound": bounds["classical"],
        "quantum_bound": bounds["quantum"],
        "violation": violation,
        "sigma": sigma,
        "raw_correlators": correlators[:10],  # Store first 10 for debugging
    }


# =============================================================================
# BATCH GENERATION
# =============================================================================


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment."""

    n_agents: int
    template: Template
    topology: Topology
    axes: Tuple[MoralAxis, MoralAxis]
    languages: List[Language]
    n_trials: int
    model: str = "claude-sonnet-4-20250514"

    def __post_init__(self):
        # Ensure we have enough languages for agents
        if len(self.languages) < self.n_agents:
            # Cycle through available languages
            self.languages = [
                self.languages[i % len(self.languages)] for i in range(self.n_agents)
            ]


def generate_requests(
    config: ExperimentConfig, seed: int = None
) -> Tuple[List[Dict], List[Dict]]:
    """Generate API requests for an experiment configuration."""

    if seed:
        random.seed(seed)

    requests = []
    specs = []

    # Get narrative generator
    generator = NARRATIVE_GENERATORS.get(config.template)
    if not generator:
        print(f"Warning: No generator for {config.template}, using liferaft")
        generator = generate_liferaft_narrative

    for trial in range(config.n_trials):
        # Generate scenario (same for all agents in trial, but randomized between trials)
        scenario = generator(config.n_agents, config.topology)
        agents = scenario["agents"]

        # For each agent, measure under both axes
        for i, agent in enumerate(agents):
            lang = config.languages[i]

            for axis in config.axes:
                axis_def = AXIS_DEFINITIONS[axis]
                prompt_template = PROMPTS.get(lang, PROMPTS[Language.ENGLISH])

                prompt = prompt_template.format(
                    title=scenario["title"],
                    narrative=scenario["narrative"],
                    agent=agent,
                    axis_name=axis_def["name"],
                    axis_question=axis_def["question"].format(agent=f"Person {agent}"),
                )

                salt = secrets.token_hex(4)
                axis_code = "p" if axis == config.axes[0] else "s"
                lang_str = "-".join(
                    l.value for l in config.languages[: config.n_agents]
                )
                custom_id = f"nb_{config.template.value[:4]}_{config.n_agents}_{config.topology.value[:3]}_{lang_str}_{trial:03d}_{agent}{axis_code}_{salt}"

                requests.append(
                    {
                        "custom_id": custom_id,
                        "params": {
                            "model": config.model,
                            "max_tokens": 200,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    }
                )

                specs.append(
                    {
                        "custom_id": custom_id,
                        "n_agents": config.n_agents,
                        "template": config.template.value,
                        "topology": config.topology.value,
                        "trial": trial,
                        "agent": agent,
                        "axis": axis.value,
                        "language": lang.value,
                        "languages": [
                            l.value for l in config.languages[: config.n_agents]
                        ],
                        "axes": [a.value for a in config.axes],
                    }
                )

    return requests, specs


def generate_sweep(
    n_trials: int, model: str
) -> Tuple[List[Dict], List[Dict], List[ExperimentConfig]]:
    """Generate requests for a parameter sweep."""

    all_requests = []
    all_specs = []
    configs = []

    # Sweep parameters
    n_agents_options = [3, 4, 5, 6]
    topology_options = [Topology.ALL, Topology.CHAIN, Topology.STAR]
    template_options = [Template.LIFERAFT, Template.TROLLEY_NETWORK, Template.PRISONERS]
    axes_options = [
        (MoralAxis.DEONTOLOGICAL, MoralAxis.CONSEQUENTIALIST),
        (MoralAxis.JUSTICE, MoralAxis.CARE),
    ]

    # Full language set for max N
    all_languages = [
        Language.ENGLISH,
        Language.JAPANESE,
        Language.ARABIC,
        Language.CHINESE,
        Language.HINDI,
        Language.ICELANDIC,
    ]

    for n_agents in n_agents_options:
        for topology in topology_options:
            for template in template_options:
                for axes in axes_options:
                    config = ExperimentConfig(
                        n_agents=n_agents,
                        template=template,
                        topology=topology,
                        axes=axes,
                        languages=all_languages[:n_agents],
                        n_trials=n_trials,
                        model=model,
                    )

                    reqs, specs = generate_requests(config)
                    all_requests.extend(reqs)
                    all_specs.extend(specs)
                    configs.append(config)

    return all_requests, all_specs, configs


# =============================================================================
# RESULTS PARSING AND ANALYSIS
# =============================================================================


def parse_verdict(text: str) -> Tuple[int, Optional[str]]:
    """Parse verdict from response. Returns (verdict, error)."""
    import re

    try:
        clean = text.strip()
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                if "verdict" in part.lower():
                    clean = part
                    break
            clean = clean.replace("json", "").strip()

        data = json.loads(clean)
        v = data.get("verdict", "").upper()

        if "NOT" in v and "GUILTY" in v:
            return 1, None
        elif "GUILTY" in v:
            return -1, None
    except:
        pass

    # Regex fallback
    if re.search(r"\bNOT[_\s]?GUILTY\b", text, re.IGNORECASE):
        return 1, None
    elif re.search(r"\bGUILTY\b", text, re.IGNORECASE):
        return -1, None

    return 0, f"Parse failed: {text[:80]}"


def analyze_results(results: Dict, specs: List[Dict]) -> List[Dict]:
    """Analyze results and compute Mermin statistics for each configuration."""

    specs_map = {s["custom_id"]: s for s in specs}

    # Group by configuration
    configs = {}
    parse_errors = []

    for cid, data in results.items():
        spec = data.get("spec") or specs_map.get(cid, {})
        verdict = data.get("verdict", 0)

        if verdict == 0:
            parse_errors.append(cid)
            continue

        # Configuration key
        key = (
            spec.get("n_agents"),
            spec.get("template"),
            spec.get("topology"),
            tuple(spec.get("axes", [])),
            tuple(spec.get("languages", [])),
        )

        trial = spec.get("trial")
        agent = spec.get("agent")
        axis = spec.get("axis")

        if key not in configs:
            configs[key] = {}
        if trial not in configs[key]:
            configs[key][trial] = {}

        # Map axis value back to primary/secondary
        axes_list = spec.get("axes", [])
        axis_key = "primary" if axis == axes_list[0] else "secondary"

        configs[key][trial][(agent, axis_key)] = verdict

    # Compute statistics for each configuration
    analysis = []

    for key, trials in configs.items():
        n_agents, template, topology, axes, languages = key

        if n_agents is None:
            continue

        # Compute Mermin correlator
        stats = compute_chsh_extended(trials, n_agents)

        analysis.append(
            {
                "n_agents": n_agents,
                "template": template,
                "topology": topology,
                "axes": list(axes),
                "languages": list(languages),
                "M": stats["M"],
                "se": stats["se"],
                "n_trials": stats["n_trials"],
                "classical_bound": stats["classical_bound"],
                "quantum_bound": stats["quantum_bound"],
                "violation": stats["violation"],
                "sigma": stats["sigma"],
            }
        )

    return analysis, parse_errors


def print_analysis(analysis: List[Dict], parse_errors: List, output_dir: Path):
    """Print analysis results."""

    print("\n" + "=" * 80)
    print("QND N-BODY ENTANGLEMENT TEST - RESULTS")
    print("=" * 80)
    print(
        "M = Mermin correlator | Classical: |M| ≤ bound | Quantum: |M| ≤ higher bound"
    )
    print("=" * 80)

    # Group by N
    by_n = {}
    for r in analysis:
        n = r["n_agents"]
        if n not in by_n:
            by_n[n] = []
        by_n[n].append(r)

    violations = []

    for n in sorted(by_n.keys()):
        results = by_n[n]
        bounds = mermin_bounds(n)

        print(f"\n{'─' * 80}")
        print(
            f" N={n} AGENTS | Classical ≤ {bounds['classical']:.1f} | Quantum ≤ {bounds['quantum']:.2f}"
        )
        print(f"{'─' * 80}")

        # Sort by sigma
        results.sort(key=lambda x: -x.get("sigma", 0))

        for r in results:
            lang_str = "-".join(r["languages"][:3]) + (
                "..." if len(r["languages"]) > 3 else ""
            )
            axes_str = f"{r['axes'][0][:4]}/{r['axes'][1][:4]}"

            line = f"  {r['template'][:8]:<8} {r['topology'][:5]:<5} {axes_str:<10} {lang_str:<12}"
            line += f"M={r['M']:+.3f}±{r['se']:.3f} n={r['n_trials']:<3}"

            if r["violation"]:
                stars = "★" * min(int(r["sigma"]), 5)
                line += f"  {stars} {r['sigma']:.1f}σ VIOLATION"
                violations.append(r)

            print(line)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(analysis)
    n_viol = len(violations)

    print(f"Total configurations: {total}")
    print(
        f"Violations detected: {n_viol} ({100*n_viol/total:.1f}%)" if total > 0 else ""
    )
    print(f"Parse errors: {len(parse_errors)}")

    if violations:
        print(f"\n{'★' * 40}")
        print("VIOLATIONS DETECTED!")
        print(f"{'★' * 40}")

        # Best by N
        print("\nBest violations by N:")
        for n in sorted(by_n.keys()):
            n_viols = [v for v in violations if v["n_agents"] == n]
            if n_viols:
                best = max(n_viols, key=lambda x: x["sigma"])
                print(
                    f"  N={n}: {best['template']} {best['topology']} → {best['sigma']:.2f}σ"
                )

        # Overall best
        best_overall = max(violations, key=lambda x: x["sigma"])
        print(
            f"\nStrongest: N={best_overall['n_agents']} {best_overall['template']} "
            f"{best_overall['topology']} → {best_overall['sigma']:.2f}σ"
        )
    else:
        print("\nNo violations detected. All results within classical bounds.")

    # Save artifact
    artifact = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_configs": total,
            "violations": n_viol,
            "best_sigma": max(v["sigma"] for v in violations) if violations else 0,
        },
        "results": analysis,
        "violations": violations,
        "parse_errors": parse_errors[:50],
    }

    path = output_dir / "qnd_nbody_results.json"
    with open(path, "w") as f:
        json.dump(artifact, f, indent=2)

    print(f"\nResults saved to: {path}")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="QND N-Body Entanglement Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id", help="Batch ID for status/results")

    # Experiment configuration
    parser.add_argument(
        "--n-agents", type=int, default=3, help="Number of agents (2-6)"
    )
    parser.add_argument(
        "--template",
        default="liferaft",
        choices=["liferaft", "trolley_network", "prisoners", "triage"],
    )
    parser.add_argument("--topology", default="all", choices=["all", "chain", "star"])
    parser.add_argument(
        "--axes",
        nargs=2,
        default=["deontological", "consequentialist"],
        help="Two moral axes to test",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        help="Languages for agents (cycles if fewer than n_agents)",
    )
    parser.add_argument("--n-trials", type=int, default=100)
    parser.add_argument("--sweep", action="store_true", help="Run parameter sweep")

    parser.add_argument("--output-dir", default="qnd_nbody_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # ==========================================================================
    # SUBMIT
    # ==========================================================================
    if args.mode == "submit":

        if args.sweep:
            print("Generating parameter sweep...")
            all_requests, all_specs, configs = generate_sweep(args.n_trials, args.model)

            print(f"Sweep configuration:")
            print(f"  - N agents: 3, 4, 5, 6")
            print(f"  - Topologies: all, chain, star")
            print(f"  - Templates: liferaft, trolley_network, prisoners")
            print(f"  - Axes: deon/conseq, justice/care")
            print(f"  - Total configs: {len(configs)}")

        else:
            # Parse enums
            template = Template(args.template)
            topology = Topology(args.topology)
            axes = tuple(MoralAxis(a) for a in args.axes)
            languages = [Language(l) for l in args.languages]

            config = ExperimentConfig(
                n_agents=args.n_agents,
                template=template,
                topology=topology,
                axes=axes,
                languages=languages,
                n_trials=args.n_trials,
                model=args.model,
            )

            all_requests, all_specs = generate_requests(config)
            configs = [config]

            print(f"Single configuration:")
            print(f"  - N agents: {args.n_agents}")
            print(f"  - Template: {args.template}")
            print(f"  - Topology: {args.topology}")
            print(f"  - Axes: {args.axes}")
            print(f"  - Languages: {args.languages}")

        # Cost estimate
        cost = len(all_requests) * (1000 * 1.5 + 100 * 7.5) / 1e6

        print(f"\nTotal requests: {len(all_requests)}")
        print(f"Estimated cost: ${cost:.2f}")

        # Pre-registration hash
        prereg = hashlib.sha256(
            json.dumps(
                {
                    "n_requests": len(all_requests),
                    "n_configs": len(configs),
                    "timestamp": datetime.now().isoformat(),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]

        print(f"Pre-registration hash: {prereg}")

        # Save specs
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        specs_path = output_dir / f"specs_{ts}.json"
        with open(specs_path, "w") as f:
            json.dump({"prereg": prereg, "specs": all_specs}, f)

        # Submit batch
        batch = client.messages.batches.create(requests=all_requests)

        print(f"\nBatch submitted: {batch.id}")
        print(f"Status: {batch.processing_status}")

        # Save batch info
        with open(output_dir / f"batch_{ts}.json", "w") as f:
            json.dump(
                {
                    "batch_id": batch.id,
                    "prereg": prereg,
                    "n_requests": len(all_requests),
                    "sweep": args.sweep,
                },
                f,
                indent=2,
            )

        print(
            f"\nCheck status: python {sys.argv[0]} --api-key KEY --mode status --batch-id {batch.id}"
        )

    # ==========================================================================
    # STATUS
    # ==========================================================================
    elif args.mode == "status":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Batch: {args.batch_id}")
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

        if hasattr(batch.request_counts, "succeeded"):
            total = (
                batch.request_counts.processing
                + batch.request_counts.succeeded
                + batch.request_counts.errored
            )
            if total > 0:
                pct = 100 * batch.request_counts.succeeded / total
                print(f"Progress: {pct:.1f}%")

    # ==========================================================================
    # RESULTS
    # ==========================================================================
    elif args.mode == "results":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        # Load specs
        specs_files = sorted(output_dir.glob("specs_*.json"))
        if not specs_files:
            print("Error: No specs file found")
            return

        with open(specs_files[-1]) as f:
            data = json.load(f)
        specs = data.get("specs", data)
        prereg = data.get("prereg", "unknown")

        print(f"Pre-registration hash: {prereg}")
        print(f"Retrieving results for {args.batch_id}...")

        specs_map = {s["custom_id"]: s for s in specs}

        # Retrieve results
        results = {}
        for r in client.messages.batches.results(args.batch_id):
            if r.result.type == "succeeded":
                text = r.result.message.content[0].text
                verdict, error = parse_verdict(text)
                results[r.custom_id] = {
                    "spec": specs_map.get(r.custom_id, {}),
                    "verdict": verdict,
                    "error": error,
                }
            else:
                results[r.custom_id] = {
                    "spec": specs_map.get(r.custom_id, {}),
                    "verdict": 0,
                    "error": f"API error: {r.result.type}",
                }

        print(f"Retrieved {len(results)} results")

        # Analyze
        analysis, errors = analyze_results(results, specs)

        # Print
        print_analysis(analysis, errors, output_dir)


if __name__ == "__main__":
    main()
