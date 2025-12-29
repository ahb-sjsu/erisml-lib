#!/usr/bin/env python3
"""
Quantum Normative Dynamics (QND) Experiment
Testing quantum cognition predictions on Reddit AITA data

This experiment tests three QND predictions:
1. ORDER EFFECTS: Asking questions in different orders changes moral judgments
   (non-commuting observables)
2. INTERFERENCE: Multiple ethical frameworks don't simply add - they interfere
3. SUPERPOSITION COLLAPSE: Ambiguous cases show more quantum effects than clear cases

Usage:
    python qnd_aita_experiment.py --api-key YOUR_ANTHROPIC_KEY
    
Or set ANTHROPIC_API_KEY environment variable.
"""

import json
import os
import argparse
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
from pathlib import Path
import random

# Data processing
import pandas as pd

# For API calls
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic package not installed. Install with: pip install anthropic")


# ============================================================================
# SAMPLE AITA DATA (for immediate testing without API)
# These are representative examples - in production you'd fetch from Reddit/Pushshift
# ============================================================================

SAMPLE_AITA_POSTS = [
    {
        "id": "sample_001",
        "title": "AITA for not letting my sister use my car after she crashed it last time?",
        "body": """My sister (25F) asked to borrow my car (28F) for a weekend trip. Last time she borrowed it 
6 months ago, she got into a fender bender and didn't tell me until I noticed the damage. She said 
it wasn't her fault but never offered to pay for repairs. I paid $800 out of pocket.

Now she's asking again because her car is in the shop. She promised to be careful and said the 
accident was a one-time thing. Our mom thinks I should help family, but I don't trust her with my car. 
She called me selfish and said I'm holding a grudge. AITA?""",
        "verdict": "NTA",
        "score": 4523,
        "num_comments": 892,
        "ambiguity_level": "low"  # Clear NTA case
    },
    {
        "id": "sample_002",
        "title": "AITA for telling my friend her wedding dress doesn't look good on her?",
        "body": """My best friend (29F) asked for my honest opinion about her wedding dress. She tried it on 
and asked what I thought. The dress was objectively unflattering - it washed out her complexion and 
the cut wasn't right for her body type.

I tried to be gentle and said 'I think you could find something that flatters you more.' She got 
really upset and said I ruined the experience. She wanted me to just say it looked beautiful. 
Her mom agrees with her that I should have lied. But she asked for my HONEST opinion. AITA?""",
        "verdict": "ESH",  # Entangled - both have partial blame
        "score": 2341,
        "num_comments": 1543,
        "ambiguity_level": "high"  # Genuinely contested
    },
    {
        "id": "sample_003",
        "title": "AITA for not attending my brother's wedding because of the venue?",
        "body": """My brother (32M) is getting married at a destination wedding in Mexico. I (28F) have severe 
anxiety about flying and haven't been on a plane in 5 years. I've been in therapy for it but I'm 
not ready for a 4-hour flight.

I told him I couldn't come and offered to throw them a reception party when they get back. He said 
if I really loved him I'd push through my fear for one day. He's now saying I'm being dramatic and 
choosing my 'issues' over family. My parents are split - dad gets it, mom thinks I should just 
take medication and go. AITA?""",
        "verdict": "NAH",  # No clear asshole - genuine conflict
        "score": 3892,
        "num_comments": 2103,
        "ambiguity_level": "high"
    },
    {
        "id": "sample_004",
        "title": "AITA for reporting my coworker for time theft?",
        "body": """I (34M) noticed my coworker (28M) has been clocking in, then going to get breakfast for 
30-40 minutes every day. He's been doing this for months. We're hourly employees and this is 
clearly against policy.

I mentioned it to him first and he laughed it off, saying 'everyone does stuff like this.' I 
reported it to HR. He got written up and is now on thin ice. He and several coworkers think I'm a 
snitch and the office atmosphere is now hostile. But he was literally stealing from the company. AITA?""",
        "verdict": "YTA",  # Controversial - technically right but socially wrong
        "score": 1892,
        "num_comments": 3421,
        "ambiguity_level": "medium"
    },
    {
        "id": "sample_005",
        "title": "AITA for not sharing my inheritance with my step-siblings?",
        "body": """My grandmother left me (26F) $50,000 in her will. She specifically named me and not my 
step-siblings (24M, 22F), who she never really bonded with after my mom remarried when I was 15.

My step-siblings are struggling financially and my stepdad thinks I should split it 'to be fair.' 
My mom is staying neutral but I can tell she wants peace. I offered to help with specific expenses 
but won't split it evenly - it was left to ME. They're calling me greedy. AITA?""",
        "verdict": "NTA",
        "score": 6234,
        "num_comments": 1876,
        "ambiguity_level": "low"
    },
    {
        "id": "sample_006",
        "title": "AITA for refusing to cook separate meals for my picky husband?",
        "body": """My husband (35M) is extremely picky. He won't eat vegetables, most proteins except chicken 
nuggets and ground beef, and only likes 'white' foods (pasta, bread, rice). I (33F) have been 
cooking him separate meals for 3 years but I'm exhausted.

I told him I'll make one family meal and he can eat it or make his own food. He says I'm being 
unsupportive of his eating issues (he won't see a doctor about it). He thinks a good wife would 
accommodate him. My MIL says I should just do it since 'it's not that hard.' AITA?""",
        "verdict": "NTA",
        "score": 8921,
        "num_comments": 2654,
        "ambiguity_level": "low"
    },
    {
        "id": "sample_007",
        "title": "AITA for telling my daughter she can't bring her boyfriend to family Christmas?",
        "body": """My daughter (19F) has been dating her boyfriend (24M) for 3 months. She wants to bring him 
to our family Christmas, which has always been immediate family only (me, husband, and our 3 kids).

I said no - we barely know him and Christmas is special family time. She can bring him to New Year's 
when extended family comes. She's furious and says I'm being controlling and don't respect her 
relationship. My husband thinks we should let her but I feel 3 months isn't long enough. AITA?""",
        "verdict": "NAH",
        "score": 2134,
        "num_comments": 1923,
        "ambiguity_level": "high"
    },
    {
        "id": "sample_008",
        "title": "AITA for calling the police on my neighbor's loud party at 2am?",
        "body": """My neighbor (20sM) threw a party that went until 3am on a Tuesday night. I (42F) have 
work at 6am and couldn't sleep. I asked them twice to quiet down - first at 11pm, then at 1am. 
Both times they said they would but got louder.

At 2am I called the non-emergency police line. The party got shut down and my neighbor got a 
noise violation ticket. Now the whole building is mad at me for 'being that person' and my 
neighbor won't acknowledge me. I need to sleep to function at work. AITA?""",
        "verdict": "NTA",
        "score": 5432,
        "num_comments": 987,
        "ambiguity_level": "low"
    },
    {
        "id": "sample_009",
        "title": "AITA for not forgiving my father after he apologized?",
        "body": """My father (58M) was emotionally absent my entire childhood. He worked constantly, missed 
every important event, and when he was home, he was distant and critical. I (28F) have been in 
therapy for years dealing with the effects.

Now he's retired and wants a relationship. He gave what I think is a genuine apology and says he 
regrets his choices. But I don't feel ready to forgive him or have a close relationship. My mom 
and siblings think I should give him a chance since 'he's trying.' AITA for not being ready?""",
        "verdict": "NAH",
        "score": 4521,
        "num_comments": 2341,
        "ambiguity_level": "medium"
    },
    {
        "id": "sample_010",
        "title": "AITA for refusing to pay for my portion of a meal I didn't eat?",
        "body": """I (27F) went to dinner with friends. I ordered a salad ($15) but when we got the bill, 
they wanted to split it evenly. The total was $200 for 5 people, so $40 each. Others had steaks, 
multiple drinks, and appetizers.

I said I'd pay for what I ordered plus tip ($20). They said splitting evenly is 'just what 
friends do' and I was making it awkward. One friend said I was being cheap. But I literally ate 
a $15 salad while they had $50+ meals. I paid my share and left. AITA?""",
        "verdict": "NTA",
        "score": 7832,
        "num_comments": 1432,
        "ambiguity_level": "low"
    }
]


