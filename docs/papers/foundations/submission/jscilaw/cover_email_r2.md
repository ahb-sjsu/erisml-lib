Subject: Revised manuscript — "The Legal Bond Index" (round 2)

Dear Sean,

Thank you — genuinely — for the editorial review. It is rare to get comments this
specific and this constructive, and I want you to know they materially changed the
paper rather than just polishing it.

Two of the review's methodological concerns turned out to be exactly right, and I
think it's worth saying so plainly. First, cross-race neighbourhoods are indeed
worse-matched than same-race ones; the new distance diagnostics, caliper analyses,
and matched specifications you suggested now quantify that, and the paper reports an
adjusted range (1.01–1.02 on the decile score) alongside the unadjusted index.
Second, the plain permutation test really was testing the wrong null: on
semi-synthetic race-blind data it false-fires 56% of the time. The conditional
randomization test the review pointed me toward is correctly calibrated, and the
headline race result survives it decisively (z = 5.0, global multiscale p = 0.001,
now at full sample size with 1,000 draws). The sex effect did not survive the
corrected inference, and the revision withdraws it explicitly.

Beyond that, I implemented every item: the title you suggested, the ground-truth
validation suite (all four conditions), matching-method robustness, the risk-category
corrections with raw disagreement rates at both the ≥5 and ≥8 thresholds, the
expanded doctrinal discussion (Washington v. Davis, McCleskey, Loomis, and the
risk-assessment literature), removal of the threshold ranges, the k-curve as the
primary result with a global multiscale test, and the smaller items (pointwise CI
labels, ties and neighbour reuse, recidivism and scale definitions, the reference
labels, and the Wilson-loop material moved to a brief author note).

The attached response letter walks through each point with section references. The
analysis pipeline was rebuilt end to end; a single seeded script reproduces every
number, table, and figure from the public ProPublica file, and the outputs are
bundled with the submission.

I believe the paper is considerably stronger — and more honest — for this round of
review, and I'm grateful for the care that went into it.

Attachments: revised manuscript (PDF), point-by-point response to the editorial
review, reproduction script and outputs.

Best regards,
Andrew

Andrew H. Bond
Department of Computer Engineering
San José State University
andrew.bond@sjsu.edu · ORCID 0009-0003-2599-6158
