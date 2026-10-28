# Planner interaction decisions

Updated 28 October 2026. This is a personal conversion checklist editor, not a team project-management system.
The current interaction contract is also documented in [the planner guide](planner.md).

## Numbered checkbox outline

Gert explicitly chose one list type: a checkbox beside a hierarchical number, such as `1`, `1.1`, `1.2`, `1.2.1`, `2`.
The editor has no list-type selector or bullet/ordered-list shortcuts. Numbers are derived from the complete document
order, not stored as text or used as task identity. Collapse and hide-completed do not renumber the remaining items.
Moving, nesting, inserting and deleting items updates the displayed numbers. Separate list containers under the same
parent continue that parent's numbering. Existing and pasted conventional lists become the same checkbox hierarchy.

Each item remains a rich container for paragraphs, tables and shared purchase views. Enter continues prose inside
the item; Shift+Enter inserts a line break. New item is a separate, visible action with its shortcut shown in the UI.
This typing contract is Gert's requested application behaviour; it is not claimed as a universal outliner convention.

### New-item placement, 28 October

Gert chose context-sensitive insertion: **New item**, Cmd/Ctrl+Shift+Enter and `/task` prepend a subitem to an
expanded item that already has subitems. A collapsed item or an item without subitems gets a same-level item after
its full contents. Existing paragraphs, tables, purchase views and subitems retain their ownership. The new item is
unchecked, gets a fresh ID and receives the caret. Explicit **Add subitem** and **Add item at same level** actions
are available in the existing contextual menu; Add subitem expands a collapsed parent. Keyboard shortcuts help
explains the rule inside the app. Enter continues multiline writing; Tab/Shift+Tab retain the existing nesting commands.

The ordinary-outline insertion rule in
[Logseq's source](https://github.com/logseq/logseq/blob/master/src/main/frontend/handler/editor.cljs#L219-L241)
provided a concrete precedent for selecting child versus same-level insertion based on expansion and existing children.
[Workflowy](https://workflowy.com/help/add-edit-format) and
[Dynalist](https://help.dynalist.io/article/49-make-subitems) document same-level insertion and Tab nesting, but those
help pages do not establish the expanded-parent edge case. This behaviour follows Gert's choice.
The [WAI-ARIA menu-button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) was consulted again;
the actions reuse the current menu, saved selection, focus return and shared action registry.

Source inspection covered insertion positions, the installed task-item schema and the inherited Shift+Tab command.
No tests, builds, typechecks or browser interaction checks were run. Gert's hands-on editing remains the acceptance check.

The slash picker accepts its highlighted item with plain Tab or Enter, as Gert requested. Its footer displays the
navigation/accept/dismiss keys. Tab is intercepted only for an active picker with a matching item; modified Tab,
composition input and ordinary editor/table Tab behaviour are preserved. The
[WAI-ARIA combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) was consulted for highlighted suggestion
acceptance and preserving editing keys; Tab acceptance here is an explicit application choice, not an APG requirement.

## Menus and shortcut discovery

Sources consulted for this change:

- [NN/g: UI accelerators](https://www.nngroup.com/articles/ui-accelerators/) supports exposing shortcuts alongside
  actions rather than requiring recall. The planner shows shortcut labels on the right of menu actions and in tooltips.
- [NN/g: contextual menus](https://www.nngroup.com/articles/contextual-menus/) informs relevant context-sensitive
  commands and visible alternative access. The planner has an Actions trigger, item handles and right-click access;
  primary insertion and formatting commands also remain directly available.
- [WAI-ARIA menu button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) defines the trigger semantics,
  expanded state and keyboard opening conventions used here.
- [WAI-ARIA menu/menubar pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) defines menu roles, arrow/Home/End
  navigation, activation, Escape/focus return, Tab exit and focusable unavailable actions. The planner also supports
  type-ahead selection and Shift+F10/context-menu-key invocation.

One action registry supplies menu labels, keyboard labels, availability and execution. Context selects item, text,
table and purchase-view commands. The Actions trigger also includes less frequent formatting/style commands and a
Keyboard shortcuts reference. No fabricated keyboard shortcut is shown for actions without one; insertion aliases
such as `/table` are shown where appropriate. Menu selection is restored before an action executes.

Normal input menus remain available in purchase cells; Shift+right-click bypasses the custom document menu. The
menu includes Cut/Copy/Paste. Native Cut/Copy events retain ProseMirror serialization; menu Paste uses the browser
clipboard API and the editor's existing paste event pipeline. Permission failures explain how to use keyboard paste.
See [MDN Clipboard.read](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/read) for permission requirements
and [MDN execCommand](https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand) for the deprecated native
copy/cut bridge. This bridge is limited to explicit clipboard actions in the project's Chrome-based local workflow.

## Verification limits

### File menu correction, 26 October

The old Files & recovery control used a native disclosure containing a stack of buttons, independently of the editor's
menu code. It scrolled off-screen, had no menu navigation, and did not provide normal selection/outside-click dismissal.
It is replaced by **File** at the left of the sticky formatting toolbar. Its full-width text rows are grouped into reload,
exports and restore/import actions; commands that open a dialog use an ellipsis. The popup fits the viewport and opens
above the trigger when there is more space above. The existing reload/backup/restore data operations are unchanged.

`plan-dropdown.ts` now owns the shared presentation, focus, keyboard navigation and dismissal for File and the editor
menus. `plan-menu.ts` retains editor selection/context handling. No menu library or application-wide mechanism was added.
Up/Down, Home/End, type-ahead, Enter/Space, Escape/focus return, Tab exit, outside-click and action dismissal use the same
implementation. Up Arrow on a trigger opens at the last item; Down Arrow opens at the first. Unavailable items remain
focusable but cannot run. Ordinary form controls and the separate slash-completion Tab behaviour remain unchanged.

The [WAI-ARIA menu-button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) and
[menu](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) guidance was consulted again for this correction.
[NN/g's menu-design guidance](https://www.nngroup.com/articles/menu-design/) informed the trigger's stable location and
clear labels; its broader website-navigation recommendations are not a command-menu conformance standard.

Source inspection, the existing app's read-only DOM and console inspection established that File is a menu button in
the sticky toolbar, the old disclosure is gone, and there are no editor console errors after hot reload. No tests,
builds, typechecks or browser interaction checks were run. Popup appearance and keyboard/pointer behaviour still need
Gert's hands-on acceptance.

### Initial editor inspection, 25 October

Installed Tiptap/ProseMirror sources were inspected for schema parsing, commands and clipboard handling. Read-only
inspection of Gert's existing app tab showed hierarchical number labels, no list-type controls and no editor console
errors. Gert's tab was on the BOM during the final inspection, so this does not establish visible Plan layout or prove
menu keyboard/focus behaviour. No interaction automation, tests, builds, typechecks or services were run for this change.
Hands-on editing, nesting/movement, menu navigation and paste remain Gert's visual acceptance check.
