Job Match Parsing Test Data

Contents
- cv/: three mock CV PDFs plus one ground-truth TXT file per CV.
- jd/: three mock job-description TXT files plus one ground-truth TXT file per JD.

Difficulty
- #1 = easy: explicit sections and directly stated facts/requirements.
- #2 = medium: relevant information is distributed across prose, experience, and summary sections; optional requirements use varied wording.
- #3 = hard: denser structure, information distributed across sections, conventional two-column CV layout, and requirements embedded in narrative text. It is intentionally challenging but not adversarial.

Ground-truth conventions
- CV technical skills include technologies explicitly mentioned anywhere in the CV, not only in a dedicated skills section.
- JD ground truth separates Mandatory and Optional requirements within the requested categories.
- In JDs, wording such as "is a plus", "preferred", "nice to have", "bonus points", "helpful", or "not required" is treated as optional.
- Ground truth contains only information supported by the corresponding mock document; it does not infer unstated skills or qualifications.
