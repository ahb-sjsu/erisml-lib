"""
Recover N-body Mermin test results from the Anthropic batch API.

The original analysis failed because qnd_nbody_results.json contains IDs from
a different experiment (order_harm_intent_* format) instead of the N-body IDs
(nb_life_4_* format). The batch still exists and results can be re-retrieved.

Usage:
    export ANTHROPIC_API_KEY=your_key
    python recover_nbody_results.py
"""

import json, os, sys

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)

BATCH_ID = "msgbatch_01DEzJbQtaRV1H2LEXyypBhD"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "qnd_nbody_results")
SPECS_FILE = os.path.join(RESULTS_DIR, "specs_20251231_005229.json")
RAW_FILE = os.path.join(RESULTS_DIR, f"{BATCH_ID}_raw.json")

def main():
    client = anthropic.Anthropic()

    # 1. Check batch status
    print(f"Checking batch {BATCH_ID}...")
    batch = client.messages.batches.retrieve(BATCH_ID)
    print(f"  Status: {batch.processing_status}")
    print(f"  Created: {batch.created_at}")
    print(f"  Counts: {batch.request_counts}")

    if batch.processing_status != "ended":
        print(f"  Batch not complete (status: {batch.processing_status})")
        return

    # 2. Load specs
    with open(SPECS_FILE, "r") as f:
        specs_list = json.load(f)
    specs_map = {s["custom_id"]: s for s in specs_list}
    print(f"  Loaded {len(specs_map)} specs")

    # 3. Retrieve all results
    print("  Retrieving results...")
    raw_results = []
    success = 0
    errors = 0

    for result in client.messages.batches.results(BATCH_ID):
        cid = result.custom_id
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            raw_results.append({"custom_id": cid, "text": text})
            success += 1
        else:
            raw_results.append({"custom_id": cid, "error": str(result.result)})
            errors += 1

    print(f"  Retrieved: {success} successes, {errors} errors")

    # 4. Save raw results
    with open(RAW_FILE, "w") as f:
        json.dump(raw_results, f, indent=2)
    print(f"  Saved raw results to {RAW_FILE}")

    # 5. Parse verdicts
    import re
    parsed = []
    parse_errors = []

    for item in raw_results:
        cid = item["custom_id"]
        if "error" in item:
            parse_errors.append(cid)
            continue

        text = item["text"]
        # Try JSON parse
        verdict = None
        try:
            # Strip markdown code fences
            clean = re.sub(r"```json\s*", "", text)
            clean = re.sub(r"```\s*", "", clean)
            data = json.loads(clean)
            verdict = data.get("verdict", "").upper()
        except:
            # Regex fallback
            m = re.search(r'"verdict"\s*:\s*"(GUILTY|NOT_GUILTY)"', text, re.IGNORECASE)
            if m:
                verdict = m.group(1).upper()

        if verdict in ("GUILTY", "NOT_GUILTY"):
            parsed.append({
                "custom_id": cid,
                "verdict": -1 if verdict == "GUILTY" else 1,
                "spec": specs_map.get(cid, {})
            })
        else:
            parse_errors.append(cid)

    print(f"  Parsed: {len(parsed)} verdicts, {len(parse_errors)} parse errors")

    # 6. Save parsed results
    output_file = os.path.join(RESULTS_DIR, "qnd_nbody_results_recovered.json")
    with open(output_file, "w") as f:
        json.dump({
            "batch_id": BATCH_ID,
            "total": len(raw_results),
            "parsed": len(parsed),
            "parse_errors": len(parse_errors),
            "results": parsed,
            "error_ids": parse_errors
        }, f, indent=2)
    print(f"  Saved parsed results to {output_file}")

    # 7. Basic Mermin analysis
    if parsed:
        print("\n=== Preliminary Mermin Analysis ===")
        from collections import defaultdict
        configs = defaultdict(list)
        for item in parsed:
            spec = item["spec"]
            if not spec:
                continue
            key = (spec.get("n_agents"), spec.get("template"), spec.get("topology"))
            configs[key].append(item["verdict"])

        for key, verdicts in sorted(configs.items()):
            n, template, topo = key
            mean_v = sum(verdicts) / len(verdicts) if verdicts else 0
            print(f"  {template} (n={n}, {topo}): {len(verdicts)} verdicts, mean={mean_v:.3f}")

if __name__ == "__main__":
    main()
