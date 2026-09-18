# Reply to IEEE Publications, file discrepancy notice of 2026-09-16

To: xea@ieee.org
Subject: TCSS-2026-03-0366 – corrected source and PDF files

Attachments:
- `TCSS-2026-03-0366_source.zip` (final_manuscript.tex, single file with the bibliography inline, plus the `figures/` folder it references)
- `TCSS-2026-03-0366_final_manuscript.pdf` (17 pages, built from that .tex with pdfLaTeX, black text only, no line numbers, no highlighting)

---

Dear IEEE Publications,

Thank you for the notice about TCSS-2026-03-0366, "Geometric Prediction of Economic Behavior: Cross-Domain Validation Across Game Theory and Prospect Theory."

The discrepancy came from the source file in the original package. I supplied a Word (.docx) copy that had been converted from the LaTeX source, and the PDF was produced from the LaTeX source directly, so the two did not correspond line for line.

Attached are the LaTeX source and the PDF built from it. The .tex file is self-contained apart from the five figure files in the enclosed figures folder, and it compiles with pdfLaTeX under the IEEEtran class. The PDF is the clean final version: black text throughout, no highlighting, no line numbers. Both files match the accepted version of the article as revised for the final submission. Please disregard the earlier .docx file.

Please let me know if anything further is needed.

Kind regards,

Andrew H. Bond
Department of Computer Engineering, San José State University
andrew.bond@sjsu.edu

---

## Record (not part of the email)

- 2026-09-16: IEEE reported "discrepancies between the source manuscript file and the author-supplied PDF" and asked for a source (.doc or .tex) and a clean PDF by email to xea@ieee.org.
- Diagnosis 2026-09-18: `final_manuscript.pdf` (built 2026-09-10 07:12 from `final_manuscript.tex`) contains no colored text, hyperlinks or line numbers (content streams scanned, 0 non-black colour operators). A fresh pdfLaTeX build of the committed .tex reproduces the shipped PDF text exactly (17 pages, 0 differing lines). The `.docx` committed in 718f4ca is a conversion: no running header, no "Fig. N"/"Table N" numbering, ~500 fewer words. It was the uploaded "source" and is the discrepancy.
- Package contents: the .tex as committed in f9b340d (unchanged since), the five referenced figure files, the shipped PDF. The zip and the renamed PDF are untracked copies for the email only.
