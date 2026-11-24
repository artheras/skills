# Platform delivery specifications

## Baseline exports

| Destination | Canvas | Primary ratio | Notes |
| --- | --- | --- | --- |
| Douyin | 1080 x 1920 | 9:16 | The workflow's default. Captions must be burned in — a subtitle track is not displayed. Lower-right UI is dense; keep the CTA left of it. |
| TikTok | 1080 x 1920 | 9:16 | Keep captions and CTA clear of lower controls. Burn captions in. |
| Bilibili | 1080 x 1920 vertical, or 1920 x 1080 | 9:16 or 16:9 | Vertical for the Story feed, landscape for the main site. Pick one and state it; they are different cuts, not one export. |
| Xiaohongshu | 1080 x 1920 | 9:16 | Use a legible opening frame and restrained text density. |
| Instagram Reels | 1080 x 1920 | 9:16 | Keep essential text in the central safe area. |
| YouTube Shorts | 1080 x 1920 | 9:16 | Make the first frame understandable without a title card. |
| X feed | 1920 x 1080 or 1080 x 1080 | 16:9 or 1:1 | Choose based on the accompanying post and chart legibility. |
| LinkedIn | 1920 x 1080 or 1080 x 1080 | 16:9 or 1:1 | Prefer an accessible, professional pace and explicit sources. |

Use H.264 MP4 unless the distribution channel explicitly asks for another codec. Keep a
platform-specific source of truth for current upload limits; those limits change more
often than the layout baseline above.

## Safe areas and captions

- For 1080 x 1920, reserve roughly 180 px at the top and 260 px at the bottom for
  platform UI, captions, and calls to action. Verify the final export in the destination app.
- Use at most two caption lines. Keep each line concise enough to be read in its display
  duration, then review without sound.
- At 1080-wide vertical exports, start around 46 to 60 px for captions and tune for the
  actual font, language, and contrast.
- Do not cover a chart axis, source label, or a key visual with a subtitle.
- Burned-in captions need an ffmpeg built with libass. Without it the workflow
  embeds a selectable subtitle track and says so in the `captions_burned_in`
  check — which the Chinese and short-form platforms above will simply not show,
  so for them that check failing is a release blocker rather than a note.

## Audio and watermark rules

- Only use audio that is original, licensed, or supplied by the platform under its own
  terms.
- Do not recycle an export with another platform watermark.
- Deliver a clean master, a captioned master when requested, and a source list.
