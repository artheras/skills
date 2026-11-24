# Shot motion

The renderer animates **still images** (Ken Burns). Four moves exist, and a beat has
exactly one:

| Move | What it does | Use it for |
| --- | --- | --- |
| `zoom_in` | Pushes slowly into the frame | Arriving at a detail; the hook |
| `zoom_out` | Pulls back to reveal context | A close; showing the whole after the part |
| `pan_left` / `pan_right` | Drifts across the frame | Wide material that does not fit the crop |

Rules the renderer enforces, so plan inside them:

- One move per beat, 2–6 seconds. Under two seconds a move reads as a glitch; over six
  it reads as a stall.
- The same asset may appear in at most two consecutive beats, and the second must use a
  different move. Repeating an image with the same move is what makes a video look like
  a slideshow of one picture.
- Direction should follow the material. Panning away from the subject, or zooming out of
  an already wide frame, spends time without showing anything new.

## Motion that is not a camera move

`source=animate` is different: it hands one of the user's own images to Veo and asks for
real movement inside it — a person's gesture, water, smoke, a camera push with parallax.
The image is the starting frame and its content is kept; `generate_prompt` describes only
the motion, never new subject matter. It is billed per second, needs `allow_generation`,
and no single generated or animated shot may run longer than 8 seconds.

Reach for it when a still genuinely cannot carry the beat. A zoom is free and usually
enough.

## Restraint

- Keep decorative transitions to two or fewer in a short video.
- Hold a chart or dense frame long enough to read its title, scale, source, and the
  change being pointed at. Motion that outruns reading is motion that hid the evidence.
- Never use motion to manufacture urgency around a number someone might act on — a
  price, a result, a risk, a deadline. This is a rule about honesty, not pace, and it
  applies wherever being wrong costs the viewer something; financial content is only
  its strictest case.
