/** Independent section stations and visibility, sharing one authored-section document. */
import { readCrossSections, recordCrossSection, type AuthoredSection, type SectionDocument,
  type SectionPlane } from './cross-section-api';

export function sectionStations(section: AuthoredSection): number[] {
  if (section.plane === 'XZ') return [section.y_mm!];
  const x = section.x_mm!, opposite = 2 * section.centre_x_mm - x;
  return section.mirror_x && Math.abs(opposite - x) > 0.001 ? [x, opposite] : [x];
}

export interface SectionControls {
  plane: SectionPlane;
  coordinate: number;
  rawOpacity: number;
  blueOpacity: number;
  activeId: string | null;
}
interface Panel extends SectionControls {
  range: HTMLInputElement;
  numeric: HTMLInputElement;
  output: HTMLOutputElement;
  rawInput: HTMLInputElement;
  blueInput: HTMLInputElement;
  select: HTMLSelectElement;
  record: HTMLButtonElement;
  rawStatus: HTMLParagraphElement;
  blueStatus: HTMLParagraphElement;
  key: string;
  bounds?: [number, number];
}

export function createSectionControls(container: HTMLElement, changed: (panel: SectionControls) => void) {
  container.insertAdjacentHTML('beforeend', '<section class="cross-sections"><h3>Cross sections</h3></section>');
  const host = container.querySelector<HTMLElement>('.cross-sections')!;
  let document: SectionDocument = { version: 1, revision: -1, sections: [] };
  let refreshing = false, recording = false, readFailed = false;
  const panels: Panel[] = [];
  const axis = (plane: SectionPlane) => plane === 'XZ' ? 'Y' : 'X';
  const active = (panel: Panel) => document.sections.find(section => section.plane === panel.plane
    && section.id === panel.activeId && sectionStations(section).some(at => Math.abs(at - panel.coordinate) < 0.5));
  function save(panel: Panel) {
    localStorage.setItem(panel.key, JSON.stringify({ coordinate: panel.coordinate,
      ...(panel.plane === 'XZ' ? { y: panel.coordinate } : {}), activeId: panel.activeId,
      rawOpacity: panel.rawOpacity * 100, blueOpacity: panel.blueOpacity * 100 }));
  }
  function updateBounds(panel: Panel) {
    const stations = document.sections.filter(section => section.plane === panel.plane).flatMap(sectionStations);
    const low = Math.floor(Math.min(panel.bounds?.[0] ?? Math.min(0, panel.coordinate), ...stations));
    const high = Math.ceil(Math.max(panel.bounds?.[1]
      ?? Math.max(panel.coordinate, panel.plane === 'XZ' ? 2000 : 1500), ...stations));
    for (const input of [panel.range, panel.numeric]) {
      input.min = String(low); input.max = String(high); input.disabled = !panel.bounds && !stations.length;
    }
    panel.coordinate = Math.max(low, Math.min(high, panel.coordinate));
  }
  function update(panel: Panel) {
    const current = active(panel), coordinate = panel.coordinate, coordinateAxis = axis(panel.plane);
    panel.range.value = panel.numeric.value = String(coordinate);
    panel.output.value = `${coordinateAxis} = ${coordinate} mm`;
    panel.range.setAttribute('aria-valuetext', `${coordinateAxis} ${coordinate} millimetres`);
    for (const [input, opacity] of [[panel.rawInput, panel.rawOpacity], [panel.blueInput, panel.blueOpacity]] as const) {
      input.value = String(Math.round(opacity * 100));
      input.setAttribute('aria-valuetext', `${input.value} percent`);
      input.parentElement!.querySelector('output')!.value = `${input.value}%`;
    }
    const choices = document.sections.filter(section => section.plane === panel.plane)
      .flatMap(section => sectionStations(section).map(at => ({ section, at }))).sort((a, b) => a.at - b.at);
    panel.select.replaceChildren(new Option('At current position', ''), ...choices.map(({ section, at }) =>
      new Option(`${coordinateAxis} ${at} mm · ${section.label || section.state}${section.label ? ` · ${section.state}` : ''}`,
        JSON.stringify([section.id, at]))));
    panel.select.value = current ? JSON.stringify([current.id, sectionStations(current)
      .find(at => Math.abs(at - coordinate) < 0.5)!]) : '';
    panel.record.disabled = recording || !current || current.state === 'recorded';
    panel.record.textContent = current?.plane === 'YZ' && sectionStations(current).length > 1
      ? 'Record this YZ pair' : `Record this ${panel.plane} section`;
    const opposite = current?.plane === 'YZ' && Math.abs(current.x_mm! - coordinate) > 0.5;
    panel.blueStatus.textContent = current
      ? `${current.state === 'recorded' ? 'Recorded' : 'Draft'} · ${current.label || `${coordinateAxis} ${coordinate} mm`}`
        + (opposite ? current.opposite_segments ? ' · authored opposite-side detail' : ' · matching opposite profile' : '')
        + (current.plane === 'YZ' && sectionStations(current).length > 1
          ? ` · paired X stations ${sectionStations(current).join(' / ')} mm` : '')
        + (current.notes ? ` — ${current.notes}` : '')
      : `No blue draft at ${coordinateAxis} = ${coordinate} mm. Ask me to create this section.`;
    changed(panel);
  }
  function move(panel: Panel, value: number, selectedId?: string) {
    if (!Number.isFinite(value)) return;
    panel.coordinate = Math.max(Number(panel.range.min), Math.min(Number(panel.range.max), value));
    panel.activeId = selectedId ?? [...document.sections].reverse().find(section => section.plane === panel.plane
      && sectionStations(section).some(at => Math.abs(at - panel.coordinate) < 0.5))?.id ?? null;
    update(panel); save(panel);
  }
  for (const plane of ['XZ', 'YZ'] as const) {
    const coordinateAxis = axis(plane);
    const title = plane === 'XZ' ? 'XZ · transverse' : 'YZ · longitudinal';
    const direction = plane === 'XZ' ? 'Rear → front' : 'Left → right';
    const datum = plane === 'XZ' ? 'rear' : 'left';
    host.insertAdjacentHTML('beforeend', `
      <section class="section-family" data-section-plane="${plane}" aria-labelledby="section-${plane}-heading">
        <h4 id="section-${plane}-heading">${title}</h4>
        <label class="reference-opacity">Position ${coordinateAxis} from ${datum} datum <output data-section-position-value></output>
          <input type="range" min="0" max="2000" step="1" data-section-position disabled />
        </label>
        <div class="section-station"><span>${direction}</span>
          <label>${coordinateAxis} <input type="number" step="1" data-section-position-number disabled /> mm</label>
        </div>
        <label class="reference-opacity section-raw">Green · raw scan <output></output>
          <input type="range" min="0" max="100" step="5" data-section-raw-opacity aria-label="${plane} green raw scan opacity" />
        </label>
        <label class="reference-opacity section-blue">Blue · authored <output></output>
          <input type="range" min="0" max="100" step="5" data-section-blue-opacity aria-label="${plane} blue authored opacity" />
        </label>
        <label class="reference-result">Blue sections<select data-section-saved aria-label="${plane} blue sections"></select></label>
        <button type="button" data-section-record disabled>Record this ${plane} section</button>
        <p data-section-raw-status role="status"></p>
        <p data-section-blue-status role="status" aria-live="polite"></p>
      </section>`);
    const family = host.querySelector<HTMLElement>(`[data-section-plane="${plane}"]`)!;
    const find = <T extends HTMLElement>(selector: string) => family.querySelector<T>(selector)!;
    const key = plane === 'XZ' ? 'campervan.cross-sections' : 'campervan.cross-sections.yz';
    const saved = JSON.parse(localStorage.getItem(key) ?? '{}');
    const previous = saved.coordinate ?? saved.y;
    const panel: Panel = {
      plane, coordinate: Number.isFinite(previous) ? previous : plane === 'XZ' ? 1000 : 750,
      activeId: saved.activeId ?? null, rawOpacity: Number(saved.rawOpacity ?? 100) / 100,
      blueOpacity: Number(saved.blueOpacity ?? 100) / 100, key,
      range: find('[data-section-position]'), numeric: find('[data-section-position-number]'),
      output: find('[data-section-position-value]'), rawInput: find('[data-section-raw-opacity]'),
      blueInput: find('[data-section-blue-opacity]'), select: find('[data-section-saved]'),
      record: find('[data-section-record]'), rawStatus: find('[data-section-raw-status]'), blueStatus: find('[data-section-blue-status]'),
    };
    panels.push(panel);
    panel.range.oninput = () => move(panel, panel.range.valueAsNumber);
    panel.numeric.oninput = () => {
      if (panel.numeric.value !== '' && panel.numeric.validity.valid) move(panel, panel.numeric.valueAsNumber);
    };
    panel.rawInput.oninput = () => { panel.rawOpacity = Number(panel.rawInput.value) / 100; update(panel); save(panel); };
    panel.blueInput.oninput = () => { panel.blueOpacity = Number(panel.blueInput.value) / 100; update(panel); save(panel); };
    panel.select.onchange = () => {
      if (!panel.select.value) return;
      const [id, at] = JSON.parse(panel.select.value) as [string, number];
      move(panel, at, id);
    };
    panel.record.onclick = async () => {
      const section = active(panel); if (!section || section.state !== 'draft' || recording) return;
      recording = true; panels.forEach(update);
      try {
        document = await recordCrossSection(section.id, document.revision);
      } catch (error) {
        panel.blueStatus.textContent = `Section was not recorded: ${String(error)}`;
        return;
      } finally { recording = false; panels.forEach(item => { item.record.disabled = active(item)?.state !== 'draft'; }); }
      panels.forEach(update); save(panel);
    };
  }
  host.insertAdjacentHTML('beforeend', '<p>Choose a position, then ask me to draft the blue outline. We refine it together '
    + 'before you record it. Inactive blue sections stay faint. Opposite-side YZ profiles normally match; '
    + 'local differences can be authored explicitly. Zero opacity hides a line.</p>');
  async function refresh() {
    if (refreshing || recording) return;
    refreshing = true;
    try {
      const next = await readCrossSections();
      if (next.revision !== document.revision || readFailed) {
        const previous = document; document = next;
        for (const panel of panels) {
          const changedDraft = [...next.sections].reverse().find(section => section.state === 'draft'
            && section.plane === panel.plane && sectionStations(section).some(at => Math.abs(at - panel.coordinate) < 0.5)
            && JSON.stringify(section) !== JSON.stringify(previous.sections.find(item => item.id === section.id)));
          updateBounds(panel); move(panel, panel.coordinate, changedDraft?.id ?? active(panel)?.id);
        }
      }
      readFailed = false;
    } catch (error) {
      readFailed = true; panels.forEach(panel => { panel.blueStatus.textContent = `Could not read blue sections: ${String(error)}`; });
    } finally { refreshing = false; }
  }
  panels.forEach(panel => { updateBounds(panel); move(panel, panel.coordinate, panel.activeId ?? undefined); });
  void refresh();
  const timer = window.setInterval(() => { if (!window.document.hidden) void refresh(); }, 2000);
  import.meta.hot?.dispose(() => window.clearInterval(timer));
  return {
    panels,
    sections: () => document.sections,
    setBounds(plane: SectionPlane, bounds: [number, number] | undefined) {
      const panel = panels.find(item => item.plane === plane)!;
      panel.bounds = bounds; updateBounds(panel); move(panel, panel.coordinate, panel.activeId ?? undefined);
    },
    status(plane: SectionPlane, text: string) {
      panels.find(item => item.plane === plane)!.rawStatus.textContent = text;
    },
  };
}
