# Crosscut-first layouts

**Goal:** Prefer sheets that can be broken into useful smaller rectangles before ripping individual parts.

**Approach:** Keep the existing solver, unrestricted candidates, middle-third section candidates and saved incumbent.
Add explicit crosscut-first three-stage candidates. Rank part-weighted physical section length after stock use and the
middle-third preference, ahead of offcut quality. Ignore empty bands so waste-only strips earn no reward.

1. Add shared full-width crosscut detection to `cutting.py`; reuse it in scoring and sequence ordering.
2. Explore crosscut-first orientations alongside unrestricted candidates for whole sheets and middle-third sections.
   Include native first-stage width caps derived from the required blanks: orientation alone can retain wide bands
   with staggered cuts inside them. Preserve uncapped candidates as well.
3. Put full-width breakdown cuts first, then retain native order for the remaining cuts. Explain this in the existing
   sequence display, SVG cut labels and application documentation. Preserve kerf, grain, trim, stock limits and fitting blanks.
4. Resume the existing 6mm sheet search through the running application's API. Inspect its result and logs. No tests,
   extra verification processes, service starts or browser interaction checks, following project instructions.

Evidence: [Kreg's grouped-cut workflow](https://learn.kregtool.com/learn/layout-and-cutting-to-maximize-plywood/) and
[PackingSolver's stage/orientation controls](https://fontanf.github.io/packingsolver/rectangleguillotine.html#first-stage-orientation).
