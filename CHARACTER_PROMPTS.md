# Character prompts

Paste-ready text-to-image prompts for every character, for trying other image models (user, Oct 4, 2026). They are
the same texts `assets/scripts/model_pipeline.py concept` builds (subject + pose + style + framing), with the
anatomy written positively. Models that support a negative prompt get the listed negatives; for models that don't,
leave them out (writing "no tail" into the positive prompt makes some models draw a tail).

Rules that still apply: check every image against the anatomy line (count parts, check where they attach,
`CHARACTERS.md`), colors from `PALETTE.md` (hero orange and lava orange are reserved for the hero and lava),
one subject, full body, plain background, arms horizontal (T-pose) for anything that gets rigged.

## Building blocks

Style **character** (all new characters, "characterful, not cute"):
```
Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors.
```
Style **hero** (only the orangutan and the jungle cat):
```
Stylized 3D cartoon character render like a modern animated kids' movie, cute chibi proportions, big head, huge glossy expressive eyes with bright highlights, kind happy smile, soft sculpted fur clumps with a playful hair tuft, warm saturated colors, smooth clean materials.
```
Framing (always):
```
Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```
Poses (pick the one listed per character):

- **humanoid**: Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human.
- **tpose**: Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera. Nothing overlaps the body: a tail, if any, sticks out sideways, fully visible and clear of the legs.
- **quadruped**: Character reference, side view from the left, standing neutral on all four straight legs, legs a little apart so none overlap, head up turned slightly toward the camera, tail stretched straight out behind, fully visible and clear of the body and legs.
- **hexapod**: Character reference, side view from the left, standing on all six legs, the legs spread apart so none overlap, head and antennae up, the whole body fully visible.
- **wings**: Front view, standing upright on its feet facing the camera, both wings spread wide open to the sides like a T-pose, every wing feather visible, tail feathers pointing down.
- **spread**: Three-quarter front view from slightly above, standing with all legs spread wide so none overlap, claws raised and open, the whole body fully visible.
- **flippers**: Three-quarter front view from slightly above, all four flippers stretched out flat to the sides, head forward, the whole body fully visible.

## Characters

### Orangutan hero (in game, reference only)

Style `hero`, pose `tpose`. Anatomy: 2 arms, 2 legs, 1 very long tail (about body length), 2 ears, 2 eyes.

```
a chibi orangutan hero with bright orange shaggy fur, a big round head with a playful hair tuft on top, a pale peach face and big friendly eyes, long arms, short legs, and an unusually long lemur-style tail about as long as its body, striped in orange and darker rust rings. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera. Nothing overlaps the body: a tail, if any, sticks out sideways, fully visible and clear of the legs. Stylized 3D cartoon character render like a modern animated kids' movie, cute chibi proportions, big head, huge glossy expressive eyes with bright highlights, kind happy smile, soft sculpted fur clumps with a playful hair tuft, warm saturated colors, smooth clean materials. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `extra limbs, second tail, short tail, human clothes, realistic ape anatomy, multiple characters, text, watermark, cropped, props, ground shadow`

### Jungle cat (sidekick)

Style `hero`, pose `quadruped`. Anatomy: 4 legs, 1 tail, 2 ears, 2 eyes.

```
a chibi jungle cat cub (leopard cat), warm golden ochre fur with dark brown leopard rosette spots, cream belly and muzzle, dark ear backs, dark rings on a long fluffy tail, pink nose. Character reference, side view from the left, standing neutral on all four straight legs, legs a little apart so none overlap, head up turned slightly toward the camera, tail stretched straight out behind, fully visible and clear of the body and legs. Stylized 3D cartoon character render like a modern animated kids' movie, cute chibi proportions, big head, huge glossy expressive eyes with bright highlights, kind happy smile, soft sculpted fur clumps with a playful hair tuft, warm saturated colors, smooth clean materials. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `extra tails, standing upright, extra legs, multiple characters, text, watermark, cropped, props, ground shadow`

### Parrot (hint parrot / giant Parrot Air parrot)