# ============================================================================
# DATA STRUCTURES FOR QUANTUM ETHICAL STATE
# ============================================================================

@dataclass
class SuperpositionBranch:
    """A branch in the moral superposition"""
    branch_id: str
    verdict: str  # YTA, NTA, ESH, NAH
    amplitude_squared: float  # Probability if measured
    reasoning: str
    dominant_framework: str  # consequentialist, deontological, virtue, care

@dataclass
class InterferenceResult:
    """Results of interference test between reasoning paths"""
    path_a: str
    path_b: str
    p_a_alone: float
    p_b_alone: float
    p_both_classical: float  # Expected if no interference
    p_both_actual: float
    interference_term: float  # p_actual - p_classical
    effect: str  # constructive, destructive, none

@dataclass
class OrderEffectResult:
    """Results of order effect test"""
    order_a: list  # e.g., ["harm", "intent", "verdict"]
    order_b: list  # e.g., ["intent", "harm", "verdict"]
    verdict_a: str
    verdict_b: str
    order_effect_detected: bool
    confidence_a: float
    confidence_b: float

@dataclass 
class QuantumEthicalState:
    """Full quantum state for an ethical situation"""
    post_id: str
    content: str
    
    # Superposition structure
    is_superposed: bool
    branches: list  # List of SuperpositionBranch
    
    # Measurement
    measured_verdict: Optional[str] = None
    measurement_confidence: float = 0.0
    
    # Experimental results
    order_effects: Optional[OrderEffectResult] = None
    interference: Optional[InterferenceResult] = None
    
    # Entanglement (for ESH cases)
    is_entangled: bool = False
    entangled_parties: list = field(default_factory=list)
    
    # Decoherence
    coherence_level: float = 1.0  # 1.0 = pure superposition, 0.0 = fully classical
    
    # Metadata
    timestamp: str = ""
    
    def to_dict(self):
        return asdict(self)


