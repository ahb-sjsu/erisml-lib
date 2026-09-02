#!/usr/bin/env python3
"""The Hohfeld quarter-turn hunt (UNSEALED, exploratory).

Keystone status: the demonstrated Hohfeldian operations (correlative swap s,
deontic negation r^2) generate only V4; D4 (order 8) is posited, licensed only if
a quarter-turn r (O->C->L->N->O) is independently demonstrated as a normative
operation (formal/HohfeldV4.lean; CONCEPT_REGISTRY.md sec 1).

This cell hunts the quarter-turn in a language model's LEARNED REPRESENTATION.
The move: r has a direct pair corpus -- the 4-cycle. Fit rho(r) on cycle pairs
(O->C, C->L, L->N, N->O) exactly as rho(s) and rho(r2) are fitted on theirs, then
test the DIHEDRAL RELATIONS on held-out scenarios AND a held-out surface-template
family (fit on template family A, evaluate on family B -- so the maps must encode
jural structure, not wording):

  V4 sector (yardstick):  S.S ~ I,  R2.R2 ~ I,  [S,R2] ~ 0
  Rehabilitation tests:   R.R ~ R2   (the cycle squares to deontic negation)
                          R^4 ~ I
                          S.R.S ~ R^3     (dihedral conjugation)
  Non-abelian signature:  R(S(x)) -> target r(s(state)),  S(R(x)) -> s(r(state))
                          -- e.g. from O these differ: rs(O)=L vs sr(O)=O.

Every relation is graded as held-out prediction: compose the fitted maps, compare
to the model's ACTUAL representation of the D4-predicted target statement for the
same scenario. Errors are normalized (1 = predicting the target by the source
representation unchanged; 0 = perfect). The V4 relations' own errors are the
yardstick: the quarter-turn is "found" only if the D4 relations hold at errors
comparable to the measured V4 sector, out-of-sample in scenario AND template.

Substrate: Qwen2.5-0.5B (CPU), layers {12, 18}; 1600 scenarios x 4 positions x
2 template families. Statements are auto-generated jural templates -- a
limitation (template English, not court prose), disclosed.
"""
import itertools
import json
import os
import numpy as np

HERE = os.path.expanduser("~/hohfeld-hunt")
CACHE = os.path.join(HERE, "states.npz")
MODEL = "Qwen/Qwen2.5-0.5B"
LAYERS = [12, 18]
BATCH = 32
SEED = 0
RIDGE = 1e-2

AGENTS = ["Avery", "Blake", "Casey", "Devon", "Emery", "Finley", "Gray", "Harper",
          "Indigo", "Jules", "Kai", "Logan", "Mika", "Noor", "Oakley", "Parker",
          "Quinn", "Reese", "Sasha", "Tatum", "Uma", "Vale", "Wren", "Xen",
          "Yael", "Zion", "Ari", "Bell", "Cruz", "Dana", "Eli", "Fern",
          "Gale", "Hollis", "Iris", "Jem", "Kit", "Lane", "Marlow", "Nova"]
ACTIONS = ["deliver the report", "repay the loan", "water the garden",
           "sign the contract", "return the car", "share the data",
           "repair the fence", "teach the lesson", "clean the office",
           "provide the records", "refund the deposit", "maintain the road",
           "disclose the defect", "ship the parts", "translate the document",
           "host the meeting", "audit the accounts", "renew the license",
           "store the equipment", "publish the results", "guard the entrance",
           "test the samples", "update the registry", "archive the files",
           "inspect the bridge", "supply the materials", "escort the visitor",
           "certify the scales", "label the products", "log the transactions",
           "notify the tenants", "post the schedule", "prune the orchard",
           "restock the shelves", "settle the invoice", "tune the engine",
           "verify the identity", "weld the frame", "wrap the shipment",
           "zone the parcel"]

# Template families: same jural content, different surface. Fit on A, eval on B.
TEMPLATES = {
    "A": {
        "O": "{A} must {act} for {B}.",
        "C": "{B} is entitled to have {A} {act}.",
        "L": "{A} is free not to {act} for {B}.",
        "N": "{B} has no claim that {A} {act}.",
    },
    "B": {
        "O": "{A} has a duty to {B} to {act}.",
        "C": "{B} holds a claim against {A} that {A} {act}.",
        "L": "{A} is under no duty to {B} to {act}.",
        "N": "{B} cannot demand that {A} {act}.",
    },
}
STATES = ["O", "C", "L", "N"]
# D4 action on states (index 0..3 = O,C,L,N per the Lean encoding)
S_MAP = {"O": "C", "C": "O", "L": "N", "N": "L"}      # correlative swap
R2_MAP = {"O": "L", "L": "O", "C": "N", "N": "C"}     # deontic negation
R_MAP = {"O": "C", "C": "L", "L": "N", "N": "O"}      # posited quarter-turn


def scenarios():
    rng = np.random.default_rng(SEED)
    combos = list(itertools.product(range(len(AGENTS)), range(len(ACTIONS))))
    rng.shuffle(combos)
    out = []
    for ai, ci in combos[:1600]:
        A = AGENTS[ai]
        B = AGENTS[(ai + 7) % len(AGENTS)]
        out.append((A, B, ACTIONS[ci]))
    return out


def gen_texts(scen):
    texts, index = [], {}
    for si, (A, B, act) in enumerate(scen):
        for fam in ("A", "B"):
            for st in STATES:
                index[(si, fam, st)] = len(texts)
                texts.append(TEMPLATES[fam][st].format(A=A, B=B, act=act))
    return texts, index


