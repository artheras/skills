---
name: aria-music-direction
description: >-
  Create rights-safe music direction and validation manifests for ARIA posters,
  reels, and short-form videos. Use when a user needs a soundtrack brief, music
  cue selection, music licensing or provenance record, mix plan, or soundtrack
  QA for an ARIA creative asset.
---

# ARIA Music Direction

Turn approved visual work into a rights-safe music brief and manifest. This skill
makes the music decision explicit; it does not supply an audio master, buy a
licence, or infer permission from a mood reference.

## Scope and boundaries

- Treat every catalogue entry as direction text, not as an audio asset or licence.
- Use only user-owned, commissioned, licensed, or explicitly approved music in a released edit.
- Do not copy tracks, samples, stems, or licence files into a deliverable without the user's confirmed rights. If rights are unclear, choose `no_music` or keep the work in draft.
- Use `minimal-editorial-poster` for a static visual anchor and `short-form-video-editing` for final edit, captions, and platform package.
- For finance, research, trading, macro, or crypto, keep music emotionally restrained; never imply certainty, urgency, return, or a buy/sell signal.
- Do not publish, purchase licences, access music accounts, or clear rights for the user.

## Required intake

1. Destination, duration, platform, audience, language, and visual treatment.
2. Narration, dialogue, ambient sound, and silence priority.
3. One usage mode: `no_music`, `original`, `licensed`, `commissioned`, or `user_supplied`.
4. Rights record: provider or owner, licence proof/location, territory, term, and named approver.
5. For finance: as-of timestamp, sources, disclosure, and named release approver.

## Workflow

### 1. Decide whether the edit needs music

Select `no_music` when narration, source clarity, live sound, or a serious research tone is primary. Record a concise reason; silence is a deliberate editorial choice, not a missing field.

### 2. Pick a direction, not a borrowed track

Use `assets/aria-cue-catalog.json` to select a mood and mix treatment. The cues name rhythm, energy and use cases only. They are not downloadable tracks and their `brief_only` status cannot be released.

### 3. Record rights before release

Create `music-cue-manifest.json` using `assets/music-cue-manifest.schema.json`. Use a concrete source and license proof reference. A released music edit must be `cleared` and have explicit human approval.

### 4. Define a restrained mix

- Voice-led explanation: begin around `-16 LUFS` integrated and duck music by `6–10 dB` under speech.
- Music-led social cut: begin around `-14 LUFS` integrated.
- Keep true peak at or below `-1 dBTP`; verify final loudness with the platform export.
- Use transitions and accents sparingly; finance clips should make chart labels and disclosure more prominent than the beat.

### 5. Produce handoff artifacts

Deliver a `music-brief.md`, a `music-cue-manifest.json` (or no-music decision), rights state, mix notes, and the usage note for captions/disclosure. Run `python scripts/music_manifest_gate.py --manifest path/to/music-cue-manifest.json`.

## Quality bar

- Music supports the message without claiming a market outcome.
- Every non-silent released edit has provenance, territory, term, clearance, and human approval.
- Original/user-supplied music still has an owner and usage permission documented.
- Caption timing and source/disclosure readability take priority over musical transitions.