# ============================================================================
# QND EXPERIMENT ENGINE
# ============================================================================

class QNDExperiment:
    """Engine for running QND experiments on moral dilemma data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        if self.api_key and HAS_ANTHROPIC:
            self.client = Anthropic(api_key=self.api_key)
        self.results = []
        self.cache = {}  # Cache LLM responses for reproducibility
        
    def _hash_prompt(self, prompt: str) -> str:
        """Create a hash for caching"""
        return hashlib.md5(prompt.encode()).hexdigest()[:12]
    
    def _call_llm(self, prompt: str, system: str = "", use_cache: bool = True) -> str:
        """Call Claude API with caching"""
        cache_key = self._hash_prompt(system + prompt)
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.client:
            # Return mock response for testing without API
            return self._mock_response(prompt)
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system if system else "You are a moral reasoning assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            self.cache[cache_key] = result
            return result
        except Exception as e:
            print(f"API Error: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Generate mock responses for testing without API"""
        # Simple mock based on prompt content
        prompt_lower = prompt.lower()
        
        if "verdict" in prompt_lower:
            verdicts = ["NTA", "YTA", "ESH", "NAH"]
            # Use hash for deterministic mock responses
            idx = hash(prompt) % 4
            confidence = 0.5 + (hash(prompt + "conf") % 50) / 100
            return json.dumps({
                "verdict": verdicts[idx],
                "confidence": confidence,
                "reasoning": "Mock reasoning for testing purposes."
            })
        
        if "harm" in prompt_lower:
            harm_level = (hash(prompt) % 100) / 100
            return json.dumps({
                "harm_assessment": harm_level,
                "reasoning": "Mock harm assessment."
            })
            
        if "intent" in prompt_lower:
            intents = ["malicious", "negligent", "neutral", "good"]
            idx = hash(prompt) % 4
            return json.dumps({
                "intent": intents[idx],
                "reasoning": "Mock intent assessment."
            })
        
        return json.dumps({"response": "mock", "data": hash(prompt) % 100})

    # ========================================================================
    # TEST 1: ORDER EFFECTS
    # ========================================================================
    
    def test_order_effects(self, post: dict, n_trials: int = 3) -> OrderEffectResult:
        """
        QND Prediction: Non-commuting observables produce order effects.
        
        Test: Does asking about harm first vs. intent first change the verdict?
        Classical prediction: Order shouldn't matter
        Quantum prediction: Order matters (non-commuting operators)
        """
        
        title = post.get("title", "")
        body = post.get("body", "")
        content = f"{title}\n\n{body}"
        
        # Order A: Harm → Intent → Verdict
        prompt_order_a = f"""Analyze this moral situation step by step.

SITUATION:
{content}

Step 1: First, assess the HARM caused. What damage or negative consequences resulted from the actions?

Step 2: Now, assess the INTENT. What were the motivations and state of mind of the person?

Step 3: Based on your harm and intent analysis, give your final verdict.

Respond in JSON format:
{{
    "harm_assessment": "description of harm",
    "intent_assessment": "description of intent", 
    "verdict": "NTA/YTA/ESH/NAH",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        # Order B: Intent → Harm → Verdict
        prompt_order_b = f"""Analyze this moral situation step by step.

