---
name: short-form-video-editing
description: >-
  Turn approved footage, posters, charts, and image assets into a platform-ready
  short-form video package: edit plan, captions, publish copy, and delivery manifest.
  Use when creating social clips, product explainers, market recaps, or finance videos
  that need platform specifications, asset provenance, subtitle, and release checks.
---

# Short-form Video Editing

Create a production-ready edit package from approved assets. This skill specifies the
edit, subtitles, copy, and release checks; it does not publish content, handle account
credentials, or invent rights for a source asset.

## Scope and boundaries

Use this skill after the user has supplied or approved the source footage, charts,
images, poster artwork, brand copy, and destination platform.

- Use ui-asset-sourcing before selecting visual assets whose source or licence is unclear.
- Use minimal-editorial-poster when a static opening card, thumbnail, or campaign poster
  is needed.
- Use minimal-editorial-exports when the same visual system also needs a print or static
  export.
- Use aria-music-direction when a soundtrack needs a rights-safe cue brief, mix hand-off,
  or release manifest.
- Do not use unlicensed music, third-party clips, trademarks, screenshots, or market data
  without recording their source and usage rights.
- Do not upload, publish, execute trades, or expose brokerage, API, or personal data.

## Required intake

Collect the minimum information before producing the final package:

1. Objective, audience, platform, language, and call to action.
2. Approved assets with an owner, source URL or record, and usage rights.
3. Target format: vertical social, horizontal feed, or square feed.
4. Desired duration, style references, brand tokens, and narration.
5. Music mode: `no_music`, `original`, `licensed`, `commissioned`, or `user_supplied`.
   For music, identify the intended cue, clearance holder, territory, and term.
6. If financial content is present: as-of time, data sources, required disclosure, and
   named human approver for release.

If any required asset rights or financial source is missing, label the corresponding edit
beat as pending instead of treating it as ready.

## Workflow

### 1. Define the platform cut

Choose one primary cut before editing:

- TikTok, Xiaohongshu, Instagram Reels, and YouTube Shorts: 1080 x 1920, 9:16.
- X and LinkedIn: 16:9 or 1:1, selected from the publishing objective.

See references/platform-specs.md for safe-area and subtitle guidance. Produce a separate
manifest for each materially different crop, language, or platform claim.

### 2. Build a concise story

Use a three-beat outline unless the user asks for a different treatment:

1. Hook: establish the question, event, or visual change within two seconds.
2. Evidence: show the key proof, chart, product action, or source-backed explanation.
3. Close: state the qualified conclusion and a single call to action.

Keep decorative scene transitions to two or fewer. Favour cuts, restrained emphasis,
and readable charts over motion that competes with the data.

### 3. Produce the edit plan

Create edit-plan.json using assets/edit-plan.schema.json. For every beat record:

- Start and end time, purpose, visual asset, crop or motion instruction, and on-screen copy.
- Caption line or narration text.
- Source attribution placement when it is required.
- A pending flag for any missing approval, source, or asset licence.

Use references/motion-tokens.md for durations and motion restraint.

### 4. Direct music safely

If music is included, create `music-cue-manifest.json` using `aria-music-direction`.
Record the rights source, license evidence, territory, term, mix intent, and human
clearance before release. Voice-led market recaps may use `no_music`; record the
editorial reason in the delivery manifest.

### 5. Produce captions and publishing copy

Deliver both SRT and VTT captions. Keep captions to two lines, preserve sentence meaning,
and leave platform UI safe areas clear. Include:

- Primary post copy.
- One concise alternative hook.
- Alt text or an accessible visual description.
- Hashtags only when they serve discovery rather than pad the caption.

### 6. Apply financial-content guardrails

For market, investing, trading, macro, or crypto content:

- Include the data source and as-of time for every time-sensitive claim.
- Use the disclosure: “仅作信息展示，不构成投资建议。” or “Illustrative only. Not
  investment advice.” unless legal review supplies approved localized wording.
- Avoid guaranteed returns, urgency, personalised buy or sell recommendations, and
  unqualified performance claims.
- Never show account IDs, API keys, credentials, balances, order controls, or private
  portfolio data without explicit approved redaction.
- Require a named human approval before a finance video is marked `released`.

See references/financial-content-rules.md for the release checklist.

## Deliverable package

Return a folder containing:

- edit-plan.json
- captions.srt and captions.vtt
- publish-copy.md
- delivery-manifest.json
- music-cue-manifest.json when music is used
- source-notes.md
- approved media exports, or explicit placeholders for exports that still need rendering

Validate delivery-manifest.json before handoff:

    python3 scripts/video_delivery_gate.py --manifest delivery-manifest.json

The validator enforces output format, captions, asset and music provenance, financial
disclosures, and release approval. A draft may carry pending approval; released items may
not.

## Quality bar

The final package must feel intentional at muted autoplay:

- The first frame is recognizable without audio.
- The visual hierarchy prioritizes the claim, supporting data, then brand.
- Captions remain readable above platform controls.
- Music must be cleared and mixed below narration; transitions support, rather than obscure,
  source-backed information.
- Every factual financial statement can be traced back to a recorded source.
