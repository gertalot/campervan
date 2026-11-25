import { createColourField } from './paint-colour-field';
import { paintTextures, samePaint, type PaintSwatch } from './paint-swatch';
import type { PlanMenuItem } from './plan-dropdown';
import './paint-picker.css';

export const paintCommandLabel = 'Paint bucket';
export const paintShortcut = 'B';

interface PaintPickerOptions {
  onToggle(): void;
  onSample(): void;
  historyCommands(): PlanMenuItem[];
  used(): PaintSwatch[];
  favourites(): PaintSwatch[];
  onFavourites(items: PaintSwatch[]): void;
}

const tabNames = ['RGB', 'HSV', 'Textures', 'Favourites', 'Currently used'] as const;
type PickerTab = typeof tabNames[number];

function button(label: string) {
  const control = document.createElement('button');
  control.type = 'button';
  control.textContent = label;
  return control;
}

function appearance(chip: HTMLElement, swatch: PaintSwatch) {
  const texture = paintTextures.find(item => item.id === swatch.texture);
  chip.style.setProperty('--paint-colour', swatch.colour);
  chip.style.setProperty('--paint-opacity', String(swatch.opacity));
  chip.style.setProperty('--paint-image', texture?.image ? `url("${texture.image}")` : 'none');
}

function paintName(swatch: PaintSwatch) {
  const texture = paintTextures.find(item => item.id === swatch.texture);
  const colour = swatch.colour.toUpperCase();
  const name = swatch.texture === 'solid' ? colour : `${texture?.label ?? swatch.texture} · ${colour}`;
  return `${name} · ${Math.round(swatch.opacity * 100)}%`;
}

