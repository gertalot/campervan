export type Parameters = Record<string, number>;
export interface FieldMetadata {
  title: string;
  default: number;
  unit: string;
  group: string[];
  control?: 'position';
  description?: string;
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
}
export interface MutationResponse { session_id: string; requested_revision: number }
export interface ModelStatus extends MutationResponse {
  model_paths: string[];
  published_revision: number | null;
  state: 'idle' | 'regenerating' | 'ready' | 'failed';
  error: { message: string } | null;
}
export interface Api {
  getParameters(): Promise<ParameterResponse>;
  getStatus(): Promise<ModelStatus>;
  putParameters(parameters: Parameters): Promise<MutationResponse>;
  regenerate(): Promise<MutationResponse>;
  setPosition(percent: number): Promise<{ bed_extension_percent: number }>;
}
export class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

async function request<T>(path: string, method = 'GET', body?: Parameters): Promise<T> {
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
export const getStatus = () => request<ModelStatus>('model/status');
export const putParameters = (parameters: Parameters) => request<MutationResponse>('parameters', 'PUT', parameters);
export const regenerate = () => request<MutationResponse>('model/regenerate', 'POST');
export const setPosition = (percent: number) => request<{ bed_extension_percent: number }>(
  'model/position', 'PATCH', { bed_extension_percent: percent },
);
