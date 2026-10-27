import type { JSONContent } from '@tiptap/core';
import { ApiError, request } from './api';
import { isStaticSite } from './site-runtime';

export interface PurchaseFilter { category: string; tag: string; supplier: string; status: string; search: string }
export const emptyFilter = (): PurchaseFilter => ({ category: '', tag: '', supplier: '', status: '', search: '' });
export interface PurchaseRecord {
  id: string; name: string; product_id: string | null; role_id: string | null; category: string; tags: string[];
  supplier: string; url: string; notes: string; unit: string; required: number | null; owned: number; bought: number;
  unit_price: number | null; spent: number | null;
}
export interface PlanningDocument {
  version: 2; revision: number; content: JSONContent; purchases: Record<string, PurchaseRecord>;
}
export interface Operation {
  kind: 'purchase' | 'delete_purchase' | 'reset_purchase'; id: string; values?: Record<string, unknown>;
}
export interface PurchaseRow {
  record: PurchaseRecord; required: number | null; remaining: number | null; remaining_cost: number | null;
  status: string; uses: string[]; shared: boolean; legacy_owned: boolean; generated: boolean;
}
export interface Totals { spent: number; remaining: number; forecast: number; unknown_remaining: number; unknown_spent: number }
export interface PurchaseView { rows: PurchaseRow[]; totals: Totals; revision: number }
export interface Backup { version: 1; planning: PlanningDocument; project: unknown; products: unknown[] }
export interface Change { loaded?: boolean; purchases?: boolean }
export const id = () => crypto.randomUUID();
export function newPurchase(): PurchaseRecord {
  return { id: 'manual-' + id(), name: 'New item', product_id: null, role_id: null, category: '', tags: [],
    supplier: '', url: '', notes: '', unit: 'each', required: null, owned: 0, bought: 0, unit_price: null, spent: null };
}
type Save = { kind: 'content'; content: JSONContent } | { kind: 'purchase'; operation: Operation };

