import { request } from './api';
import './apriltags.css';

interface Layout { columns: number; rows: number; per_page: number; pages: number; marker_length_mm: number }

export function setupAprilTags(panel: HTMLElement) {
  panel.innerHTML = `
    <div class="apriltags-content">
      <h2>AprilTags</h2>
      <p>Generate printable 36h11 tags. The layout fits as many tags as possible on each page at the exact size you choose.</p>
      <form id="apriltags-form">
        <fieldset><legend>Tags</legend>
          <label for="tag-size">Printed width including white border (mm)</label>
          <input id="tag-size" name="size_mm" type="number" min="10" max="1000" step="0.1" value="100" required />
          <label for="tag-count">Number of tags</label>
          <input id="tag-count" name="count" type="number" min="1" max="587" step="1" value="40" required />
          <label for="tag-start">Starting ID</label>
          <input id="tag-start" name="start_id" type="number" min="0" max="586" step="1" value="1" required />
        </fieldset>
        <fieldset><legend>Paper and spacing</legend>
          <label for="tag-paper">Paper size</label>
          <select id="tag-paper"><option value="210,297">A4 (210 × 297 mm)</option>
            <option value="297,420">A3 (297 × 420 mm)</option>
            <option value="215.9,279.4">US Letter (215.9 × 279.4 mm)</option><option value="custom">Custom</option></select>
          <label for="tag-paper-width">Paper width (mm)</label>
          <input id="tag-paper-width" name="paper_width_mm" type="number" min="50" max="1500" step="0.1" value="210" required />
          <label for="tag-paper-height">Paper height (mm)</label>
          <input id="tag-paper-height" name="paper_height_mm" type="number" min="50" max="1500" step="0.1" value="297" required />
          <label for="tag-margin">Page margin (mm)</label>
          <input id="tag-margin" name="margin_mm" type="number" min="1" max="100" step="0.1" value="5" required />
          <label for="tag-gap">Gap between tags (mm)</label>
          <input id="tag-gap" name="gap_mm" type="number" min="0" max="100" step="0.1" value="0" required />
        </fieldset>
        <fieldset><legend>Print marks</legend>
          <label class="tag-check"><input name="cut_lines" type="checkbox" checked /> Thin cut lines</label>
          <label class="tag-check"><input id="tag-crosshair" name="crosshair" type="checkbox" checked /> Grey centre circle and cross</label>
          <label for="tag-diameter">Centre circle diameter (mm)</label>
          <input id="tag-diameter" name="crosshair_diameter_mm" type="number" min="0.1" max="500" step="0.1" value="10" required />
        </fieldset>
        <div class="tag-summary" role="status" aria-live="polite" aria-atomic="true"></div>
        <p class="tag-help">Each tag keeps its full white border and has a 6 mm ID label strip below it.
          Print the PDF at <strong>100% / actual size</strong>.</p>
        <p class="tag-help">The centre mark overlays the encoded pattern and can affect detection. Turn it off for an unmodified tag.</p>
        <button type="submit">Generate PDF</button>
        <p class="tag-feedback" role="status" aria-live="polite" aria-atomic="true"></p>
        <p class="tag-error" role="alert"></p>
      </form>
    </div>`;
  const form = panel.querySelector<HTMLFormElement>('form')!;
  const summary = panel.querySelector<HTMLElement>('.tag-summary')!;
  const error = panel.querySelector<HTMLElement>('.tag-error')!;
  const feedback = panel.querySelector<HTMLElement>('.tag-feedback')!;
  const button = panel.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  const paper = panel.querySelector<HTMLSelectElement>('#tag-paper')!;
  const width = panel.querySelector<HTMLInputElement>('#tag-paper-width')!;
  const height = panel.querySelector<HTMLInputElement>('#tag-paper-height')!;
  const crosshair = panel.querySelector<HTMLInputElement>('#tag-crosshair')!;
  const diameter = panel.querySelector<HTMLInputElement>('#tag-diameter')!;
  function settings() {
    const data: Record<string, number | boolean> = {};
    for (const input of form.querySelectorAll<HTMLInputElement>('input')) {
      data[input.name] = input.type === 'checkbox' ? input.checked : input.disabled ? 10 : input.valueAsNumber;
    }
    return data;
  }
  let revision = 0;
  let timer: number;
  async function updateLayout() {
    const current = ++revision;
    diameter.disabled = !crosshair.checked;
    error.textContent = '';
    summary.textContent = '';
    if (!form.checkValidity()) return;
    try {
      const layout = await request<Layout>('apriltags/layout', 'POST', settings());
      if (current !== revision) return;
      summary.textContent = `${layout.columns} columns × ${layout.rows} rows · ${layout.per_page} tags per page · `
        + `${layout.pages} ${layout.pages === 1 ? 'page' : 'pages'}. `
        + `RTAB-Map Marker/Length: ${Number((layout.marker_length_mm / 1000).toPrecision(10))} m `
        + `(${Number(layout.marker_length_mm.toPrecision(10))} mm black square).`;
    } catch (reason) {
      if (current === revision) error.textContent = String(reason instanceof Error ? reason.message : reason);
    }
  }
  paper.addEventListener('change', () => {
    if (paper.value !== 'custom') [width.value, height.value] = paper.value.split(',');
    void updateLayout();
  });
  for (const input of [width, height]) input.addEventListener('input', () => { paper.value = 'custom'; });
  form.addEventListener('input', () => {
    ++revision;
    summary.textContent = '';
    feedback.textContent = '';
    window.clearTimeout(timer);
    timer = window.setTimeout(() => { void updateLayout(); }, 150);
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    button.disabled = true;
    error.textContent = '';
    feedback.textContent = 'Generating PDF…';
    const values = settings();
    try {
      const response = await fetch('/api/v1/apriltags/pdf', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(typeof data.detail === 'string' ? data.detail
          : Array.isArray(data.detail) ? data.detail.map((issue: { msg: string }) => issue.msg).join('; ')
            : `Could not generate PDF (${response.status}).`);
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url;
      link.download = `apriltags-36h11-${values.start_id}-${Number(values.start_id) + Number(values.count) - 1}.pdf`;
      document.body.append(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      feedback.textContent = 'PDF generated. Print at 100% / actual size.';
    } catch (reason) {
      feedback.textContent = '';
      error.textContent = String(reason instanceof Error ? reason.message : reason);
    } finally {
      button.disabled = false;
    }
  });
  void updateLayout();
}
