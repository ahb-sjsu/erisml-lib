# The Bond Invariance Principle

## Andrew H. Bond, 2025

---

## The Principle

**An ethical judgment is valid only if it is invariant under all transformations that preserve the bonds.**

---

## Formal Statement

Let:
- **T** be an ethical tensor encoding agents, relationships, stakes, and context
- **B(T)** be the bond structure of T: the network of morally relevant relationships
- **G** be the group of bond-preserving transformations: {g : B(g·T) = B(T)}
- **𝒥** be any ethical judgment function (verdict, ranking, permission, constraint)

Then:

$$\boxed{\forall g \in G: \quad \mathcal{J}(T) = \mathcal{J}(g \cdot T)}$$

**If the bonds are unchanged, the judgment must be unchanged.**

---

## The Contrapositive (Accountability Form)

$$\mathcal{J}(T) \neq \mathcal{J}(T') \quad \Longrightarrow \quad B(T) \neq B(T') \;\;\text{or}\;\; \text{explicit change of normative lens}$$

**If your judgment changes, you must show what bond changed—or declare that you changed the rules.**

---

## What Counts as a Bond

A **bond** is a morally relevant relationship between entities:

| Bond Type | Example |
|-----------|---------|
| **Risk-bearing** | "A bears the risk of X for B" |
| **Obligation** | "A owes X to B" |
| **Responsibility** | "A is responsible for X" |
| **Authority** | "A has authority over B regarding X" |
| **Consent** | "A has consented to X" |
| **Role** | "A is B's physician / employer / guardian" |
| **Claim** | "A has a claim against B for X" |
| **Commitment** | "A has promised X to B" |
| **Dependency** | "A depends on B for X" |
| **Vulnerability** | "A is vulnerable to B regarding X" |

The bond structure **B(T)** is the complete set of such relationships encoded in the ethical situation T.

---

## What Transformations Are Bond-Preserving

A transformation g is **bond-preserving** if it changes only morally arbitrary features:

| Bond-Preserving (g ∈ G) | Not Bond-Preserving (g ∉ G) |
|-------------------------|------------------------------|
| Renaming agents | Changing who bears risk |
| Reordering presentation | Changing who has consented |
| Changing units | Adding or removing obligations |
| Equivalent descriptions | Altering role relationships |
| Syntactic reformulation | Shifting responsibility |
| Coordinate reparameterization | Breaking commitments |

**The test:** Does the transformation change who owes what to whom, who bears what risk, who has what claim? If no, it is bond-preserving. If yes, it is not.

---

## Three Forms of the Principle

### I. The Invariance Form
$$\forall g \in G: \quad \mathcal{J}(T) = \mathcal{J}(g \cdot T)$$
*Same bonds → same judgment.*

### II. The Accountability Form  
$$\mathcal{J}(T) \neq \mathcal{J}(T') \;\Longrightarrow\; B(T) \neq B(T') \;\lor\; \Delta\text{Lens}$$
*Different judgment → different bonds or declared lens change.*

### III. The Audit Form
$$\text{For any judgment } \mathcal{J}(T), \text{ it must be possible to exhibit:}$$
$$\text{(i) the bonds } B(T) \text{ on which it depends, and}$$
$$\text{(ii) a proof that } \mathcal{J} \text{ is constant on the orbit } G \cdot T$$
*Every judgment must be traceable to bonds and verifiably invariant.*

---

## The Diagnostic

A system violates the Bond Invariance Principle if:

1. **Judgment varies under relabeling** — changing names, order, or syntax changes the output
2. **Judgment depends on morally arbitrary features** — encoding choices, coordinate systems, unit conventions affect the result
3. **Judgment cannot be traced to bonds** — no explanation links the output to the morally relevant relationships
4. **Equivalent descriptions yield different verdicts** — "withhold treatment" vs. "allow natural death" produce different judgments despite identical bond structure

Any such violation indicates that the system is responding to **representation**, not **reality**.

---

## Why This Matters

### For AI Systems
An AI ethics module satisfies BIP if and only if its outputs depend solely on the morally relevant relationships in the situation, not on arbitrary features of how that situation is represented.

### For Human Reasoning  
A moral argument satisfies BIP if and only if its conclusion would survive any rephrasing that preserves the underlying moral relationships.

### For Institutions
A policy satisfies BIP if and only if its application is consistent across all presentations of morally equivalent cases.

---

## The Motto

$$\text{Bonds, not labels.}$$

$$\text{Structure, not syntax.}$$

$$\text{Relationships, not representations.}$$

---

## Citation

Bond, A.H. (2025). The Bond Invariance Principle. In *Tensorial Ethics: A Geometric Framework for Moral Philosophy*.

---

*The bonds are what matter.*

*If the bonds are the same, the judgment must be the same.*

*This is the Bond Invariance Principle.*

*It is the foundation of trustworthy ethical reasoning—human or machine.*
