/// <reference types="vite/client" />
/** Runtime inputs for an exported snapshot; the local app still uses its API. */
export const isStaticSite = import.meta.env.MODE === 'static';

export function assetUrl(path: string): string {
  return new URL(path, new URL(import.meta.env.BASE_URL, document.baseURI)).href;
}

let snapshot: Promise<Record<string, unknown>> | undefined;
export async function readSnapshotPart<T>(key: string): Promise<T> {
  snapshot ??= fetch(assetUrl('snapshot.json')).then(async response => {
    if (!response.ok) throw new Error(`Could not load the exported project (${response.status}).`);
    return response.json() as Promise<Record<string, unknown>>;
  });
  const data = await snapshot;
  if (!(key in data)) throw new Error(`The exported project is missing ${key}. Run make site again.`);
  return structuredClone(data[key]) as T;
}
