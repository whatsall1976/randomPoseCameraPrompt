# Random Camera + Pose Prompt Composer

A small Python utility for composing image-generation prompts from independently randomized camera and pose fragments.

It reads a categorized JSON file, randomly selects one entry from each requested category, and joins the selected fragments into a single text prompt.

This is useful for generating controlled variations for tools such as ComfyUI, Stable Diffusion, FLUX, GPT Image, Grok Image, or any other text-to-image workflow.

---

## Files

The basic setup uses these two files:

```text
random_compose_prompt.py
camera_pose_categories_v2.json
```

By default, the script expects the JSON file at:

```text
/mnt/data/camera_pose_categories_v2.json
```

You can override this with `-json`.

---

## Categories

The JSON file contains eight independent fragment categories:

| ID | Category | Description |
|---:|---|---|
| 1 | `distance` | Camera-to-subject distance, such as close-up or long shot |
| 2 | `camera_angle` | Camera viewpoint, such as high-angle, low-angle, profile, POV |
| 3 | `lens_focal_length` | Lens / focal-length description, such as 24mm, 50mm, 85mm |
| 4 | `framing` | How much of the body is visible, such as shoulders-up or full-body |
| 5 | `overall_pose` | Main body pose, such as standing, sitting, leaning, walking, dancing |
| 6 | `hand_arm_expression` | Hand and arm position or gesture |
| 7 | `leg_pose` | Leg and foot position |
| 8 | `head_pose` | Head direction, tilt, and gaze |

---

## Basic Usage

Use `-fragments` to specify which categories should participate in the final prompt.

Example:

```bash
python random_compose_prompt.py -fragments 1,3,5
```

This means:

```text
1 = distance
3 = lens_focal_length
5 = overall_pose
```

Possible output:

```text
medium close-up, 85mm portrait lens, leaning against a wall
```

Each selected category contributes exactly one randomly chosen fragment.

---

## `-fragments`

Syntax:

```bash
-fragments 1,3,5
```

The values are comma-separated category IDs.

Examples:

```bash
python random_compose_prompt.py -fragments 1,2
```

Randomizes only:

```text
distance + camera angle
```

Example output:

```text
close-up, low-angle view
```

Another example:

```bash
python random_compose_prompt.py -fragments 2,3,4,5,6,7,8
```

This randomizes everything except `distance`.

The order supplied to `-fragments` is also the order used in the resulting prompt.

For example:

```bash
python random_compose_prompt.py -fragments 5,2,3
```

might produce:

```text
standing with hips tilted to one side, three-quarter front view, 50mm normal lens
```

---

## `-range`

Use `-range` when you want a category to randomly select only from a specific subset of its entries.

Syntax:

```bash
-range 'CATEGORY:[START-END]'
```

Multiple ranges can be separated with commas:

```bash
-range '1:[3-6],3:[3-4]'
```

The indices are:

- **1-based**
- **inclusive**

So:

```text
1:[3-6]
```

means category `1` may use entries:

```text
3, 4, 5, 6
```

---

## Range Example

Suppose the `distance` category begins with:

```json
[
  "extreme close-up",
  "very close-up",
  "tight close-up",
  "close-up",
  "medium close-up",
  "loose close-up"
]
```

Then:

```bash
-range '1:[3-6]'
```

limits `distance` to only:

```text
tight close-up
close-up
medium close-up
loose close-up
```

Likewise, if the beginning of `lens_focal_length` is:

```json
[
  "14mm ultra-wide lens",
  "18mm wide-angle lens",
  "20mm wide-angle lens",
  "24mm wide-angle lens"
]
```

then:

```bash
-range '3:[3-4]'
```

limits the lens selection to:

```text
20mm wide-angle lens
24mm wide-angle lens
```

Full example:

```bash
python random_compose_prompt.py \
  -fragments 1,3,5 \
  -range '1:[3-6],3:[3-4]'
```

Possible output:

```text
medium close-up, 24mm wide-angle lens, jumping forward
```

Category `5` has no range restriction here, so `overall_pose` is selected from its entire list.

---

## Show Selected Categories

Add:

```bash
--show-indices
```

to see how the final prompt was assembled.

Example:

```bash
python random_compose_prompt.py \
  -fragments 1,3,5 \
  -range '1:[3-6],3:[3-4]' \
  --show-indices
```

Example output:

```text
[1] distance: medium close-up
[3] lens_focal_length: 24mm wide-angle lens
[5] overall_pose: jumping forward

medium close-up, 24mm wide-angle lens, jumping forward
```

Without `--show-indices`, only the final prompt is printed.

---

## Reproducible Random Output

Use `-seed` if you need repeatable results.

Example:

```bash
python random_compose_prompt.py -fragments 1,3,5 -seed 1234
```

Running the same command with the same JSON data and the same seed will produce the same selections.

This can be useful for debugging or reproducing a generation setup.

