# Imagery direction

Choosing the *kind* of imagery is the decision that matters. A beautifully
executed photograph is still wrong on a product whose direction called for flat
illustration, and no amount of retouching fixes that.

## Match the kind to the direction

| If the style direction is… | Imagery that fits | Imagery that fights it |
| --- | --- | --- |
| Minimalism / Swiss / Exaggerated Minimalism | One large photo with real negative space, or nothing at all | Busy collages, decorative spot illustrations, stock gradients |
| Glassmorphism / Aurora / Liquid Glass | Vivid abstract gradients and blurred color fields *behind* the glass layer | Literal photography behind glass — detail turns to mud under blur |
| Neumorphism / Soft UI / Claymorphism | Soft 3D objects, rounded icon-like renders | High-contrast photography, sharp line art |
| Brutalism / Neubrutalism | Raw, unretouched photos; harsh crops; visible halftone | Polished corporate stock, soft gradients |
| Flat Design / Vibrant & Block-based | Flat vector illustration with the palette's colors | Photorealistic 3D, drop-shadowed realism |
| 3D & Hyperrealism / Spatial UI | Rendered 3D product/objects, depth and real lighting | Flat 2D spot illustration |
| Data-Dense / Financial / Executive Dashboard | Almost none — charts *are* the imagery | Decorative hero photos taking space from data |
| Dark Mode (OLED) / Cyberpunk / HUD | Imagery shot or rendered dark, with emissive accents | Bright white-background product shots punching holes in the UI |
| Organic Biophilic / Biomimetic | Natural textures, plants, real materials | Synthetic gradients, geometric abstraction |
| Editorial / Storytelling-Driven | Documentary photography, consistent grade across the set | Mixed sources with clashing color temperature |

**The consistency rule that outranks all of the above:** every image in one
interface should look like it came from one source. Mixed color temperature,
inconsistent grain, and clashing crops read as "assembled from whatever was
available" no matter how good each individual image is.

## Keeping generated images on-palette

Generated imagery drifts off-palette unless the palette is stated in the
prompt. Put the actual hex values in — a color name is not specific enough,
and near-but-not-quite is more jarring than plainly different.

A prompt that holds its direction names, in this order:

1. **Kind and treatment** — "flat vector illustration", "documentary
   photograph", "soft 3D render"
2. **Subject**, specific to this product — not "business people"
3. **Palette**, by hex — "limited palette: #0891B2, #ECFEFF, #164E63"
4. **Composition**, including where the empty space goes if text will sit on
   it — "wide, subject on the right third, flat empty space on the left"
5. **Negative constraints** — what it must not become

Example for a healthcare booking site (Healthcare App palette):

```
flat vector illustration, a calm empty clinic waiting room with soft daylight,
limited palette: #0891B2 primary, #ECFEFF background, #164E63 for line work,
wide composition with the room on the right and open background on the left for
a headline, no text in the image, no gradients, not photorealistic,
not corporate stock photography
```

Then check the result against the palette before shipping it — generation is
approximate, and one drifted image undoes the palette work.

## Backend choice

Inside Aria Code's own chat loop the local backend is called as
`generate_image` / `edit_image`; the names below are the MCP tool names an
external client sees. The paid OpenAI backend is MCP-only.

- **`aria.report.generate_image_local`** (SDXL-Turbo, free, local): abstract
  backgrounds, textures, gradient fields, light restyling of an existing photo.
  It is a 4-step distilled model — it will not follow an aggressive
  restructuring instruction, and **it cannot render legible text**. Do not ask
  it for anything containing words.
- **`aria.report.generate_image`** (OpenAI `gpt-image-1`, paid): flat/graphic
  illustration, precise instruction-following, and the only one of the two that
  renders text legibly. Costs real money per call, so it requires
  `confirmed: true` — call `aria.report.estimate_image_cost` first and tell the
  user the number.

For turning an existing user photo into on-direction art, the
`aria.report.edit_image` / `aria.report.edit_image_local` variants (or
`edit_image` in Aria's chat loop) take the photo as the starting point.

## When generating is the wrong call

- **Real people for testimonials, team pages, or reviews.** A generated
  "customer" presented as real is a misrepresentation. Ask for real photos, or
  use an obvious illustration/monogram avatar that is not pretending.
- **Real places, products, or premises.** A generated storefront for an actual
  restaurant is a fabricated depiction of a real business.
- **Anything needing photojournalistic credibility.**
- **Logos and brand marks** — see the main skill; use Simple Icons or ask for
  the user's file.
- **Precise text inside the image.** Even the stronger backend is unreliable
  here, and rendered text cannot be translated, selected, or read by a screen
  reader. Put text in HTML on top of the image instead.

## Practical notes

- Generate at the aspect ratio you will actually use. Cropping a square hero
  to 21:9 later destroys the composition you approved.
- Empty space in the image is not wasted — it is where the headline goes.
  Ask for it explicitly.
- For dark UIs, generate dark. Brightening a light image in CSS produces grey,
  not black.
- Keep the prompt that produced each accepted image. Regenerating a matching
  second image later is only possible if you still have the first prompt.
