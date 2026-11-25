/** Independent section stations with shared raw/authored visibility. */
import { readCrossSections, recordCrossSection, type AuthoredSection, type SectionDocument,
  type SectionPlane } from './cross-section-api';

export function sectionStations(section: AuthoredSection): number[] {
  if (section.plane === 'XZ') return [section.y_mm!];
  if (section.plane === 'XY') return [section.z_mm!];
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
  let centreX = 750;
  const panels: Panel[] = [];
  const opacityKey = 'campervan.cross-sections.opacity';
  const opacity = JSON.parse(localStorage.getItem(opacityKey)
    ?? localStorage.getItem('campervan.cross-sections.yz')
    ?? localStorage.getItem('campervan.cross-sections') ?? '{}');
  const rawOpacity = Number(opacity.rawOpacity ?? 100) / 100;
  const blueOpacity = Number(opacity.blueOpacity ?? 100) / 100;
  localStorage.setItem(opacityKey, JSON.stringify({ rawOpacity: rawOpacity * 100, blueOpacity: blueOpacity * 100 }));
  const axis = (plane: SectionPlane) => plane === 'XZ' ? 'Y' : plane === 'YZ' ? 'X' : 'Z';
  const displayCoordinate = (plane: SectionPlane, value: number) => plane === 'YZ' ? value - centreX : value;
  const worldCoordinate = (plane: SectionPlane, value: number) => plane === 'YZ' ? value + centreX : value;
  const coordinateLabel = (plane: SectionPlane, value: number) => {
    const displayed = displayCoordinate(plane, value);
    return plane === 'YZ' && displayed > 0 ? `+${displayed}` : String(displayed);
  };
  const active = (panel: Panel) => document.sections.find(section => section.plane === panel.plane
    && section.id === panel.activeId && sectionStations(section).some(at => Math.abs(at - panel.coordinate) < 0.5));
  function save(panel: Panel) {
    localStorage.setItem(panel.key, JSON.stringify({ coordinate: displayCoordinate(panel.plane, panel.coordinate),
      ...(panel.plane === 'YZ' ? { origin: 'centre' } : {}),
      ...(panel.plane === 'XZ' ? { y: panel.coordinate } : {}), activeId: panel.activeId }));
  }
  function updateBounds(panel: Panel) {
    const stations = document.sections.filter(section => section.plane === panel.plane).flatMap(sectionStations);
    const low = panel.plane === 'YZ' ? centreX - 800
      : Math.floor(Math.min(panel.bounds?.[0] ?? Math.min(0, panel.coordinate), ...stations));
    const high = panel.plane === 'YZ' ? centreX + 800 : Math.ceil(Math.max(panel.bounds?.[1]
      ?? Math.max(panel.coordinate, 2000), ...stations));
    for (const input of [panel.range, panel.numeric]) {
      input.min = String(displayCoordinate(panel.plane, low));
      input.max = String(displayCoordinate(panel.plane, high)); input.disabled = !panel.bounds && !stations.length;
    }
    panel.coordinate = Math.max(low, Math.min(high, panel.coordinate));
  }
  function update(panel: Panel) {
    const current = active(panel), coordinate = panel.coordinate, coordinateAxis = axis(panel.plane);
    panel.range.value = panel.numeric.value = String(displayCoordinate(panel.plane, coordinate));
    panel.range.setAttribute('aria-valuetext', `${coordinateAxis} ${coordinateLabel(panel.plane, coordinate)} millimetres`
      + (panel.plane === 'YZ' ? ' from vehicle centreline' : panel.plane === 'XY' ? ' height' : ' from rear datum'));
    const choices = document.sections.filter(section => section.plane === panel.plane)
      .flatMap(section => sectionStations(section).map(at => ({ section, at }))).sort((a, b) => a.at - b.at);
    panel.select.replaceChildren(new Option('At current position', ''), ...choices.map(({ section, at }) => {
      const outside = panel.plane === 'YZ' && Math.abs(displayCoordinate(panel.plane, at)) > 800;
      const option = new Option(`${coordinateAxis} ${coordinateLabel(panel.plane, at)} mm · ${section.label || section.state}`
        + (section.label ? ` · ${section.state}` : '') + (outside ? ' · outside ±800 mm' : ''), JSON.stringify([section.id, at]));
      option.disabled = outside;
      return option;
    }));
    panel.select.value = current ? JSON.stringify([current.id, sectionStations(current)
      .find(at => Math.abs(at - coordinate) < 0.5)!]) : '';
    panel.record.hidden = !current || current.state !== 'draft';
    panel.record.disabled = recording || !current || current.state === 'recorded';
    panel.record.textContent = current?.plane === 'YZ' && sectionStations(current).length > 1
      ? 'Record pair' : 'Record';
    panel.blueStatus.textContent = '';
    panel.blueStatus.hidden = true;
    changed(panel);
  }
  function move(panel: Panel, value: number, selectedId?: string) {
    if (!Number.isFinite(value)) return;
    panel.coordinate = Math.max(worldCoordinate(panel.plane, Number(panel.range.min)),
      Math.min(worldCoordinate(panel.plane, Number(panel.range.max)), value));
    panel.activeId = selectedId ?? [...document.sections].reverse().find(section => section.plane === panel.plane
      && sectionStations(section).some(at => Math.abs(at - panel.coordinate) < 0.5))?.id ?? null;
    update(panel); save(panel);
  }
  for (const plane of ['XZ', 'YZ', 'XY'] as const) {
    const coordinateAxis = axis(plane);
    const title = plane === 'XZ' ? 'XZ · transverse' : plane === 'YZ' ? 'YZ · longitudinal' : 'XY · horizontal';
    const direction = plane === 'XZ' ? 'Rear → front' : plane === 'YZ' ? 'Left (−) → right (+)' : 'Bottom → top';
    host.insertAdjacentHTML('beforeend', `
      <section class="section-family" data-section-plane="${plane}" aria-labelledby="section-${plane}-heading">
        <h4 id="section-${plane}-heading">${title}</h4>
        <input type="range" min="0" max="2000" step="1" data-section-position
          aria-label="${title} position ${coordinateAxis} in millimetres" disabled />
        <label class="section-station">${direction}: ${coordinateAxis} =
          <input type="number" step="1" data-section-position-number
            aria-label="${title} position ${coordinateAxis} in millimetres" disabled /> mm
        </label>
        <div class="section-blue-actions"><label for="section-${plane}-saved">Blue sections</label>
          <button type="button" data-section-record hidden>Record</button></div>
        <select id="section-${plane}-saved" data-section-saved aria-label="${plane} blue sections"></select>
        <p data-section-raw-status role="status" hidden></p>
        <p data-section-blue-status role="status" aria-live="polite" hidden></p>
      </section>`);
    const family = host.querySelector<HTMLElement>(`[data-section-plane="${plane}"]`)!;
    const find = <T extends HTMLElement>(selector: string) => family.querySelector<T>(selector)!;
    const key = plane === 'XZ' ? 'campervan.cross-sections' : `campervan.cross-sections.${plane.toLowerCase()}`;
    const saved = JSON.parse(localStorage.getItem(key) ?? '{}');
    const previous = plane === 'YZ' ? saved.origin === 'centre' ? saved.coordinate : 0 : saved.coordinate ?? saved.y;
    const panel: Panel = {
      plane, coordinate: worldCoordinate(plane, Number.isFinite(previous) ? previous : plane === 'XZ' ? 1000 : 0),
      activeId: plane === 'YZ' && saved.origin !== 'centre' ? null : saved.activeId ?? null,
      rawOpacity, blueOpacity, key,
      range: find('[data-section-position]'), numeric: find('[data-section-position-number]'),
      select: find('[data-section-saved]'),
      record: find('[data-section-record]'), rawStatus: find('[data-section-raw-status]'), blueStatus: find('[data-section-blue-status]'),
    };
    panels.push(panel);
    panel.range.oninput = () => move(panel, worldCoordinate(plane, panel.range.valueAsNumber));
    panel.numeric.oninput = () => {
      if (panel.numeric.value !== '' && panel.numeric.validity.valid) move(panel, worldCoordinate(plane, panel.numeric.valueAsNumber));
    };
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
        panel.blueStatus.hidden = false;
        return;
      } finally { recording = false; panels.forEach(item => { item.record.disabled = active(item)?.state !== 'draft'; }); }
      panels.forEach(update); save(panel);
    };
  }
  host.insertAdjacentHTML('beforeend', `
    <section class="section-opacity" aria-labelledby="section-opacity-heading">
      <h4 id="section-opacity-heading">Section opacity</h4>
      <label class="section-raw">Green · raw scan <output></output>
        <input type="range" min="0" max="100" step="5" data-section-opacity="rawOpacity" />
      </label>
      <label class="section-blue">Blue · authored <output></output>
        <input type="range" min="0" max="100" step="5" data-section-opacity="blueOpacity" />
      </label>
    </section>`);
  for (const property of ['rawOpacity', 'blueOpacity'] as const) {
    const input = host.querySelector<HTMLInputElement>(`[data-section-opacity="${property}"]`)!;
    const showOpacity = () => {
      input.value = String(Math.round(panels[0][property] * 100));
      input.setAttribute('aria-valuetext', input.value + ' percent');
      input.parentElement!.querySelector('output')!.value = input.value + '%';
    };
    showOpacity();
    input.oninput = () => {
      const value = Number(input.value) / 100;
      panels.forEach(panel => { panel[property] = value; changed(panel); });
      showOpacity();
      localStorage.setItem(opacityKey, JSON.stringify({
        rawOpacity: panels[0].rawOpacity * 100, blueOpacity: panels[0].blueOpacity * 100,
      }));
    };
  }
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
      readFailed = true; panels.forEach(panel => {
        panel.blueStatus.textContent = `Could not read blue sections: ${String(error)}`;
        panel.blueStatus.hidden = false;
      });
    } finally { refreshing = false; }
  }
  panels.forEach(panel => { updateBounds(panel); move(panel, panel.coordinate, panel.activeId ?? undefined); });
  void refresh();
  const timer = window.setInterval(() => { if (!window.document.hidden && !container.closest('[inert]')) void refresh(); }, 2000);
  import.meta.hot?.dispose(() => window.clearInterval(timer));
  return {
    panels,
    sections: () => document.sections,
    displayCoordinate,
    rawStations(plane: SectionPlane, coordinate: number) {
      const opposite = 2 * centreX - coordinate;
      return plane === 'YZ' && Math.abs(opposite - coordinate) > 0.001 ? [coordinate, opposite] : [coordinate];
    },
    setCentreline(value: number) {
      if (!Number.isFinite(value) || value === centreX) return;
      const panel = panels.find(item => item.plane === 'YZ')!;
      const offset = panel.coordinate - centreX;
      centreX = value; panel.coordinate = centreX + offset;
      updateBounds(panel); move(panel, panel.coordinate);
    },
    setBounds(plane: SectionPlane, bounds: [number, number] | undefined) {
      const panel = panels.find(item => item.plane === plane)!;
      panel.bounds = bounds; updateBounds(panel); move(panel, panel.coordinate, panel.activeId ?? undefined);
    },
    status(plane: SectionPlane, text: string) {
      const status = panels.find(item => item.plane === plane)!.rawStatus;
      status.textContent = text;
      status.hidden = !text;
    },
  };
}
