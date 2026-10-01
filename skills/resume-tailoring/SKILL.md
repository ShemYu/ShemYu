# Resume tailoring

Use this skill whenever an agent or tool produces a resume, one-pager, or JD-tailored variant from this repo. Canonical generation (`uv run python -m src.main`) does not call a model. This skill is the method for any tailored draft.

`career/**/*.md` is the wiki and graph. `text.en` / `text.ja` on a claim are the locked wording. `views/` only chooses which claims appear. `data/` is an old snapshot; do not tailor from it. Publication rules for the canonical pages also live in [`RESUME_STANDARD.md`](../../RESUME_STANDARD.md). Where this skill and that file disagree on a **public fact**, this skill wins.

Do not apply, submit, or send a resume on the owner's behalf. The owner reviews before any submission.

## Process

Read the job description first. Classify it on two scales. Never mix the scores.

- **A — agent engineering.** Agents, evaluation, RAG, failure modes.
- **B — skills carry-over.** Serving, API, deploy, infra, MLOps, production GenAI.

Check Japanese separately. Native or business-fluent Japanese is a hard exclude: stop and tell the owner. Japanese listed only as a plus is acceptable; note that it is a plus, not a match.

For each role, list candidate sentences from **that role's** claims that match the JD. If more than three match, rank them and keep the best three. If fewer than three match, fill from that same role's other experience. Never borrow a sentence from another job. Never invent filler to reach three.

Bullet 1 is the sentence most likely to make this JD's reader keep reading.

Role headline and role summary are real responsibilities. Reuse the approved sentence verbatim. Do not rephrase it to fit a JD. Only bullet selection and order change.

The Cookpad summary sentence always stays, including for platform-role JDs and on one-pagers. Two approved forms, and only these:

- **One-pager and any page that must not name the product.** `Develops a multimodal cooking coach that uses video and learner voice to identify where a cook is stuck and guide the next step.`
- **Detailed resume only.** `Develops Moment Coach AI, a multimodal cooking coach that uses video and learner voice to identify where a cook is stuck and guide the next step.`

The product name “Moment Coach AI” appears only on the detailed resume. Do not substitute the company slogan “Building AI that makes everyday life more joyful.”

After drafting, a hiring-manager-style reviewer (Vera) reviews the draft. Fix what she flags and resubmit until she passes it. Only then hand it to the owner.

Approved PDFs are archived to the owner's Google Drive folder `履歷/` as `<Company>-<variant>-<YYYYMMDD>.pdf`.

## Bullet shape

Every bullet has three beats: the problem solved (stated first and compellingly), then the technique or method, then the result. Include a number only when the source claim has that number. Starting with a verb is an example of a clear opening, not a hard rule.

Audience is peers and hiring managers in the field, not the general public.

- No metric without a source number.
- No component list without a problem and a result.
- No generic filler (`ensuring scalable and secure operations`).
- No invented purpose opener (`To X,`) that misstates why something was built.
- When a bullet has both an adoption fact and a metric, state them as separate facts. Do not write the metric as the cause of the adoption.
- Past roles use past tense. Cookpad is current.

Role-summary wording is reused verbatim from the approved resumes (`views/one-pager.yaml`, `views/detailed.yaml`, and the Cookpad sentences above). Do not rephrase a summary that already passed review.

Good — problem, method, result, and the number is on the claim:

> Built a multi-agent video-understanding system to identify cooking issues from video, improving dish coverage from 50% to 95% through iterative grounding, retrieval, and reasoning improvements.

Bad — the same result renamed, which this repo does not allow:

> Built a multi-agent video-understanding system to identify cooking issues from video, improving recall from 50% to 95%.

Good — adoption and the metric stay independent (Cathay RKB):

> Improved the regulatory agent's F1 from 0.67 to 0.89. Adopted by 2 of 5 subsidiaries.

Bad — the metric is written as the cause:

> Improved F1 from 0.67 to 0.89, resulting in adoption by 2 of 5 subsidiaries.

Bad — invented purpose. The claim is that the PoC was productionized on Databricks, not that it was built “to modernize compliance”:

> To modernize compliance, productionized the PoC as a Databricks deployment workflow.

Good — the locked Cathay sentence, with no invented purpose:

> With a data scientist, mapped the client's regulatory-comparison workflow in a workshop (legal and compliance participated) and selected it as the pilot; productionized the PoC as a Databricks deployment workflow, storing related data on the Databricks data layer per internal access rules.

Bad — a tool list and filler, with no problem and no result:

> Solutions deployed using Databricks workflows and AWS infrastructure, ensuring scalable and secure operations.

## Layout

A one-pager spends its space on the current and most recent roles (Cookpad, Cathay). Older roles (TripSaaS, research assistant, III intern) are one line each: title, company, dates, and at most a one-line summary.

Include a short Profile. It states the overlapping arc, and it is not rewritten per JD: the last four years of prototype-to-production (serving, APIs, deploy, MLOps) across financial services and consumer products, plus the last one to two years of multi-agent systems, RAG, and agent evaluation; owning AI systems end to end. The approved profile sentence already on `career/people/shem.md` and the view summaries is the wording to reuse. It says 6+ years. Do not change that count.

Use normal letter spacing in section headings. Letter-spaced headings like `P R O F E S S I O N A L` break ATS parsing. Do not insert spaces between letters, and do not set wide tracking on headings.

Length: one page for quick-fit roles; at most two pages for Staff or senior-ownership roles.

## Hard fact rules (public wording)

If a claim does not support a JD item, leave it off. Do not upgrade a claim to match the posting.

- **Cookpad result.** Public wording is `dish coverage 50%→95%`. Never call that result recall. Never publish `40%→95%`, `67.6%→83.0%`, or `53/56`. The fraction and the 15-case, 56-item ruler stay on internal notes (`cookpad-vu-ruler-note`).
- **Cathay dates and team.** Cathay ended 2026-01. Team size is `Led 4 full-time engineers (7 including contractors)`. Never write `coordinated 10` or a cross-functional 10. DOGI's contributor count is a different internal note, not the team size.
- **Cathay RKB PoC.** The PoC was built jointly by the owner and a data scientist. Public wording is `productionized the PoC`. Never `the data scientist's PoC` or `DS built the PoC`, and never imply the owner built it alone.
- **English.** `Professional Working` (owner decision 2026-09-28). Public skill title is `English (Professional Working)`. Do not write `Limited Working`.
- **Experience.** `6+ years`, never `7+`.
- Do not mention LiteLLM.
- Do not write `distributed AI Gateway`. `AI Gateway` on the Cathay platform claims is the allowed name.
- Do not claim JD items the claims do not support.

## Counterexample

A one-page resume produced outside this method (not stored in the repo) shows the failures to avoid:

- Section headings were letter-spaced (`P R O F E S S I O N A L E X P E R I E N C E`), which breaks ATS.
- The Cookpad summary was the company slogan, not the cooking-coach sentence.
- TripSaaS, the research assistant role, and the III internship each received full bullets. On a one-pager those are one line.
- There was no Profile stating the prototype-to-production arc.
- Cathay said `DS built the PoC`.
- A Cathay bullet ended in `ensuring scalable and secure operations`.
- Another bullet listed video-infrastructure components with no problem and no result.
- Dish coverage `50%→95%` was missing, so the page spent its Cookpad space on an inventory.
