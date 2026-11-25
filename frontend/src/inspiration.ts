import { request } from './api';
import { onTab } from './tabs';
import './inspiration.css';

interface Photo {
  id: string;
  title: string;
  source: string;
  tags: string[];
  description?: string;
  credit?: string;
  favourite?: boolean;
}

const photoUrl = (photo: Photo) => `/api/v1/inspiration/images/${photo.id}.webp`;

function sourceLink(photo: Photo) {
  const link = document.createElement('a');
  link.href = photo.source;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  const host = new URL(photo.source).hostname.replace(/^www\./, '');
  link.textContent = `${host} ↗`;
  link.setAttribute('aria-label', `Source for ${photo.title} on ${host} (opens in a new tab)`);
  return link;
}

export function setupInspiration(panel: HTMLElement) {
  panel.innerHTML = `
    <div class="inspiration-heading"><h2>Inspiration</h2><span data-count aria-live="polite"></span></div>
    <div class="inspiration-filters" role="group" aria-label="Filter photos by tag"></div>
    <p role="status" class="inspiration-status"></p>
    <div class="inspiration-grid"></div>
    <dialog aria-label="Enlarged interior photograph" class="inspiration-dialog">
      <button type="button" class="inspiration-heart"></button>
      <button type="button" class="inspiration-close" aria-label="Close photograph" title="Close (Esc)" autofocus>×</button>
      <img class="inspiration-full" alt="">
      <div class="inspiration-controls">
        <div class="inspiration-caption" aria-live="polite"></div>
        <button type="button" data-step="-1" aria-label="Previous photograph" aria-keyshortcuts="ArrowLeft" title="Previous (←)">←</button>
        <button type="button" data-step="1" aria-label="Next photograph" aria-keyshortcuts="ArrowRight" title="Next (→)">→</button>
      </div>
      <p role="status" class="inspiration-save-error"></p>
    </dialog>`;
  const grid = panel.querySelector<HTMLElement>('.inspiration-grid')!;
  const filters = panel.querySelector<HTMLElement>('.inspiration-filters')!;
  const status = panel.querySelector<HTMLElement>('[role=status]')!;
  const count = panel.querySelector<HTMLElement>('[data-count]')!;
  const dialog = panel.querySelector<HTMLDialogElement>('dialog')!;
  const full = dialog.querySelector<HTMLImageElement>('img')!;
  const fullHeart = dialog.querySelector<HTMLButtonElement>('.inspiration-heart')!;
  const saveError = dialog.querySelector<HTMLElement>('.inspiration-save-error')!;
  const caption = dialog.querySelector<HTMLElement>('.inspiration-caption')!;
  const steps = dialog.querySelectorAll<HTMLButtonElement>('[data-step]');
  let catalogue: Photo[] = [];
  let photos: Photo[] = [];
  const selectedTags = new Set<string>();
  const savingFavourites = new Set<Photo>();
  let index = 0;
  let loaded = false;
  let loading = false;

  function updateCount() {
    count.textContent = selectedTags.size ? `${photos.length} of ${catalogue.length} photos`
      : `${photos.length} ${photos.length === 1 ? 'photo' : 'photos'}`;
    if (!photos.length) status.textContent = catalogue.length ? 'No photos match these tags.' : 'The gallery is empty.';
  }

  function renderGrid() {
    photos = selectedTags.size ? catalogue.filter(photo => photo.tags.some(tag => selectedTags.has(tag))) : catalogue;
    grid.replaceChildren(...photos.map(card));
    updateCount();
  }

  function setupFilters() {
    const tags = new Set(catalogue.flatMap(photo => photo.tags));
    filters.replaceChildren();
    for (const tag of ['', ...tags]) {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.tag = tag;
      button.textContent = tag || 'All photos';
      button.setAttribute('aria-pressed', String(!tag));
      button.onclick = () => {
        if (!tag) selectedTags.clear();
        else if (selectedTags.has(tag)) selectedTags.delete(tag);
        else selectedTags.add(tag);
        for (const control of filters.querySelectorAll('button')) {
          const value = control.dataset.tag!;
          control.setAttribute('aria-pressed', String(value ? selectedTags.has(value) : !selectedTags.size));
        }
        status.textContent = '';
        renderGrid();
      };
      filters.append(button);
    }
  }

  function photoTags(photo: Photo) {
    const tags = document.createElement('small');
    tags.className = 'inspiration-tags';
    tags.textContent = photo.tags.join(' · ');
    return tags;
  }

  function updateHeart(button: HTMLButtonElement, photo: Photo) {
    button.setAttribute('aria-pressed', String(Boolean(photo.favourite)));
    button.setAttribute('aria-disabled', String(savingFavourites.has(photo)));
    button.title = photo.favourite ? 'Remove from favourites' : 'Add to favourites';
  }

  function syncHearts(photo: Photo) {
    for (const button of panel.querySelectorAll<HTMLButtonElement>(`[data-heart="${photo.id}"]`)) {
      updateHeart(button, photo);
    }
  }

  function heartButton(photo: Photo, button = document.createElement('button')) {
    button.type = 'button';
    button.className = 'inspiration-heart';
    button.dataset.heart = photo.id;
    button.setAttribute('aria-label', `Favourite: ${photo.title}, ${photo.description || 'photo'}`);
    button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5 3.6 12a5.4 5.4 0 0 1 8.4-6.7 5.4 5.4 0 0 1 8.4 6.7Z"/></svg>';
    updateHeart(button, photo);
    button.onclick = async () => {
      if (savingFavourites.has(photo)) return;
      savingFavourites.add(photo);
      syncHearts(photo);
      status.textContent = '';
      saveError.textContent = '';
      try {
        photo.favourite = await request<boolean>(`inspiration/${photo.id}/favourite`, 'PUT', { favourite: !photo.favourite });
      } catch (error) {
        const message = `Could not save the heart for ${photo.title}. ${String(error)}`;
        status.textContent = message;
        if (dialog.open) saveError.textContent = message;
      } finally {
        savingFavourites.delete(photo);
        syncHearts(photo);
      }
    };
    return button;
  }

  function showPhoto(next: number) {
    index = (next + photos.length) % photos.length;
    const photo = photos[index];
    heartButton(photo, fullHeart);
    saveError.textContent = '';
    full.src = photoUrl(photo);
    full.alt = photo.description || photo.title;
    const title = document.createElement('strong');
    title.textContent = photo.title;
    const position = document.createElement('span');
    position.textContent = `${index + 1} / ${photos.length}`;
    caption.replaceChildren(position, title);
    if (photo.description) {
      const description = document.createElement('span');
      description.textContent = photo.description;
      caption.append(description);
    }
    caption.append(photoTags(photo), sourceLink(photo));
    if (photo.credit) {
      const credit = document.createElement('span');
      credit.textContent = `Photo: ${photo.credit}`;
      caption.append(credit);
    }
    for (const step of steps) step.disabled = photos.length < 2;
    if (!dialog.open) dialog.showModal();
  }
  for (const step of steps) step.onclick = () => showPhoto(index + Number(step.dataset.step));
  dialog.querySelector<HTMLButtonElement>('.inspiration-close')!.onclick = () => dialog.close();
  dialog.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      event.stopPropagation();
      showPhoto(index + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });

  function card(photo: Photo) {
    const item = document.createElement('article');
    item.className = 'inspiration-card';
    const open = document.createElement('button');
    open.type = 'button'; open.className = 'inspiration-preview';
    open.setAttribute('aria-label', `Enlarge ${photo.description || photo.title}`);
    open.onclick = () => showPhoto(photos.indexOf(photo));
    const image = new Image();
    image.loading = 'lazy'; image.decoding = 'async'; image.src = photoUrl(photo);
    image.alt = photo.description || photo.title;
    open.append(image);
    const remove = document.createElement('button');
    remove.type = 'button'; remove.className = 'inspiration-remove';
    remove.title = `Remove ${photo.title} from the gallery`;
    remove.setAttribute('aria-label', remove.title);
    remove.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/></svg>';
    remove.onclick = async () => {
      remove.disabled = true;
      try {
        await request(`inspiration/${photo.id}`, 'DELETE');
        const removed = photos.indexOf(photo);
        const enlarged = dialog.open ? photos[index] : undefined;
        const currentCard = grid.children[removed];
        const restoreFocus = currentCard?.contains(document.activeElement) || document.activeElement === document.body;
        catalogue = catalogue.filter(entry => entry.id !== photo.id);
        photos = photos.filter(entry => entry.id !== photo.id);
        currentCard?.remove();
        status.textContent = `Removed ${photo.title}.`;
        updateCount();
        if (enlarged) {
          if (photos.length) showPhoto(enlarged === photo ? Math.min(index, photos.length - 1) : photos.indexOf(enlarged));
          else dialog.close();
        } else if (restoreFocus && removed >= 0) {
          const neighbour = grid.children[Math.min(removed, photos.length - 1)];
          (neighbour?.querySelector('button') ?? filters.querySelector('button'))?.focus();
        }
      } catch (error) {
        status.textContent = String(error);
        remove.disabled = false;
      }
    };
    const title = document.createElement('h3');
    title.textContent = photo.title;
    item.append(open, heartButton(photo), remove, title, photoTags(photo), sourceLink(photo));
    return item;
  }

  onTab(async tab => {
    if (tab !== 'inspiration') {
      if (dialog.open) dialog.close();
      return;
    }
    if (loaded || loading) return;
    loading = true;
    status.textContent = 'Loading photographs…';
    try {
      catalogue = await request<Photo[]>('inspiration');
      setupFilters();
      status.textContent = '';
      renderGrid();
      loaded = true;
    } catch (error) {
      status.textContent = String(error);
    } finally {
      loading = false;
    }
  });
}