---

## Use a Different JSON File

By default, the script reads:

```text
/mnt/data/camera_pose_categories_v2.json
```

To use another file:

```bash
python random_compose_prompt.py \
  -fragments 1,2,3,5 \
  -json ./my_fragments.json
```

The replacement JSON must contain the same category names expected by the script:

```json
{
  "distance": [],
  "camera_angle": [],
  "lens_focal_length": [],
  "framing": [],
  "overall_pose": [],
  "hand_arm_expression": [],
  "leg_pose": [],
  "head_pose": []
}
```

---

## JSON Example

A shortened example:

```json
{
  "distance": [
    "extreme close-up",
    "close-up",
    "medium shot",
    "full-body distance"
  ],
  "camera_angle": [
    "eye-level view",
    "high-angle view",
    "low-angle view",
    "POV shot"
  ],
  "lens_focal_length": [
    "24mm wide-angle lens",
    "40mm natural perspective lens",
    "50mm normal lens",
    "85mm portrait lens"
  ],
  "framing": [
    "shoulders-up framing",
    "waist-up framing",
    "full-body framing"
  ],
  "overall_pose": [
    "standing upright",
    "leaning against a wall",
    "walking toward the camera"
  ],
  "hand_arm_expression": [
    "arms relaxed at the sides",
    "right hand on hip"
  ],
  "leg_pose": [
    "legs together",
    "ankles crossed"
  ],
  "head_pose": [
    "head facing forward",
    "looking into the distance"
  ]
}
```

You can freely add, remove, or reorder entries inside each list.

Note that changing the order of entries also changes the meaning of numeric ranges used with `-range`.

---

## Practical Examples

### Camera variation only

```bash
python random_compose_prompt.py -fragments 1,2,3,4
```

Possible output:

```text
medium shot, three-quarter front view, 40mm natural perspective lens, waist-up framing
```

### Pose variation only

```bash
python random_compose_prompt.py -fragments 5,6,7,8
```

Possible output:

```text
leaning against a wall, right hand on hip, ankles crossed, looking into the distance
```

### Complete camera + pose combination

```bash
python random_compose_prompt.py -fragments 1,2,3,4,5,6,7,8
```

Possible output:

```text
medium close-up, low-angle view, 50mm normal lens, waist-up framing, standing with hips tilted to one side, one hand touching the cheek, one knee slightly bent, head tilted slightly right
```

### Restrict close shots and wide lenses

```bash
python random_compose_prompt.py \
  -fragments 1,2,3,5,6,7,8 \
  -range '1:[1-6],3:[1-5]'
```

This keeps `distance` within the first six close-range entries and `lens_focal_length` within the first five wide-angle entries.

---

## Command-Line Reference

```text
-fragments        Required. Comma-separated category IDs.
                  Example: 1,3,5

-range            Optional. Restrict one or more categories to inclusive
                  1-based entry ranges.
                  Example: '1:[3-6],3:[3-4]'

-json             Optional. Path to the category JSON file.
                  Default: /mnt/data/camera_pose_categories_v2.json

-seed             Optional. Integer random seed for reproducible output.

--show-indices     Optional. Show each selected category and value before
                  printing the final composed prompt.
```

---

## Important Notes

### Ranges use entry positions, not values

This:

```bash
-range '3:[3-4]'
```

means:

> select from entries 3 through 4 of category 3

It does **not** mean focal lengths from 3mm through 4mm.

### Ranges are inclusive

```text
[3-6]
```

includes:

```text
3, 4, 5, 6
```

### Category IDs are fixed in the Python script

```text
1 distance
2 camera_angle
3 lens_focal_length
4 framing
5 overall_pose
6 hand_arm_expression
7 leg_pose
8 head_pose
```

If you rename categories in the JSON, update `CATEGORY_MAP` in `random_compose_prompt.py` as well.

### Quoting `-range`

On shells such as Bash or Zsh, it is safest to wrap the range expression in quotes:

```bash
-range '1:[3-6],3:[3-4]'
```

This prevents shell interpretation of brackets.

---

## Example Workflow

A typical workflow might be:

```bash
python random_compose_prompt.py \
  -fragments 1,2,3,4,5,6,7,8 \
  -range '1:[3-12],3:[4-16]'
```

Then append the generated fragment string to your fixed subject/style prompt.

For example:

```text
20-year-old woman wearing a black leather jacket,
medium close-up,
three-quarter front view,
50mm normal lens,
waist-up framing,
leaning against a wall,
right hand on hip,
one knee slightly bent,
looking into the distance,
cinematic lighting, realistic skin texture
```

This lets the script control camera and pose variation while your main prompt controls subject, wardrobe, environment, style, and lighting.


## Default behavior

If you run the script without any arguments:

```bash
python random_compose_prompt.py
```

it randomly selects one entry from **all 8 categories** and combines them into one prompt.
