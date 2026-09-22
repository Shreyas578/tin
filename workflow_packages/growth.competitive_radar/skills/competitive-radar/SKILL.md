---
name: competitive-radar
description: Process internet signals, match against features, score leads, and generate Output A and Output B.
---

# Competitive Radar Instructions

You will receive an array of `signals` along with the founder's `core_features`, `keywords`, `icp`, `competitors`, `known_weaknesses`, `build_signal_threshold`, `recency_days`, and `historical_gaps` (an array of strings tracking previous counts, e.g. `["Notion Integration: 4"]`).

## Input Schema
Every signal in the array conforms exactly to this structure. Reference these exact fields in your outputs:
```json
{
  "id": "string",
  "layer": "1 | 2 | 3 | 4",
  "source": "reddit | hn | g2 | linkedin | ...",
  "author_name": "string",
  "author_profile": "string",
  "company": "string",
  "complaint_text": "string",
  "date": "ISO string",
  "engagement_count": "number",
  "url": "string"
}
```

Your job is to process these signals through a strict pipeline.

## Step 1: Pre-Filtering (Recency & ICP)
Before evaluating any signal, apply two strict filters:
1. **Recency Rule**: Is the `date` of the signal older than `recency_days`? If YES, discard the signal entirely. We only process fresh signals.
2. **ICP Filter**: Does the author's title, company, or context fit the Ideal Customer Profile (`icp`)? If NO, discard the signal entirely. 

If the signal survives both filters, proceed to Step 2.

## Step 2: Feature Match Check
Evaluate every remaining signal against the list of `core_features`. Use the `keywords` array to help identify if an unanswered question (Layer 3) is highly relevant to the problem space.
- Does the complaint or question describe a problem that is definitively solved by one of the `core_features`?
- **MATCH**: The feature exists completely. Note the specific feature matched.
- **NO MATCH**: The feature does not exist. Note the gap in capability.
- **AMBIGUITY RULE**: If a complaint only partially matches a feature, or if you are in doubt, **treat it as NO MATCH and log it.** Do not attempt a weak sell.

## Step 3: Scoring & Consolidation
Score each signal based on the following criteria:
- Active public complaint this week (Layer 1): +3
- Competitor bad review, recent and specific (Layer 2): +2
- Unanswered question, still active (Layer 3): +1
- Trigger event at their company (Layer 4, e.g. funding announcements on TechCrunch, new executive hires on LinkedIn, or negative review spikes): +3
- Direct feature match confirmed: +3
- **High Engagement Bonus**: If `engagement_count` > 10, add +1.

**Consolidation Rule**: If a single prospect appears in multiple layers (e.g., posted on Reddit and left a G2 review), consolidate all their signals into one single prospect entry. List each signal separately under their name, and **sum the score** across all of them. Add a **+2 bonus** for appearing in more than one layer.

## Step 4: Categorization & Capping
Divide the evaluated prospects into two buckets:
- **Strike Now**: Score >= 5. Sort descending by score. **CAP this list at the top 15 prospects maximum.** These are warm leads ready for immediate outreach.
- **Logged / Gap**: No feature match yet, regardless of score. These go into the feature gap tracker.

## Step 5: Generate Output A (Ranked Outreach List)
Format the "Strike Now" and "Logged" prospects exactly as follows:

```
STRIKE NOW (score 5+, capped at 15)

Prospect: [author_name] ([author_profile]), Title @ [company]
Score: [Total Score]
Signals:
  - [source, date]: "[complaint_text]" (Engagement: [engagement_count])
  - [List additional consolidated signals here if applicable]
Feature match: [Describe what they complained about]
→ [Your matching core feature]

Suggested opening:
"[Draft an opening line adhering STRICTLY to these constraints:
1. Reference their exact complaint, do not just paraphrase it.
2. NEVER mention your product name in the first sentence.
3. Keep it under 3 lines total.
4. Tone: direct, founder-to-founder, no salesy fluff.]"

---

LOGGED — NO FEATURE MATCH YET

PAYLOAD: 
[
  {"gap": "[Missing capability]", "author_name": "[author_name]", "company": "[company]", "source_url": "[url]"},
  ...
]
```

## Step 6: Generate Output B (Internal Intelligence Brief)
Aggregate the signals to produce strategic insights. 
**Threshold Memory Rule**: Sum the occurrences of a gap in the *current batch* with its historical count extracted from the `historical_gaps` strings. The format of these strings is strictly `Gap Name: integer` (e.g., `Notion Integration: 4`). Parse these carefully; if a string does not conform to this format or is unparseable, skip it and treat the historical count as 0. Use the cumulative sum to evaluate against the `build_signal_threshold`.
**Rule for Empty Sections**: If there are no signals supporting a section this week, omit that section entirely. Do not write "nothing this week."

```
WHAT TO EXPLOIT THIS WEEK:
[Identify a weakness in a competitor based on multiple Layer 2 or Layer 1 signals that matches a core feature. Suggest an action.]

WHAT TO COUNTER — 2 WEEK WINDOW:
[Identify a competitor move (Layer 4) and suggest a counter-measure.]

WATCH YOUR OWN BACK:
[Cross-reference incoming signals against the provided `known_weaknesses`. If a prospect complains about a problem that matches one of your known weaknesses, alert the founder here to fix it before it scales.]

BUILD SIGNALS — CROSSED THRESHOLD:
[List any gaps where (current batch occurrences + historical_gaps count) >= `build_signal_threshold`. Explicitly state the cumulative count.]

CONTENT GAP — WRITE THIS PAGE:
[List any unanswered questions (Layer 3) that appeared multiple times. Prioritize those with the highest `engagement_count`. Suggest a page title.]
```

Output your final response with Output A followed by Output B.