export function createPaintPicker(options: PaintPickerOptions) {
  let selected: PaintSwatch = { colour: '#ffffff', opacity: 1, texture: 'solid' };
  let tab: PickerTab = 'RGB';

  const element = document.createElement('span');
  element.className = 'cad-piece-controls cad-paint-controls';
  element.dataset.campervanControl = 'true';

  function toolbarButton(label: string, hint: string) {
    const tooltip = document.createElement('span');
    tooltip.className = 'tcv_tooltip';
    tooltip.dataset.tooltip = hint;
    const frame = document.createElement('span');
    frame.className = 'tcv_button_frame';
    const control = button('');
    control.className = 'tcv_reset tcv_btn cad-piece-button';
    control.setAttribute('aria-label', label);
    control.title = hint;
    frame.append(control);
    tooltip.append(frame);
    element.append(tooltip);
    return control;
  }

  const bucket = toolbarButton(paintCommandLabel, `${paintCommandLabel} · ${paintShortcut}`);
  bucket.setAttribute('aria-pressed', 'false');
  bucket.setAttribute('aria-keyshortcuts', paintShortcut);
  bucket.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"
    stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
    <path d="m3 12 8-8 9 9-8 8a2 2 0 0 1-3 0l-6-6a2 2 0 0 1 0-3Z"/>
    <path d="M4 12h15M7 9V4a2 2 0 0 1 4 0v3"/>
    <path d="M21 15s-2 2.7-2 4a2 2 0 0 0 4 0c0-1.3-2-4-2-4Z" fill="currentColor" stroke="none"/></svg>`;
  bucket.onclick = options.onToggle;
  const choose = toolbarButton('Choose paint', 'Choose paint colour, texture and opacity');
  choose.setAttribute('aria-haspopup', 'dialog');
  choose.innerHTML = '<span class="paint-chip"></span>';
  const toolbarChip = choose.firstElementChild as HTMLElement;
  const historyButtons = options.historyCommands().map((command, index) => {
    const control = toolbarButton(command.label, command.label + ' · ' + command.shortcut);
    control.setAttribute('aria-keyshortcuts', command.ariaShortcut!);
    control.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"
      stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <path transform="${index ? 'translate(24 0) scale(-1 1)' : ''}" d="M9 5l-5 5 5 5m-5-5h10a6 6 0 0 1 6 6v3"/></svg>`;
    control.onclick = command.run;
    return control;
  });

  const popup = document.createElement('div');
  popup.id = 'cad-paint-picker';
  popup.popover = 'auto';
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-labelledby', 'cad-paint-title');
  popup.innerHTML = `
    <div class="paint-heading"><strong id="cad-paint-title">Choose paint</strong>
      <button type="button" class="paint-close" aria-label="Close paint picker" title="Close (Esc)">×</button></div>
    <div class="paint-tabs" role="tablist" aria-label="Paint options"></div>
    <div class="paint-panels"></div>
    <label class="paint-scale">Opacity <span class="paint-alpha-value" aria-hidden="true"></span>
      <input class="paint-track paint-alpha" type="range" max="100"></label>
    <div class="paint-bottom">
      <button type="button" class="paint-sample" aria-label="Sample finish from model" title="Sample finish from model">
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"
          stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path d="m13 8 3-3a2.1 2.1 0 0 1 3 3l-3 3m-5-5 7 7M12 8l-8 8-.8 4.8L8 20l8-8"/></svg>
      </button>
      <span class="paint-chip"></span>
      <div><strong class="paint-current-name"></strong><span class="paint-current-detail"></span></div>
      <button type="button" class="paint-favourite"></button></div>`;
  // Keep input outside the viewer's capture-phase camera shortcuts. Native popovers handle light dismiss.
  document.body.append(popup);
  choose.popoverTargetElement = popup;
  const opacity = popup.querySelector<HTMLInputElement>('.paint-alpha')!;
  const opacityValue = popup.querySelector<HTMLElement>('.paint-alpha-value')!;
  const currentChip = popup.querySelector<HTMLElement>('.paint-bottom .paint-chip')!;
  const currentName = popup.querySelector<HTMLElement>('.paint-current-name')!;
  const currentDetail = popup.querySelector<HTMLElement>('.paint-current-detail')!;
  const pipette = popup.querySelector<HTMLButtonElement>('.paint-sample')!;
  pipette.onclick = options.onSample;
  const favourite = popup.querySelector<HTMLButtonElement>('.paint-favourite')!;
  const tabs = popup.querySelector<HTMLElement>('.paint-tabs')!;
  const panels = popup.querySelector<HTMLElement>('.paint-panels')!;
  const pages = new Map<PickerTab, { control: HTMLButtonElement; panel: HTMLElement }>();

  const colourField = createColourField(colour => {
    selected = { ...selected, colour };
    refresh();
  });

  // Tabs use automatic activation and one tab stop (W3C APG Tabs Pattern).
  // https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
  for (const name of tabNames) {
    const id = 'cad-paint-' + name.toLowerCase().replace(' ', '-');
    const control = button(name);
    control.id = id + '-tab';
    control.setAttribute('role', 'tab');
    control.setAttribute('aria-controls', id + '-panel');
    const panel = document.createElement('div');
    panel.id = id + '-panel';
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', control.id);
    pages.set(name, { control, panel });
    control.onclick = () => showTab(name);
    control.onkeydown = event => {
      const index = tabNames.indexOf(name);
      const last = tabNames.length - 1;
      const next = { ArrowRight: (index + 1) % tabNames.length, ArrowLeft: (index + last) % tabNames.length,
        Home: 0, End: last }[event.key];
      if (next === undefined) return;
      event.preventDefault();
      showTab(tabNames[next]);
      pages.get(tabNames[next])!.control.focus();
    };
    tabs.append(control);
    panels.append(panel);
  }

  function showTab(name: PickerTab) {
    tab = name;
    currentName.hidden = name === 'RGB' || name === 'HSV';
    if (name === 'RGB' || name === 'HSV') {
      pages.get(name)!.panel.append(colourField.element);
      colourField.show(name, selected.colour);
    }
    for (const [key, { control, panel }] of pages) {
      const active = key === tab;
      control.tabIndex = active ? 0 : -1;
      control.setAttribute('aria-selected', String(active));
      panel.hidden = !active;
    }
    if (tab === 'Favourites' || tab === 'Currently used') fillLibrary();
    refresh();
  }

  opacity.oninput = () => { selected = { ...selected, opacity: opacity.valueAsNumber / 100 }; refresh(); };

  const textureButtons = paintTextures.map(texture => {
    const control = button(texture.label);
    const chip = document.createElement('span');
    chip.className = 'paint-chip';
    appearance(chip, { colour: texture.defaultColour ?? '#ffffff', texture: texture.id, opacity: 1 });
    control.prepend(chip);
    control.onclick = () => {
      selected = { ...selected, texture: texture.id, colour: texture.defaultColour ?? selected.colour };
      refresh();
    };
    pages.get('Textures')!.panel.append(control);
    return { id: texture.id, control };
  });

  let libraryButtons: { swatch: PaintSwatch; control: HTMLButtonElement }[] = [];
  function fillLibrary() {
    const saved = tab === 'Favourites';
    const list = saved ? options.favourites() : options.used();
    const panel = pages.get(tab)!.panel;
    panel.replaceChildren();
    panel.tabIndex = list.length ? -1 : 0;
    if (!list.length) panel.textContent = saved ? 'No favourite paint yet.' : 'No paint in use.';
    libraryButtons = list.map(swatch => {
      const control = button(paintName(swatch));
      const chip = document.createElement('span');
      chip.className = 'paint-chip';
      appearance(chip, swatch);
      control.prepend(chip);
      control.setAttribute('aria-pressed', String(samePaint(swatch, selected)));
      control.onclick = () => { selected = { ...swatch }; refresh(); };
      panel.append(control);
      return { swatch, control };
    });
  }

  favourite.onclick = () => {
    const list = options.favourites();
    options.onFavourites(list.some(item => samePaint(item, selected))
      ? list.filter(item => !samePaint(item, selected)) : [...list, { ...selected }]);
    if (tab === 'Favourites') fillLibrary();
    refresh();
  };

  function refresh() {
    appearance(toolbarChip, selected);
    appearance(currentChip, selected);
    choose.setAttribute('aria-label', 'Choose paint. ' + paintName(selected));
    currentName.textContent = selected.colour.toUpperCase();
    currentDetail.textContent = paintTextures.find(item => item.id === selected.texture)?.label ?? selected.texture;
    popup.style.setProperty('--shade', selected.colour);
    opacity.value = String(Math.round(selected.opacity * 100));
    opacityValue.textContent = opacity.value + '%';
    opacity.setAttribute('aria-valuetext', opacityValue.textContent);
    for (const { id, control } of textureButtons) control.setAttribute('aria-pressed', String(id === selected.texture));
    for (const { swatch, control } of libraryButtons) {
      control.setAttribute('aria-pressed', String(samePaint(swatch, selected)));
    }
    favourite.textContent = options.favourites().some(item => samePaint(item, selected))
      ? 'Remove from favourites' : 'Save to favourites';
  }

  function close() {
    if (popup.matches(':popover-open')) popup.hidePopover();
  }
  popup.querySelector<HTMLButtonElement>('.paint-close')!.onclick = () => { close(); choose.focus(); };
  popup.addEventListener('beforetoggle', event => {
    if ((event as ToggleEvent).newState !== 'open') return;
    const rect = choose.getBoundingClientRect();
    popup.style.setProperty('--paint-anchor-x', rect.left + 'px');
    popup.style.setProperty('--paint-anchor-y', rect.bottom + 6 + 'px');
    showTab(tab);
  });
  popup.addEventListener('toggle', () => {
    const open = popup.matches(':popover-open');
    choose.setAttribute('aria-expanded', String(open));
    if (open && !popup.contains(document.activeElement)) pages.get(tab)!.control.focus();
  });
  choose.setAttribute('aria-expanded', 'false');
  showTab(tab);
  return {
    element, swatch: () => ({ ...selected }), close,
    finishSample(swatch?: PaintSwatch) {
      if (swatch) selected = { ...swatch };
      popup.showPopover();
      pipette.focus();
    },
    setBucketActive(active: boolean) { bucket.setAttribute('aria-pressed', String(active)); },
    updateHistory() {
      options.historyCommands().forEach((command, index) => { historyButtons[index].disabled = !command.enabled; });
    },
    setDisabled(disabled: boolean) { if (disabled) close(); bucket.disabled = choose.disabled = pipette.disabled = disabled; },
  };
}
