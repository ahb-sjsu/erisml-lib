# erisml-lib Improvement Tasks

**Current Status:** GLASS HOUSE (Simple but fragile)  
**Goal:** Move to BUNKER (Simple and resilient)  
**Generated:** 2025-12-30

---

## Summary

| Metric | Current | Target |
|--------|---------|--------|
| Quadrant | GLASS HOUSE | BUNKER |
| Resilience Score | 46/100 | 60+ |
| Shield Rating | BRONZE | STEEL |
| Complexity Risk | MEDIUM | MEDIUM (maintain) |
| Smell Score | 43/100 | 25 or lower |

---

## 🚨 P0: Critical (Do This Week)

### Task 1: Add Timeouts to All HTTP/Network Calls
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Score:** 2/100

The #1 cause of cascading failures. Network calls without timeouts can hang forever.

**Files to audit:**
- [ ] All files using `requests`, `httpx`, `urllib`, or `aiohttp`
- [ ] Any database connections
- [ ] Any external API calls

**Implementation:**
```python
# Before (bad)
response = requests.get(url)

# After (good)
response = requests.get(url, timeout=(5, 30))  # 5s connect, 30s read

# Or with httpx
client = httpx.Client(timeout=httpx.Timeout(connect=5.0, read=30.0))
```

**Definition of Done:**
- [ ] Every HTTP call has explicit timeout
- [ ] Default timeout constants defined in config
- [ ] Timeout score reaches 50+

---

## ⚠️ P1: High Priority (This Sprint)

### Task 2: Fix Bare Except Clauses
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Files with issues:** 6 occurrences

Bare `except:` catches everything including `KeyboardInterrupt` and `SystemExit`.

**Files to fix:**
- [ ] `qnd_aita_experiment.py` (lines 449, 458, 545)
- [ ] `qnd_aita_experiment2.py` (lines 449, 458, 545)

**Implementation:**
```python
# Before (bad)
try:
    risky_operation()
except:
    pass

# After (good)
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # handle appropriately
```

**Definition of Done:**
- [ ] Zero bare except clauses
- [ ] All exceptions logged with context
- [ ] Error handling score reaches 60+

---

### Task 3: Add Retry Logic for External Calls
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Score:** 0/100

Transient failures (network blips, rate limits) are common. Retry with backoff.

**Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_external_api():
    response = requests.get(url, timeout=(5, 30))
    response.raise_for_status()
    return response.json()
```

**Definition of Done:**
- [ ] `tenacity` added to requirements.txt
- [ ] All external API calls wrapped with retry
- [ ] Retry score reaches 40+

---

### Task 4: Refactor High-Complexity Hotspots
**Owner:** _______________  
**Status:** ⬜ Not Started

These files have dangerously high complexity:

| File | Cyclomatic | Maintainability | Nesting |
|------|------------|-----------------|---------|
| `qnd_real_experiment.py` | 13.2 | 38.8 | 5 |
| `analyze_qnd_results_crash.py` | 11.2 | 32.6 | 5 |
| `bond_index_llm_evaluation.py` | - | 6.8 | 8 |

**For each file:**
- [ ] Extract functions >50 lines into smaller functions
- [ ] Reduce nesting by early returns
- [ ] Add docstrings

**Example refactor:**
```python
# Before (deeply nested)
def process():
    if condition1:
        if condition2:
            if condition3:
                do_thing()

# After (early returns)
def process():
    if not condition1:
        return
    if not condition2:
        return
    if not condition3:
        return
    do_thing()
```

**Definition of Done:**
- [ ] All files under cyclomatic complexity 10
- [ ] All files above maintainability index 40
- [ ] Max nesting depth 4

---

## 📋 P2: Medium Priority (Next Sprint)

### Task 5: Replace Print Statements with Proper Logging
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Count:** 30 print-based logging instances

**Implementation:**
```python
# Before
print(f"Processing {item}")
print(f"Error: {e}")

# After
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing {item}")
logger.error(f"Error: {e}", exc_info=True)
```

**Definition of Done:**
- [ ] Zero print statements used for logging
- [ ] Structured logging configured
- [ ] Observability score reaches 70+

---

### Task 6: Extract Magic Numbers to Constants
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Count:** 29 magic numbers

**Files to audit:** All Python files

**Implementation:**
```python
# Before
if score > 0.85:
    return "pass"
time.sleep(30)

# After
PASS_THRESHOLD = 0.85
RETRY_DELAY_SECONDS = 30

if score > PASS_THRESHOLD:
    return "pass"
time.sleep(RETRY_DELAY_SECONDS)
```

**Definition of Done:**
- [ ] All numeric literals >1 extracted to named constants
- [ ] Constants documented with units where applicable

---

### Task 7: Reduce Deep Nesting
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Count:** 4,427 deep nesting occurrences

**Worst offenders:**
- `bond_index_llm_evaluation.py` (8 levels)
- `collect_datasets.py` (8 levels)
- `bond_index_calibration_deme_fuzzing.py` (8 levels)

**Techniques:**
1. Early returns / guard clauses
2. Extract nested logic to helper functions
3. Use comprehensions instead of nested loops

**Definition of Done:**
- [ ] No function exceeds 4 levels of nesting
- [ ] Deep nesting count under 500

---

## 📝 P3: Low Priority (Backlog)

### Task 8: Add Circuit Breakers for External Dependencies
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Score:** 25/100

Prevent cascading failures when external services are down.

```python
import pybreaker

external_api_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30
)

@external_api_breaker
def call_external_service():
    return requests.get(url, timeout=(5, 30))
```

---

### Task 9: Break Up Long Functions
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Count:** 52 very long functions

Target: No function over 50 lines.

---

### Task 10: Update Deprecated APIs
**Owner:** _______________  
**Status:** ⬜ Not Started  
**Current Count:** 52 deprecated API usages

Run a deprecation audit and update to modern equivalents.

---

## 📊 Progress Tracking

| Week | Resilience | Complexity | Smell | Quadrant |
|------|------------|------------|-------|----------|
| Baseline | 46 | 60 | 43 | GLASS HOUSE |
| Week 1 | | | | |
| Week 2 | | | | |
| Week 3 | | | | |
| Week 4 | | | | |

**Re-run analysis:**
```bash
python prometheus.py ahb-sjsu/erisml-lib --html progress-report.html
```

---

## Quick Wins Checklist

These can be done in <1 hour each:

- [ ] Add `timeout=` to 5 most critical API calls
- [ ] Fix the 6 bare except clauses
- [ ] Add `tenacity` to requirements.txt
- [ ] Replace 10 print statements with logging
- [ ] Extract 5 obvious magic numbers to constants

---

## Resources

- [Tenacity Retry Library](https://tenacity.readthedocs.io/)
- [PyBreaker Circuit Breaker](https://github.com/danielfm/pybreaker)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Refactoring Guru - Code Smells](https://refactoring.guru/refactoring/smells)

---

*Generated by Prometheus Fitness Analyzer*