export class PlanningClient {
  document: PlanningDocument | null = null;
  status = isStaticSite ? 'Published snapshot · read only' : 'Loading plan…'; error = ''; blocked = false;
  private revision = 0;
  private queue: Save[] = [];
  private saving = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private listeners = new Set<(change: Change) => void>();
  private undoStack: Operation[] = [];
  private redoStack: Operation[] = [];
  private drafts = new Map<string, string>();
  private waiters: { resolve: () => void; reject: (error: Error) => void }[] = [];
  constructor() {
    window.addEventListener('beforeunload', event => {
      if (this.dirty) { event.preventDefault(); event.returnValue = ''; }
    });
  }
  get dirty() { return !isStaticSite && (this.queue.length > 0 || this.saving || this.blocked || this.drafts.size > 0); }
  get canUndoPurchase() { return !isStaticSite && this.undoStack.length > 0 && !this.blocked; }
  get canRedoPurchase() { return !isStaticSite && this.redoStack.length > 0 && !this.blocked; }
  subscribe(listener: (change: Change) => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  refreshPurchases() { this.notify({ purchases: true }); }
  private notify(change: Change = {}) { [...this.listeners].forEach(fn => fn(change)); }
  getDraft(key: string) { return this.drafts.get(key); }
  setDraft(key: string, dirty: boolean, value = '') {
    if (isStaticSite) return;
    if (dirty) this.drafts.set(key, value); else this.drafts.delete(key);
    if (!this.blocked && !this.saving && !this.queue.length) this.status = this.drafts.size ? 'Purchase cell not yet saved' : 'Saved locally';
    this.notify();
  }
  async read() {
    if (this.saving) { try { await this.flush(false); } catch { /* Explicit reload discards failed edits. */ } }
    clearTimeout(this.timer); this.blocked = true; this.status = 'Loading plan…'; this.notify();
    try {
      const next = await request<PlanningDocument>('planning');
      this.document = next; this.revision = next.revision;
      this.blocked = false; this.error = ''; this.queue = []; this.drafts.clear();
      this.undoStack = []; this.redoStack = []; this.status = isStaticSite ? 'Published snapshot · read only' : 'Saved locally';
      this.notify({ loaded: true, purchases: true });
    } catch (error) { this.fail(error); }
  }
  setContent(content: JSONContent) {
    this.ready(); this.document!.content = structuredClone(content);
    const last = this.queue.at(-1);
    if (last?.kind === 'content') last.content = structuredClone(content);
    else this.queue.push({ kind: 'content', content: structuredClone(content) });
    this.status = 'Saving…'; this.notify(); clearTimeout(this.timer);
    this.timer = setTimeout(() => { void this.drain(); }, 450);
  }
  private ready() {
    if (isStaticSite) throw new Error('The published plan is read only.');
    if (!this.document || this.blocked) throw new Error(this.error || 'The plan is not ready.');
  }
  mutate(operation: Operation, _structural = false, history = true) {
    this.ready();
    const before = this.document!.purchases[operation.id];
    const inverse: Operation = before
      ? { kind: 'purchase', id: operation.id, values: structuredClone(before) as unknown as Record<string, unknown> }
      : { kind: operation.id.startsWith('manual-') ? 'delete_purchase' : 'reset_purchase', id: operation.id };
    if (operation.kind === 'purchase') this.document!.purchases[operation.id] = structuredClone(operation.values) as unknown as PurchaseRecord;
    else delete this.document!.purchases[operation.id];
    if (history) { this.undoStack.push(inverse); this.redoStack = []; }
    // Content snapshots already in the queue precede this purchase. Never combine across it.
    this.queue.push({ kind: 'purchase', operation: structuredClone(operation) });
    this.status = 'Saving…'; clearTimeout(this.timer); this.notify(); void this.drain();
  }
  undoPurchase() { this.history(this.undoStack, this.redoStack); }
  redoPurchase() { this.history(this.redoStack, this.undoStack); }
  private history(from: Operation[], to: Operation[]) {
    this.ready(); const operation = from.pop(); if (!operation) return;
    const before = this.document!.purchases[operation.id];
    to.push(before ? { kind: 'purchase', id: operation.id, values: structuredClone(before) as unknown as Record<string, unknown> }
      : { kind: operation.id.startsWith('manual-') ? 'delete_purchase' : 'reset_purchase', id: operation.id });
    this.mutate(operation, false, false);
  }
  private fail(error: unknown) {
    this.error = error instanceof Error ? error.message : String(error); this.blocked = true;
    this.status = isStaticSite ? 'Cannot load published plan'
      : error instanceof ApiError && error.status === 409 ? 'Changed elsewhere — edits kept here' : 'Not saved — edits kept here';
    this.waiters.splice(0).forEach(w => w.reject(new Error(this.error))); this.notify();
  }
  private async drain() {
    if (this.saving || this.blocked || !this.queue.length) return;
    this.saving = true; let purchases = false;
    try {
      while (this.queue.length) {
        const next = this.queue.shift()!;
        try {
          const saved = next.kind === 'content'
            ? await request<PlanningDocument>('planning/content', 'PUT', { revision: this.revision, content: next.content })
            : await request<PlanningDocument>('planning/operations', 'POST', { revision: this.revision, operation: next.operation });
          this.revision = saved.revision; if (this.document) this.document.revision = saved.revision;
          purchases ||= next.kind === 'purchase';
        } catch (error) { this.queue.unshift(next); throw error; }
      }
      this.error = ''; this.status = this.drafts.size ? 'Purchase cell not yet saved' : 'Saved locally';
    } catch (error) { this.fail(error); }
    finally {
      this.saving = false;
      if (!this.blocked) this.waiters.splice(0).forEach(w => w.resolve());
      this.notify({ purchases });
    }
  }
  async flush(checkDrafts = true): Promise<void> {
    if (isStaticSite) return;
    clearTimeout(this.timer);
    if (this.blocked) throw new Error(this.error || 'The plan is not ready.');
    if (checkDrafts && this.drafts.size) throw new Error('Finish or correct the active purchase cell first.');
    if (!this.queue.length && !this.saving) return;
    return new Promise<void>((resolve, reject) => { this.waiters.push({ resolve, reject }); void this.drain(); });
  }
  async purchases() { await this.flush(false); return request<PurchaseView>('purchases'); }
  async restore(bundle: Backup) {
    if (isStaticSite) throw new Error('The published plan is read only.');
    if (!this.blocked) await this.flush();
    let revision = 0;
    try { revision = (await request<PlanningDocument>('planning')).revision; }
    catch (error) { if (!(error instanceof ApiError) || error.status !== 422) throw error; }
    const next = await request<PlanningDocument>('planning/restore', 'POST', { revision, backup: bundle });
    clearTimeout(this.timer); this.queue = []; this.drafts.clear(); this.blocked = false; this.error = '';
    this.document = next; this.revision = next.revision; this.undoStack = []; this.redoStack = [];
    this.status = 'Backup restored'; this.notify({ loaded: true, purchases: true });
  }
}
