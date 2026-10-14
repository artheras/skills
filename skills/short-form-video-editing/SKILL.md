---
name: short-form-video-editing
description: >-
  Turn a script and the user's own images or clips into a finished short-form
  video: an edit plan, narration, captions, the rendered file and its checks.
  Use when making social clips, product explainers, recaps, tutorials, or any
  video that needs platform specifications, asset provenance, and release checks.
---

# Short-form Video Editing

Make a video from material the user has supplied or approved. This skill plans the
edit, narrates it, renders it, and reports what it checked. It does not publish,
handle account credentials, or invent rights for a source asset.

## How this runs

Inside ARIA Desktop and Aria Code this is not a document-writing exercise: two
tools do the work, and they are offered in **Work** only, when the desktop
declares `client_capabilities.video_workflow`.

| Tool | What it does | Cost |
| --- | --- | --- |
| `video_plan` | Describes every asset, writes the edit plan (beats, narration, captions, camera moves). | Planner calls only; nothing is rendered |
| `video_render` | Narration, captions, the final file, and its checks. | TTS and encoding; Veo only if the plan contains generated shots |

**The order is fixed and the confirmation is not optional.** Call `video_plan`,
show the user the plan in a few lines, ask whether to render, and call
`video_render` only after they agree. A plan with generated shots makes the
desktop ask the user to confirm the cost before anything is billed; a refusal
comes back as the result, not as an error.

`video_plan` takes `script`, `assets`, `title`, and optionally `platform`,
`target_seconds`, `allow_generation`. `video_render` takes the same `title`.

Assets are paths relative to the connected project folder, or `attachment:1`,
`attachment:2` … in the original media attachment order — images and clips only,
not documents or connectors. Video preview frames are not separate assets.

Models: `gemini-3.8-flash` plans, `gemini-2.5-flash-tts` narrates,
`veo-3.1-fast-generate-001` generates shots when they are allowed and confirmed.

## Scope and boundaries

Use after the user has supplied or approved the source material and said where it
is going.

- Use `ui-asset-sourcing` before choosing visuals whose source or licence is unclear.
- Use `minimal-editorial-poster` for a standalone opening card, thumbnail, or poster.
- Use `aria-music-direction` when a soundtrack needs a rights-safe cue brief.
- Do not use unlicensed music, third-party clips, trademarks, screenshots, or data
  without recording where they came from and what rights apply.
- Do not upload, publish, or expose credentials, API keys, or personal data.

## Required intake

1. Objective, audience, platform, language, call to action.
2. Approved assets, each with an owner and a usage-rights record.
3. Target format: vertical, horizontal, or square.
4. Duration, style references, brand tokens, narration voice.
5. Music mode: `no_music`, `original`, `licensed`, `commissioned`, `user_supplied`.

If rights or a source are missing, mark the affected beat `pending` rather than
treating it as ready. `pending` means *the user must still supply or approve
something* — it is not a defect in the render, and a video can be complete and
still carry pending beats.

### When the content makes claims about the world

Market, health, legal, safety, and similar content carries one extra obligation:
every time-sensitive or factual claim names its source and its as-of time, and
nothing is promised that the material does not support. Finance has the strictest
form of this — see `references/financial-content-rules.md`, which also carries the
disclosure wording and the named-approver requirement before release. Apply the
same discipline to any domain where being wrong costs the viewer something.

## Workflow

### 1. Choose the platform cut

- Douyin, Xiaohongshu, TikTok, Reels, Shorts, Bilibili: 1080 x 1920, 9:16.
- X, LinkedIn, YouTube landscape: 16:9 or 1:1, chosen from the publishing objective.

See `references/platform-specs.md` for safe areas and subtitle placement. Produce a
separate plan for each materially different crop, language, or claim.

### 2. Build a concise story

Hook, evidence, close — unless the user asks for another treatment.

1. **Hook**: establish the question or visual change inside the first three seconds.
2. **Evidence**: the proof, product action, or source-backed explanation.
3. **Close**: the qualified conclusion and a single call to action.

### 3. Let the plan obey the rules the renderer enforces

`video_plan` applies these; a plan that breaks them is rejected and re-asked once,
so writing against them saves a round of paid calls:

- 2–6 seconds per beat, one idea each; beats are contiguous and total about
  `target_seconds`.
- Narration must fit its beat when spoken — roughly four Chinese characters per
  second. Captions are shorter than the narration.
- A shot taken from the material **names which asset** (`asset_id`). The same asset
  may be reused, but not for more than two consecutive beats, and with a different
  camera move.
- Use every supplied asset if there is room for it.
- `source=generate` only where material is genuinely missing; `source=animate` to put
  motion into one of the user's own images, keeping that image. Both are billed per
  second and need `allow_generation`.
- Do not invent data, prices, or promises.

`assets/edit-plan.schema.json` is the written form of this. It requires `asset_id`
for `asset` and `animate` beats, because a plan that omits it renders nothing.

### 4. Read what the render reports

`video_render` returns `status` plus a list of checks, and both matter:

| Check | Meaning |
| --- | --- |
| `duration`, `frame_size` | The file matches the plan and the platform |
| `audio`, `long_silence` | There is narration, and no dead air |
| `black_frames` | No blank stretches |
| `pending_beats` | Something awaits the user — rights, material, a fact |
| `captions_burned_in` | Whether captions are in the picture or only a track |

`rendered_with_issues` does **not** mean the file is broken. Say which check failed
and what it means for the user. A pending beat is a question for them; a failed
`frame_size` is a defect.

**Captions**: burning them into the picture needs an ffmpeg built with libass. Without
it the workflow embeds a selectable subtitle track instead and says so. Douyin,
TikTok and the rest do not display a subtitle track, so for those platforms burned-in
captions are a release requirement, not a preference.

## What the render writes

In the project folder:

- `edit_plan.json` — the plan, after validation
- `assets.json` — what each supplied asset is
- `<project>.mp4` — the video
- `subtitles.srt` — captions
- `narration.wav` and `narration/` — the spoken track, per beat
- `clips/` — the rendered shots
- `manifest.json` — duration, aspect, models used, checks, notes, pending beats

`manifest.json` is the record of the release. Its `notes` carry what the planner
wants the user to know — thin material, rights to clear — and they are worth
repeating to the user rather than leaving in the file.

## Before release

`manifest.json` records what was rendered. It does not record whether the video may
be published — who owns the material, whether the music is cleared, who approved it.
That is `delivery-manifest.json`, written against `assets/delivery-manifest.schema.json`
and checked by:

    python3 scripts/video_delivery_gate.py --manifest delivery-manifest.json

It enforces the output format for the destination, captions, asset and music
provenance, any required disclosure, and release approval. A `draft` may carry
pending approval; a `released` item may not.

Alongside it, keep `publish-copy.md` (post copy, one alternative hook, alt text) and
`source-notes.md` (where each asset came from and under what rights).

## Quality bar

The video must read at muted autoplay:

- The first frame is recognizable without sound.
- The hierarchy is claim, then support, then brand.
- Captions stay clear of platform controls.
- Music, if any, is cleared and mixed below the narration.
- Every factual statement traces back to a recorded source.
