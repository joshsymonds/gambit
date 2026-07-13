# Visual verification — see it rendered before calling it done

An aesthetic or visual task is not verified by reading the diff — diffs of markup/CSS can't tell you whether the page looks right. Verify on the rendered output, whether you implemented it yourself (the aesthetic-judgment exception) or dispatched it.

## The loop

1. Build or serve the project's real output — the same build the task's test command produces.
2. Capture the changed view with a headless browser, at more than one width:

```bash
shots=$(mktemp -d)             # scratch dir (mktemp, not a predictable /tmp path)
cd <build-dir> && python3 -m http.server 8000 &
for w in 1440 390; do          # desktop, mobile
  chromium --headless --disable-gpu --hide-scrollbars \
    --window-size=${w},2000 --screenshot=${shots}/view-${w}.png "http://localhost:8000/"
done
```

3. **Read the images — actually look.** Judge against the brief: typographic hierarchy (does the eye land in the right order?), spacing and rhythm, colour and contrast, whether ornament reads as intended. Cite what works and what doesn't; "looks fine" is not a verdict.
4. Check it doesn't break: no horizontal scroll on mobile, no overflow, no broken or missing assets, no console errors.
5. Where motion matters, capture with `prefers-reduced-motion` emulated too, and confirm the reduced-motion path is acceptable.

## Accessibility, not just pixels

A build-output test that greps *visible* text misses the accessibility tree. If the view conveys meaning through text a screen reader also reads (counts, labels), assert on the accessible name / `aria-*`, not only the visible string — text present once visibly can still be announced twice.

## The aesthetic bar is the user's

Put the screenshots in the checkpoint. Present the rendered view and your read of it; a subjective "beautiful, done" asserted without showing the user the pixels is not verification.
