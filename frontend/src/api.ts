import { isStaticSite, readSnapshotPart } from './site-runtime';
import type { MannequinSettings } from './mannequin';

export const readOnly = isStaticSite;
export type Parameters = Record<string, number>;
export interface FieldMetadata {
  title: string;
  default: number;
  unit: string;
  group: string[];
  control?: 'position';
  options?: { value: number; label: string }[];
  material?: string;
  description?: string;
  reason?: string;
  minimum?: number;
  exclusiveMinimum?: number;
  maximum?: number;
  exclusiveMaximum?: number;
}
export interface ParameterResponse {
  session_id: string;
  parameters: Parameters;
  schema: { properties: Record<string, FieldMetadata> };
  viewer_url: string;
  mannequins?: MannequinSettings | null;
  errors?: Record<string, string>;
  adjustments?: Record<string, string>;
}
export interface MutationResponse { session_id: string; requested_revision: number }
export interface ModelStatus extends MutationResponse {
  published_revision: number | null;
  state: 'idle' | 'regenerating' | 'ready' | 'failed';
  error: { message: string } | null;
}
export interface Api {
  readonly readOnly?: boolean;
  getParameters(): Promise<ParameterResponse>;
  previewParameters(parameters: Parameters): Promise<ParameterResponse>;
  getStatus(): Promise<ModelStatus>;
  putParameters(parameters: Parameters): Promise<ModelStatus>;
  loadModel(): Promise<ModelStatus>;
  regenerate(): Promise<ModelStatus>;
  setPosition(name: string, percent: number): Promise<Parameters>;
  setPositions(positions: Parameters): Promise<Parameters>;
}
export class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  if (isStaticSite) {
    if (method !== 'GET') throw new Error('This exported snapshot is read-only.');
    if (!['parameters', 'materials', 'cutting', 'purchases'].includes(path)) {
      throw new Error(`This action requires the local application: ${path}`);
    }
    return readSnapshotPart<T>(path);
  }
  const response = await fetch(`/api/v1/${path}`, {
    method,
    ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    try {
      const data: { detail?: string | { loc?: (string | number)[]; msg?: string }[] } = await response.json();
      if (typeof data.detail === 'string') message = data.detail;
      else if (Array.isArray(data.detail)) {
        message = data.detail.map(issue => `${issue.loc?.slice(1).join('.') || 'Input'}: ${issue.msg}`).join('; ');
      }
    } catch { /* A non-JSON error still has a useful HTTP status. */ }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}
export const getParameters = () => request<ParameterResponse>('parameters');
export const previewParameters = (parameters: Parameters) => request<ParameterResponse>('parameters/preview', 'POST', parameters);
export const getStatus = async (): Promise<ModelStatus> => {
  if (!isStaticSite) return request<ModelStatus>('model/status');
  const data = await getParameters();
  return { session_id: data.session_id, requested_revision: 0, published_revision: 0, state: 'ready', error: null };
};
export const putParameters = (parameters: Parameters) => request<ModelStatus>('parameters', 'PUT', parameters);
export const loadModel = () => request<ModelStatus>('model/load', 'POST');
export const regenerate = () => request<ModelStatus>('model/regenerate', 'POST');
export const setPositions = (positions: Parameters) => request<Parameters>('model/position', 'PATCH', positions);
export const setPosition = (name: string, percent: number) => setPositions({ [name]: percent });
export const saveMannequins = (settings: MannequinSettings) =>
  request<MannequinSettings>('model/mannequins', 'PUT', settings);
