# CAD and cut-list piece navigation

26 October 2026. Approved interaction: double-click a wood piece to switch views and locate the same CAD leaf.

Implementation:

- Reuse CAD paths, the existing tab router, native GPU picker and shared dropdown menu. No geometry regeneration.
- Make faded vehicle groups invisible only during picking; restore them before the visual render. Apply this to
  the native picker so hover, measurement selection and navigation agree. Keep modifier double-click gestures.
- Frame a selected piece using its current world bounds and thin axis. Keep a magenta overlay until the selection
  changes or is cleared. The overlay is visible through obstructions and never participates in picking. Restore temporary
  visibility and dispose overlay materials on dismissal, replacement or model reload.
- Escape, empty-space click and the existing toolbar's clear-selection icon clear selection. Context menus expose action names
  and shortcuts. Keep keyboard navigation through visible buttons.
- Keep single-click cut-list details non-modal, opposite the pointer, so they cannot intercept the second click.
  Restore the cut-list position when returning to the same piece; otherwise reveal its material and sheet.
- Inspect source, existing app DOM/console and development logs; run `git diff --check`. No tests, build, typecheck,
  automated interaction checks or delegated review, per AGENTS.md. Gert checks pointer behaviour and camera choice.

Sources and decisions:

- [WAI menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/): reuse the dropdown's focus, dismissal and
  keyboard handling; provide both a visible trigger and a context-menu trigger.
- [WCAG keyboard guidance](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): double-click also has a visible,
  keyboard-operable action. Do not require timed keyboard input.
- [WCAG pointer cancellation](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html): navigation happens
  on double-click, clearing on click; dragging does not activate either action.
- [Native non-modal dialog](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/show): details remain
  available while the underlying piece can receive its second click. No click-delay timer is needed.

Installed renderer inspection found that plain double-click toggles a bounding box, Escape clears only tool-scoped
selection, and the GPU picker ignores visual opacity. These behaviours explain the reported selection problems.

Implementation is in `viewer-pieces.ts`, `viewer.ts`, `vehicle-fade.ts`, and the existing cutting UI. Fading past the
halfway point excludes an outer group from picking; switching See inside off restores its picking. Completely clear
rear glass remains click-through. The shared picker buffer is invalidated when the exclusion set changes.
The highlight uses layer-zero-only overlay meshes with shared geometry and disposable magenta materials; original
piece colours remain intact. Camera framing and overlays follow the current world transforms of moving parts.
Temporary leaf visibility is restored when selection ends unless a visibility change superseded it.

The existing app loaded the new Piece actions control with status Ready and no current console warnings/errors.
This is loading evidence only. Double-click, click-through picking, camera choice and keyboard/pointer
behaviour still require Gert's visual acceptance. No automated interactions, tests, builds or typechecks were run.

Cut-list emphasis: selected shapes use a persistent bright magenta fill and a four-pixel dark outline with a white
halo. Other pieces on the same sheet are dimmed; the corresponding key/table entry or grouped gallery card also
stays highlighted. Hover cannot override the selected shape's style. Selection survives layout refreshes and ends
when another piece is selected or selection is cleared. The CAD overlay now follows the same rule and colour.
Both views use `--piece-selection-colour`, currently `#ff39a0`. CAD selection has no timer or animation loop;
selecting another piece disposes the old overlay and highlights the new one. Escape uses a document capture
listener scoped to the active CAD tab, so it also works when focus has moved to a toolbar button or the page body.

Escape correction: read-only inspection found five selected cut-list elements with keyboard focus on `BODY`.
The panel-local handler could not receive the key. Escape now uses a document capture listener scoped to the
visible Cut list tab, including after layout updates remove the focused element. An open context menu handles
its own Escape first; a subsequent Escape clears selection. The listener calls the same clear command as the menu.

Toolbar correction: remove the floating bottom-left Piece actions bar and selected-name text, which obstructed the
XYZ widget. Add two icon buttons to the existing top toolbar, using its tooltip, button-frame and 30px button styles:
Show in cut list and Clear selection. Buttons, double-click, Escape and the context menu reuse the same commands.
The navigation button is disabled until a cutting piece is selected. Tooltips include the action and shortcut;
native buttons provide Enter/Space activation and accessible names, following the
[WAI button guidance](https://www.w3.org/WAI/ARIA/apg/patterns/button/).