def forwards(texts):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(int(os.environ.get("HH_THREADS", "4")))
    tok = AutoTokenizer.from_pretrained(MODEL, padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(MODEL)
    model.eval()
    H = {L: [] for L in LAYERS}
    with torch.no_grad():
        for s in range(0, len(texts), BATCH):
            enc = tok(texts[s:s + BATCH], return_tensors="pt", padding=True,
                      truncation=True, max_length=32)
            o = model(**enc, output_hidden_states=True)
            for L in LAYERS:
                H[L].append(o.hidden_states[L][:, -1, :].float().numpy())
            if (s + BATCH) % 1600 == 0:
                print(f"    fwd {s+BATCH}/{len(texts)}", flush=True)
    return {L: np.concatenate(H[L]) for L in LAYERS}


def ridge_fit(X, Y, lam):
    d = X.shape[1]
    return np.linalg.solve(X.T @ X + lam * np.eye(d), X.T @ Y).T


def main():
    os.makedirs(HERE, exist_ok=True)
    scen = scenarios()
    texts, idx = gen_texts(scen)
    print(f"[hunt] {len(scen)} scenarios, {len(texts)} statements", flush=True)
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        H = {L: z[f"h{L}"] for L in LAYERS}
        print("[hunt] cache hit", flush=True)
    else:
        H = forwards(texts)
        np.savez(CACHE, **{f"h{L}": v for L, v in H.items()})

    n = len(scen)
    n_tr = int(0.7 * n)
    tr_s, te_s = range(n_tr), range(n_tr, n)
    results = {}

    for L in LAYERS:
        h = H[L].astype(np.float64)

        def vecs(sids, fam, st):
            return h[[idx[(i, fam, st)] for i in sids]]

        # fit maps on TRAIN scenarios, template family A
        def fit_map(mapping):
            X = np.vstack([vecs(tr_s, "A", st) for st in STATES])
            Y = np.vstack([vecs(tr_s, "A", mapping[st]) for st in STATES])
            return ridge_fit(X, Y, RIDGE * len(X))

        S = fit_map(S_MAP)
        R2 = fit_map(R2_MAP)
        R = fit_map(R_MAP)

        # held-out grading: TEST scenarios, template family B
        def err(M, mapping, note=""):
            """normalized held-out error of M as the map for `mapping`:
            pred = M h(x_st); target = h(mapping[st]); baseline = h(x_st) itself."""
            num = den = 0.0
            for st in STATES:
                X = vecs(te_s, "B", st)
                T = vecs(te_s, "B", mapping[st])
                num += ((X @ M.T - T) ** 2).sum()
                den += ((X - T) ** 2).sum()
            return float(num / den)

        def comp_err(Ms, mapping):
            """held-out error of the COMPOSITION (rightmost matrix applied first)
            against the caller-supplied state mapping's targets."""
            num = den = 0.0
            for st in STATES:
                X = vecs(te_s, "B", st)
                P = X
                for M in reversed(Ms):
                    P = P @ M.T
                T = vecs(te_s, "B", mapping[st])
                num += ((P - T) ** 2).sum()
                den += ((X - T) ** 2).sum()
            return float(num / den)

        I_MAP = {st: st for st in STATES}

        def chain(mdict_list):
            out = {}
            for st in STATES:
                cur = st
                for m in mdict_list:      # applied left-to-right textually
                    cur = m[cur]
                out[st] = cur
            return out

        row = {}
        # direct single-map quality (are these even good equivariances?)
        row["fit_S"] = err(S, S_MAP)
        row["fit_R2"] = err(R2, R2_MAP)
        row["fit_R"] = err(R, R_MAP)
        # V4 sector yardstick
        row["S.S=I"] = comp_err([S, S], I_MAP)
        row["R2.R2=I"] = comp_err([R2, R2], I_MAP)
        row["S.R2 -> sr2"] = comp_err([S, R2], chain([R2_MAP, S_MAP]))
        row["R2.S -> sr2"] = comp_err([R2, S], chain([S_MAP, R2_MAP]))
        # rehabilitation tests
        row["R.R=R2"] = comp_err([R, R], R2_MAP)
        row["R^4=I"] = comp_err([R, R, R, R], I_MAP)
        R3_MAP = chain([R_MAP, R_MAP, R_MAP])
        row["S.R.S=R^3"] = comp_err([S, R, S], R3_MAP)
        # non-abelian signature (different targets from the same source)
        row["R.S -> rs"] = comp_err([R, S], chain([S_MAP, R_MAP]))   # s first
        row["S.R -> sr"] = comp_err([S, R], chain([R_MAP, S_MAP]))   # r first
        # cross-check: does R.S wrongly hit sr targets (it shouldn't if non-abelian
        # structure is real)?
        row["R.S -> sr (WRONG tgt)"] = comp_err([R, S], chain([R_MAP, S_MAP]))

        results[str(L)] = {k: round(v, 4) for k, v in row.items()}
        print(f"\n=== layer {L} (0 = perfect, 1 = no better than identity) ===")
        for k, v in results[str(L)].items():
            print(f"  {k:24s} {v:7.3f}")

    json.dump(results, open(os.path.join(HERE, "hunt_result.json"), "w"), indent=2)
    print(f"\nwrote {HERE}/hunt_result.json")
    print("READ: quarter-turn is 'found' iff fit_R, R.R=R2, R^4=I, S.R.S=R^3 land at")
    print("errors comparable to the V4 yardstick rows, AND 'R.S -> rs' is much lower")
    print("than 'R.S -> sr (WRONG tgt)' (the non-abelian signature).")


if __name__ == "__main__":
    main()