Style `character`, pose `wings`. Anatomy: 2 wings at the shoulders, 2 legs, feet 2 toes forward + 2 back, tail feathers, hooked beak.

```
a scruffy macaw parrot, banana yellow and jungle green feathers with some red, ruffled messy head feathers, loud show-off attitude, big curved beak, feet with two toes forward and two toes back. Front view, standing upright on its feet facing the camera, both wings spread wide open to the sides like a T-pose, every wing feather visible, tail feathers pointing down. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `reptile tail, extra wings, four wings, three toes forward, multiple characters, text, watermark, cropped, props, ground shadow`

### Giant ant (ride)

Style `character`, pose `hexapod`. Anatomy: head + thorax + thin waist + abdomen; 6 legs, all on the thorax (3 per side); 2 antennae; 2 mandibles.

```
a giant ant, rust-red and dark brown chitin armor with scratches and dents, chunky head with big curved mandibles, bent antennae, tough and a bit dim expression, broad flat thorax a small rider could sit on, a thin waist and a round abdomen, three legs on each side of the thorax. Character reference, side view from the left, standing on all six legs, the legs spread apart so none overlap, head and antennae up, the whole body fully visible. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, stinger, legs on the abdomen, four legs, eight legs, saddle, multiple characters, text, watermark, cropped, props, ground shadow`

### Old tortoise (banana gate NPC)

Style `character`, pose `quadruped`. Anatomy: domed shell, 4 thick legs, short neck, tail at most a stub under the shell.

```
an old giant tortoise, mossy chipped domed shell with tiny ferns growing on it, droopy heavy eyelids, long wrinkled neck, grumpy but wise expression, sandy grey-green skin, four thick stubby legs. Character reference, side view from the left, standing neutral on all four straight legs, legs a little apart so none overlap, head up turned slightly toward the camera, tail stretched straight out behind, fully visible and clear of the body and legs. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `long tail, standing upright, human pose, multiple characters, text, watermark, cropped, props, ground shadow`

### Beach crab (ambient)

Style `character`, pose `spread`. Anatomy: wide flat shell, 2 claws, 8 walking legs (4 per side), 2 eyes on stalks, tiny antennae.

```
a beach crab, wide flat sand-colored shell with turquoise claw tips, one oversized claw, eyes on tall eyestalks, nervous twitchy expression, four walking legs on each side. Three-quarter front view from slightly above, standing with all legs spread wide so none overlap, claws raised and open, the whole body fully visible. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fur, eyes in a face, six legs, ten walking legs, multiple characters, text, watermark, cropped, props, ground shadow`

### Sea turtle (lagoon)

Style `character`, pose `flippers`. Anatomy: 2 long front flippers, 2 short rear flippers, short neck.

```
a sea turtle, turquoise-tinted shell with a lighter pattern, calm half-asleep eyes, slightly barnacled shell edge, two long front flippers and two short rear flippers. Three-quarter front view from slightly above, all four flippers stretched out flat to the sides, head forward, the whole body fully visible. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `feet with toes, long tail, fish tail, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin man (villager)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin everywhere skin shows, no tail.

```
a friendly adult goblin fisherman with bright green skin, two long pointy ears sticking out sideways, a big round nose, kind eyes under bushy eyebrows, a relaxed easy grin, short stocky body with big bare feet, wearing a teal sleeveless shirt, rolled-up brown shorts and a frayed straw hat. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, tusks, horns, claws, scary, human skin, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin woman (villager)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin, no tail.

```
a friendly adult goblin woman villager with bright green skin, two long pointy ears sticking out sideways, a big pointed nose, lively eyes, a relaxed easy smile, dark hair in a messy bun, a stocky body with big bare feet, wearing a coral-red sleeveless top, rolled-up khaki shorts and a frayed straw sun hat, relaxed beach leisure look. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, apron, dress, horns, claws, human skin, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin child (villager)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin, no tail.