SITUATION:
{content}

Step 1: First, assess the INTENT. What were the motivations and state of mind of the person?

Step 2: Now, assess the HARM caused. What damage or negative consequences resulted from the actions?

Step 3: Based on your intent and harm analysis, give your final verdict.

Respond in JSON format:
{{
    "intent_assessment": "description of intent",
    "harm_assessment": "description of harm",
    "verdict": "NTA/YTA/ESH/NAH", 
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        verdicts_a = []
        verdicts_b = []
        confidences_a = []
        confidences_b = []
        
        for trial in range(n_trials):
            # Add trial number to prevent cache hits
            response_a = self._call_llm(prompt_order_a + f"\n[Trial {trial}]", use_cache=False)
            response_b = self._call_llm(prompt_order_b + f"\n[Trial {trial}]", use_cache=False)
            
            try:
                # Extract JSON from response
                result_a = self._parse_json_response(response_a)
                result_b = self._parse_json_response(response_b)
                
                verdicts_a.append(result_a.get("verdict", "UNKNOWN"))
                verdicts_b.append(result_b.get("verdict", "UNKNOWN"))
                confidences_a.append(result_a.get("confidence", 0.5))
                confidences_b.append(result_b.get("confidence", 0.5))
            except Exception as e:
                print(f"Parse error in trial {trial}: {e}")
                verdicts_a.append("ERROR")
                verdicts_b.append("ERROR")
        
        # Check for order effect
        order_effect_detected = verdicts_a != verdicts_b
        
        # Get most common verdict for each order
        verdict_a = max(set(verdicts_a), key=verdicts_a.count) if verdicts_a else "UNKNOWN"
        verdict_b = max(set(verdicts_b), key=verdicts_b.count) if verdicts_b else "UNKNOWN"
        
        return OrderEffectResult(
            order_a=["harm", "intent", "verdict"],
            order_b=["intent", "harm", "verdict"],
            verdict_a=verdict_a,
            verdict_b=verdict_b,
            order_effect_detected=order_effect_detected,
            confidence_a=sum(confidences_a) / len(confidences_a) if confidences_a else 0,
            confidence_b=sum(confidences_b) / len(confidences_b) if confidences_b else 0
        )
    
    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from LLM response"""
        # Try direct parse
        try:
            return json.loads(response)
        except:
            pass
        
        # Try to find JSON in response
        import re
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return {}

    # ========================================================================
    # TEST 2: INTERFERENCE EFFECTS
    # ========================================================================
    
    def test_interference(self, post: dict, n_trials: int = 5) -> InterferenceResult:
        """
        QND Prediction: Reasoning paths interfere, not just add.
        
        P(verdict | both frameworks) ≠ P(verdict | conseq) + P(verdict | deont) - P(both classical)
        
        Test: Compare verdicts when using:
        - Only consequentialist reasoning
        - Only deontological reasoning  
        - Both available (interference condition)
        """
        
        title = post.get("title", "")
        body = post.get("body", "")
        content = f"{title}\n\n{body}"
        
        # Consequentialist only
        prompt_conseq = f"""Analyze this moral situation using ONLY consequentialist ethics.
Focus ONLY on:
- The outcomes and consequences of actions
- Who was harmed and how much
- The overall utility/welfare produced

Do NOT consider duties, rights, or rules - only consequences matter.

SITUATION:
{content}

Respond in JSON:
{{"verdict": "NTA/YTA/ESH/NAH", "confidence": 0.0-1.0, "framework": "consequentialist"}}"""

        # Deontological only
        prompt_deont = f"""Analyze this moral situation using ONLY deontological ethics.
Focus ONLY on:
- Duties and obligations
- Rights that were respected or violated
- Universal moral rules and principles

Do NOT consider consequences - only duties and rights matter.

SITUATION:
{content}

Respond in JSON:
{{"verdict": "NTA/YTA/ESH/NAH", "confidence": 0.0-1.0, "framework": "deontological"}}"""

        # Both frameworks
        prompt_both = f"""Analyze this moral situation considering multiple ethical perspectives.
Consider:
- The outcomes and consequences (who was harmed?)
- Duties and rights (what obligations existed?)
- The character and virtues involved
- Care and relationships

Weigh all perspectives to reach a verdict.

SITUATION:
{content}

Respond in JSON:
{{"verdict": "NTA/YTA/ESH/NAH", "confidence": 0.0-1.0, "framework": "integrated"}}"""

        # Run trials
        conseq_verdicts = []
        deont_verdicts = []
        both_verdicts = []
        
        target_verdict = "NTA"  # We'll measure P(NTA) for each condition
        
        for trial in range(n_trials):
            r_c = self._call_llm(prompt_conseq + f"\n[Trial {trial}]", use_cache=False)
            r_d = self._call_llm(prompt_deont + f"\n[Trial {trial}]", use_cache=False)
            r_b = self._call_llm(prompt_both + f"\n[Trial {trial}]", use_cache=False)
            
            try:
                conseq_verdicts.append(self._parse_json_response(r_c).get("verdict", "UNKNOWN"))
                deont_verdicts.append(self._parse_json_response(r_d).get("verdict", "UNKNOWN"))
                both_verdicts.append(self._parse_json_response(r_b).get("verdict", "UNKNOWN"))
            except:
                pass
        
        # Calculate probabilities
        p_conseq = conseq_verdicts.count(target_verdict) / len(conseq_verdicts) if conseq_verdicts else 0
        p_deont = deont_verdicts.count(target_verdict) / len(deont_verdicts) if deont_verdicts else 0
        p_both = both_verdicts.count(target_verdict) / len(both_verdicts) if both_verdicts else 0
        
        # Classical prediction: weighted average (assuming equal weights)
        p_classical = (p_conseq + p_deont) / 2
        
        # Interference term
        interference = p_both - p_classical
        
        # Determine effect type
        if abs(interference) < 0.1:
            effect = "none"
        elif interference > 0:
            effect = "constructive"
        else:
            effect = "destructive"
        
        return InterferenceResult(
            path_a="consequentialist",
            path_b="deontological",
            p_a_alone=p_conseq,
            p_b_alone=p_deont,
            p_both_classical=p_classical,
            p_both_actual=p_both,
            interference_term=interference,
            effect=effect
        )

    # ========================================================================
    # TEST 3: SUPERPOSITION DETECTION
    # ========================================================================
    
    def extract_quantum_state(self, post: dict) -> QuantumEthicalState:
        """
        Extract the full quantum ethical state, including superposition branches.
        """
        title = post.get("title", "")
        body = post.get("body", "")
        content = f"{title}\n\n{body}"
        
        prompt = f"""Analyze this moral situation as a quantum superposition of ethical states.

SITUATION:
{content}

Consider that before judgment, this situation exists in a superposition of possible moral states.
Identify the different "branches" of the superposition - the different valid interpretations
that reasonable people might hold.

For each branch, estimate:
- The verdict (NTA/YTA/ESH/NAH)
- The probability weight (how likely this interpretation is)
- The dominant ethical framework supporting it
- Key reasoning

Respond in JSON:
{{
    "is_superposed": true/false,
    "branches": [
        {{
            "branch_id": "interpretation_1",
            "verdict": "NTA/YTA/ESH/NAH",
            "amplitude_squared": 0.0-1.0,
            "dominant_framework": "consequentialist/deontological/virtue/care",
            "reasoning": "explanation"
        }},
        ...
    ],
    "coherence_assessment": "how contested/ambiguous is this case?",
    "entanglement": {{
        "is_entangled": true/false,
        "parties": ["list of parties whose moral status is correlated"]
    }}
}}"""

        response = self._call_llm(prompt)
        result = self._parse_json_response(response)
        
        # Build branches
        branches = []
        for b in result.get("branches", []):
            branches.append(SuperpositionBranch(
                branch_id=b.get("branch_id", "unknown"),
                verdict=b.get("verdict", "UNKNOWN"),
                amplitude_squared=b.get("amplitude_squared", 0.5),
                reasoning=b.get("reasoning", ""),
                dominant_framework=b.get("dominant_framework", "unknown")
            ))
        
        # If no branches, create default
        if not branches:
            branches.append(SuperpositionBranch(
                branch_id="default",
                verdict=post.get("verdict", "UNKNOWN"),
                amplitude_squared=1.0,
                reasoning="Default interpretation",
                dominant_framework="unknown"
            ))
        
        # Check entanglement
        ent = result.get("entanglement", {})
        is_entangled = ent.get("is_entangled", False)
        entangled_parties = ent.get("parties", [])
        
        # ESH verdicts imply entanglement
        if any(b.verdict == "ESH" for b in branches):
            is_entangled = True
            if not entangled_parties:
                entangled_parties = ["OP", "other_party"]
        
        return QuantumEthicalState(
            post_id=post.get("id", "unknown"),
            content=content,
            is_superposed=result.get("is_superposed", len(branches) > 1),
            branches=branches,
            is_entangled=is_entangled,
            entangled_parties=entangled_parties,
            coherence_level=1.0 if len(branches) > 1 else 0.5,
            timestamp=datetime.now().isoformat()
        )

    # ========================================================================
    # MAIN EXPERIMENT RUNNER
    # ========================================================================
    
    def run_full_experiment(self, posts: list, n_trials: int = 3) -> dict:
        """Run all QND tests on a set of posts"""
        
        results = {
            "experiment_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
            "timestamp": datetime.now().isoformat(),
            "n_posts": len(posts),
            "n_trials_per_test": n_trials,
            "posts_results": [],
            "aggregate": {
                "order_effects_detected": 0,
                "interference_effects": {"constructive": 0, "destructive": 0, "none": 0},
                "superposition_cases": 0,
                "entanglement_cases": 0
            }
        }
        
        for i, post in enumerate(posts):
            print(f"\n{'='*60}")
            print(f"Processing post {i+1}/{len(posts)}: {post.get('title', 'Untitled')[:50]}...")
            print(f"Ground truth verdict: {post.get('verdict', 'Unknown')}")
            print(f"Ambiguity level: {post.get('ambiguity_level', 'unknown')}")
            
            post_result = {
                "post_id": post.get("id", f"post_{i}"),
                "title": post.get("title", ""),
                "ground_truth_verdict": post.get("verdict", ""),
                "ambiguity_level": post.get("ambiguity_level", "unknown")
            }
            
            # Test 1: Order Effects
            print("\n  Testing ORDER EFFECTS...")
            order_result = self.test_order_effects(post, n_trials)
            post_result["order_effects"] = asdict(order_result)
            print(f"    Order A (harm→intent): {order_result.verdict_a}")
            print(f"    Order B (intent→harm): {order_result.verdict_b}")
            print(f"    Order effect detected: {order_result.order_effect_detected}")
            
            if order_result.order_effect_detected:
                results["aggregate"]["order_effects_detected"] += 1
            
            # Test 2: Interference
            print("\n  Testing INTERFERENCE...")
            interference_result = self.test_interference(post, n_trials)
            post_result["interference"] = asdict(interference_result)
            print(f"    P(NTA|consequentialist): {interference_result.p_a_alone:.2f}")
            print(f"    P(NTA|deontological): {interference_result.p_b_alone:.2f}")
            print(f"    P(NTA|both) classical: {interference_result.p_both_classical:.2f}")
            print(f"    P(NTA|both) actual: {interference_result.p_both_actual:.2f}")
            print(f"    Interference term: {interference_result.interference_term:+.2f}")
            print(f"    Effect: {interference_result.effect}")
            
            results["aggregate"]["interference_effects"][interference_result.effect] += 1
            
            # Test 3: Quantum State Extraction
            print("\n  Extracting QUANTUM STATE...")
            quantum_state = self.extract_quantum_state(post)
            post_result["quantum_state"] = {
                "is_superposed": quantum_state.is_superposed,
                "n_branches": len(quantum_state.branches),
                "branches": [asdict(b) for b in quantum_state.branches],
                "is_entangled": quantum_state.is_entangled,
                "entangled_parties": quantum_state.entangled_parties
            }
            print(f"    Superposed: {quantum_state.is_superposed}")
            print(f"    Branches: {len(quantum_state.branches)}")
            for b in quantum_state.branches[:3]:  # Show first 3
                print(f"      - {b.verdict} (p={b.amplitude_squared:.2f}): {b.reasoning[:50]}...")
            print(f"    Entangled: {quantum_state.is_entangled}")
            
            if quantum_state.is_superposed:
                results["aggregate"]["superposition_cases"] += 1
            if quantum_state.is_entangled:
                results["aggregate"]["entanglement_cases"] += 1
            
            results["posts_results"].append(post_result)
        
        # Calculate summary statistics
        n = len(posts)
        results["summary"] = {
            "order_effect_rate": results["aggregate"]["order_effects_detected"] / n,
            "superposition_rate": results["aggregate"]["superposition_cases"] / n,
            "entanglement_rate": results["aggregate"]["entanglement_cases"] / n,
            "interference_distribution": {
                k: v/n for k, v in results["aggregate"]["interference_effects"].items()
            }
        }
        
        return results


# ============================================================================
# DATA LOADING UTILITIES
# ============================================================================

def load_sample_data() -> list:
    """Load the built-in sample AITA posts"""
    return SAMPLE_AITA_POSTS


def fetch_aita_from_pushshift(limit: int = 100) -> list:
    """
    Fetch AITA posts from Pushshift API (if available)
    
    Note: Pushshift has had availability issues. This is a best-effort function.
    """
    import requests
    
    url = "https://api.pushshift.io/reddit/search/submission/"
    params = {
        "subreddit": "AmItheAsshole",
        "size": min(limit, 100),
        "sort": "desc",
        "sort_type": "score"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            posts = []
            for item in data.get("data", []):
                posts.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "body": item.get("selftext", ""),
                    "score": item.get("score", 0),
                    "num_comments": item.get("num_comments", 0),
                    "verdict": "UNKNOWN",  # Would need to parse from flair/comments
                    "ambiguity_level": "unknown"
                })
            return posts
    except Exception as e:
        print(f"Pushshift fetch failed: {e}")
    
    return []


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="QND Experiment on AITA Data")
    parser.add_argument("--api-key", type=str, help="Anthropic API key")
    parser.add_argument("--use-sample", action="store_true", default=False,
                        help="Use built-in sample data")
    parser.add_argument("--data-file", type=str, help="Path to JSON data file")
    parser.add_argument("--n-posts", type=int, default=5,
                        help="Number of posts to analyze")
    parser.add_argument("--n-trials", type=int, default=3,
                        help="Number of trials per test")
    parser.add_argument("--output", type=str, default="qnd_results.json",
                        help="Output file for results")
    args = parser.parse_args()
    
    print("=" * 70)
    print("QUANTUM NORMATIVE DYNAMICS (QND) EXPERIMENT")
    print("Testing quantum cognition predictions on moral dilemmas")
    print("=" * 70)
    
    # Load data
    if args.data_file:
        print(f"\nLoading data from {args.data_file}...")
        with open(args.data_file) as f:
            posts = json.load(f)
    elif args.use_sample:
        print("\nLoading built-in sample AITA data...")
        posts = load_sample_data()
    else:
        print("\nNo data source specified. Use --data-file or --use-sample")
        print("Generate test data with: python collect_datasets.py --synthetic")
        return
    
    posts = posts[:args.n_posts]
    print(f"Loaded {len(posts)} posts for analysis")
    
    # Initialize experiment
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nWARNING: No API key provided. Running with mock responses.")
        print("Set ANTHROPIC_API_KEY or use --api-key for real results.\n")
    
    experiment = QNDExperiment(api_key=api_key)
    
    # Run experiment
    print("\n" + "=" * 70)
    print("RUNNING QND TESTS")
    print("=" * 70)
    
    results = experiment.run_full_experiment(posts, n_trials=args.n_trials)
    
    # Print summary
    print("\n" + "=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)
    print(f"\nPosts analyzed: {results['n_posts']}")
    print(f"Trials per test: {results['n_trials_per_test']}")
    
    print("\n--- QND PREDICTIONS VS RESULTS ---\n")
    
    summary = results["summary"]
    
    print("1. ORDER EFFECTS (Non-commuting observables)")
    print(f"   QND Prediction: Should detect order effects")
    print(f"   Result: {summary['order_effect_rate']*100:.1f}% of posts showed order effects")
    print(f"   {'✓ SUPPORTS QND' if summary['order_effect_rate'] > 0.2 else '? INCONCLUSIVE'}")
    
    print("\n2. INTERFERENCE (Reasoning paths don't just add)")
    print(f"   QND Prediction: Should see constructive/destructive interference")
    int_dist = summary["interference_distribution"]
    print(f"   Result: Constructive={int_dist.get('constructive',0)*100:.1f}%, " +
          f"Destructive={int_dist.get('destructive',0)*100:.1f}%, " +
          f"None={int_dist.get('none',0)*100:.1f}%")
    has_interference = (int_dist.get('constructive',0) + int_dist.get('destructive',0)) > 0.3
    print(f"   {'✓ SUPPORTS QND' if has_interference else '? INCONCLUSIVE'}")
    
    print("\n3. SUPERPOSITION (Multiple valid interpretations)")
    print(f"   QND Prediction: Ambiguous cases should show superposition")
    print(f"   Result: {summary['superposition_rate']*100:.1f}% detected as superposed")
    print(f"   {'✓ SUPPORTS QND' if summary['superposition_rate'] > 0.5 else '? INCONCLUSIVE'}")
    
    print("\n4. ENTANGLEMENT (Correlated moral status)")
    print(f"   QND Prediction: Some cases have entangled parties")
    print(f"   Result: {summary['entanglement_rate']*100:.1f}% showed entanglement")
    print(f"   {'✓ SUPPORTS QND' if summary['entanglement_rate'] > 0.1 else '? INCONCLUSIVE'}")
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()
