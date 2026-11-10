import { createSidePanel } from './side-panel';
import type { ScanResult } from './scan-library-api';
import type { CapturePurpose } from './scan-import-api';

interface CaptureReviewHost {
  capture(): ScanResult | undefined;
  loading(): boolean;
  addCaptures(purpose: CapturePurpose): Promise<void>;
}

export function createScanWorkflowPanel(host: CaptureReviewHost) {
  const side = createSidePanel({ id: 'scan-workflow', title: 'Review and improve scan' });
  side.element.classList.add('scan-workflow-panel');
  const stages = [
    { id: 'review_capture', label: 'Review capture' },
    { id: 'understand_scene', label: 'Understand the scene' },
    { id: 'improve_layout', label: 'Improve tag layout' },
    { id: 'take_measurements', label: 'Take measurements' },
    { id: 'check_measurements', label: 'Check measurements' },
    { id: 'update_reconstruction', label: 'Update reconstruction' },
  ];
  const progress = document.createElement('ol'); progress.className = 'scan-workflow-stages';
  progress.setAttribute('aria-label', 'Scan workflow progress');
  for (const [index, stage] of stages.entries()) {
    const item = document.createElement('li'); item.dataset.stage = stage.id;
    const marker = document.createElement('span'); marker.className = 'scan-workflow-marker';
    marker.textContent = String(index + 1); marker.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span'); label.className = 'scan-workflow-label'; label.textContent = stage.label;
    const state = document.createElement('span'); state.className = 'scan-workflow-step-state';
    state.textContent = index === 0 ? 'Current' : 'Upcoming';
    if (index === 0) item.setAttribute('aria-current', 'step');
    else {
      item.title = 'Available in a later stage of this workflow\'s implementation';
      item.setAttribute('aria-describedby', 'scan-workflow-upcoming');
    }
    item.append(marker, label, state); progress.append(item);
  }
  side.body.append(progress);
  const count = document.createElement('p'); count.className = 'scan-workflow-step-count'; count.textContent = 'Step 1 of 6';
  const title = document.createElement('h3'); title.className = 'scan-workflow-title'; title.textContent = 'Review capture';
  const identity = document.createElement('p'); identity.className = 'scan-workflow-result';
  const description = document.createElement('p'); description.className = 'scan-workflow-description';
  description.textContent = 'Inspect the surface and located tags. Create a coarse depth preview or reconstruct detail from selected photographs. Original photos need no preview first.';
  const actions = document.createElement('div'); actions.className = 'scan-capture-actions';
  const buttons: HTMLButtonElement[] = [];
  for (const [purpose, label] of [
    ['preview', 'Create quick preview…'], ['photographic', 'Create detailed reconstruction…'],
  ] as const) {
    const add = document.createElement('button'); add.type = 'button'; add.className = 'scan-workflow-primary';
    add.textContent = label; add.setAttribute('aria-haspopup', 'dialog');
    add.onclick = async () => {
      adding = true; error.textContent = ''; refresh();
      try { await host.addCaptures(purpose); }
      catch (reason) { error.textContent = reason instanceof Error ? reason.message : String(reason); }
      finally { adding = false; refresh(); }
    };
    buttons.push(add); actions.append(add);
  }
  const note = document.createElement('p'); note.id = 'scan-workflow-upcoming'; note.className = 'scan-workflow-description';
  note.textContent = 'Scene understanding and the remaining steps are upcoming. You can inspect and extend your capture now.';
  const error = document.createElement('p'); error.setAttribute('role', 'alert');
  side.body.append(count, title, identity, description, actions, note);
  side.status.append(error);
  let adding = false;
  let key: string | undefined;
  function refresh() {
    const capture = host.capture();
    if (key !== capture?.key) { key = capture?.key; error.textContent = ''; }
    identity.textContent = capture
      ? [capture.group_name, capture.display_name].filter(Boolean).join(' · ')
      : 'Choose a reconstructed result from the Result selector, or add captures through Manage scans.';
    for (const button of buttons) button.disabled = adding || host.loading() || !capture;
    side.element.setAttribute('aria-busy', String(host.loading()));
  }
  return {
    openReview() { refresh(); side.open(); },
    refresh,
    hide() { side.close(); },
  };
}