```
a small friendly goblin kid with bright green skin, two big pointy ears sticking out sideways, a button nose, a gap-toothed grin, a messy tuft of black hair, wearing a sky blue t-shirt, green shorts and no shoes. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, horns, claws, human skin, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin pirate (treasure cave)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin, no tail, empty hands.

```
a friendly old goblin pirate with bright green skin, two long pointy ears sticking out sideways under a faded red bandana, a big crooked nose, a black eyepatch over one eye, a bushy grey beard and a warm laughing grin with a few missing teeth, a little round belly, wearing a red and white striped shirt, a worn blue captain's coat with gold buttons, baggy brown trousers and old boots. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, hook hand, sword, human skin, peg leg, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin knight (Knights' Meadow)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin, no tail, empty hands.

```
a friendly goblin knight with bright green skin and two long pointy ears sticking out of an open-face rounded steel helmet with a little red plume, a big nose, a proud cheerful grin, shiny simple plate armor over a teal tabard with a yellow banana emblem, a short chunky body, steel boots, empty hands. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, sword, shield, visor closed, human skin, multiple characters, text, watermark, cropped, props, ground shadow`

### Horse (Knights' Meadow ride)

Style `character`, pose `quadruped`. Anatomy: 4 legs, 1 tail, 2 ears, 2 eyes.

```
a sturdy friendly storybook horse with a chestnut brown coat, a creamy blond mane and a long flowing blond tail, white socks on the legs, big kind eyes, a small simple saddle with a red blanket. Character reference, side view from the left, standing neutral on all four straight legs, legs a little apart so none overlap, head up turned slightly toward the camera, tail stretched straight out behind, fully visible and clear of the body and legs. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `extra legs, five legs, two tails, horn, wings, rider, multiple characters, text, watermark, cropped, props, ground shadow`

### Village dog

Style `character`, pose `quadruped`. Anatomy: 4 legs, 1 tail, 2 ears, 2 eyes.

```
a scruffy medium-sized island dog, sandy brown short fur, white chest, one floppy ear, red bandana collar, one wagging tail. Character reference, side view from the left, standing neutral on all four straight legs, legs a little apart so none overlap, head up turned slightly toward the camera, tail stretched straight out behind, fully visible and clear of the body and legs. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `extra legs, two tails, standing upright, multiple characters, text, watermark, cropped, props, ground shadow`

### Goblin wizard (Wizard's Crag, P3.4 — not generated yet)

Style `character`, pose `humanoid`. Anatomy: 2 arms, 2 legs, 5 fingers per hand, 2 pointy ears, green skin, no tail, empty hands (staff is a separate prop).

```
a friendly old goblin wizard with bright green skin, two long pointy ears sticking out under a tall floppy midnight-blue hat with yellow stars and moons, a long white beard tucked into a rope belt, round spectacles, a twinkly mischievous smile, a flowing purple robe with star patterns, curly-toed slippers, empty hands. Character turnaround reference sheet, front view, strict T-pose: both arms stretched perfectly horizontal straight out to the sides at shoulder height like the letter T, elbows straight, palms down, fingers spread apart, legs straight and a little apart, facing the camera, a person built like a small human. Stylized 3D cartoon character render in the spirit of 90s/2000s platformers like Crash Bandicoot and Banjo-Kazooie: characterful and a little goofy rather than cute, normal-size eyes with personality, scruffy textured fur or rough skin, slightly exaggerated proportions, strong readable silhouette, a bit of attitude in the expression, warm saturated colors. Soft even studio lighting, no cast shadows, plain light gray background, single subject centered, whole body visible with margin around it, no text, no props, no ground plane.
```

Negative: `tail, fangs, staff, wand, human skin, scary, multiple characters, text, watermark, cropped, props, ground shadow`

## Multiview (for Tripo multiview)

Same subject text, one image per view, ideally with the chosen concept as reference image:
- front: `... seen exactly from the front, facing the camera.`
- left: `... seen exactly from the side in profile, facing the left edge of the image.`
- back: `... seen exactly from behind.`
- right: `... seen exactly from the side in profile, facing the right edge of the image.`
Add the pose hold line ("Same strict T-pose ..." / "Standing on all four paws ...") so the pose doesn't drift.
