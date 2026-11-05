# Bill of materials page

Redesigned 1 November 2026 using the frontend-design guidance supplied by Gert.

## Design decisions

- Keep the app's system font and existing dark palette: canvas `#1b1d21`, surface `#22252a`, rules `#34373e`,
  text `#e3e7ed`, secondary text `#aab3c0`, links `#9ec5ef`.
- Lead with the project cost, spent amount and remaining estimate. Flag incomplete costs beside the summary.
  Filtering changes the list and its subtotal; the project summary retains its scope.
- Use a table for item and quantity comparison. Align numbers on the right with tabular numerals.
- Sortable purchase headers are native buttons with a neutral double arrow, switching to one directional arrow
  on the sorted column. Only that header carries `aria-sort`. Numeric columns compare numeric values, unknowns
  remain last in either direction, and Total price uses remaining cost. Keep detail rows paired with their item and
  return keyboard focus to the header after sorting. Filters and purchase refreshes retain the selected sort.
  Persist column and direction in localStorage, separately for the BOM and each Plan purchase-view ID, following
  the app's existing browser preference storage. Ignore invalid saved column/direction values.
- Show item names and supplier links directly. Keep quantities and unit prices editable in their columns.
  Put metadata and actual spending in a labelled form opened by a pencil button. Save commits the form's changes;
  Cancel discards them. Both close the form and return focus to the pencil. Preserve drafts and focus on refresh.
  Keep Bought as an editable quantity without a duplicate purchase action. Emphasise the Total price above quantity.
- Keep model stock as a visible section with a direct navigation link. Expand individual products for their uses
  and cut sizes. Retain the existing link from CAD material parameters to the corresponding stock entry.
- Reuse the purchasing component embedded in the Plan. Keep read-only static exports and purchase history intact.
- Read material quantities from current complete saved cutting layouts. Keep the total requirement separate from
  owned and bought stock; the existing slats show their actual cut-piece requirement and matching ownership.
- Mark missing quantities and prices needed for outstanding purchases with amber accents and explicit text. Actual
  spending is optional and never triggers an item warning. The summary count
  filters the list to those items; the same filter is available as a labelled checkbox.
- Restore text selection within the BOM and purchasing views; the viewer stylesheet disables it on the page body.
- Use ordinary links, buttons, table headers and labelled native controls. Horizontal scrolling is confined to
  the table at narrow widths; cost and filter controls wrap. No decorative motion or external font dependencies.

## Primary guidance consulted

- [W3C WAI: Tables](https://www.w3.org/WAI/tutorials/tables/) — table headers and explicit row/column scope.
- [W3C WAI: Labelling controls](https://www.w3.org/WAI/tutorials/forms/labels/) — associated labels for detail fields,
  accessible names for inline quantity controls.
- [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md) —
  semantic controls, visible keyboard focus, number alignment, overflow handling and explicit empty states.
- [W3C WAI: Use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) — pair amber warning accents
  with text identifying the missing information.
- [W3C WAI: Validating input](https://www.w3.org/WAI/tutorials/forms/validation/) — native form validation before
  saving, labelled inputs and retained values when validation fails.
- [W3C APG: Sortable table](https://www.w3.org/WAI/ARIA/apg/patterns/table/examples/sortable-table/) — native header
  buttons, `aria-sort` on the active header, distinct neutral/directional icons and full-cell activation targets.

These sources inform the implementation; they do not establish universal usability or accessibility compliance.
