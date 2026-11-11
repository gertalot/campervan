/** Shared scan asset loading for reconstruction inspection and the CAD reference overlay. */
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js';
import { LoadingManager, Mesh, MeshBasicMaterial, MeshStandardMaterial, Points, PointsMaterial,
  type Material, type Object3D, type Texture, type MeshPhongMaterial } from 'three';
import type { ScanResult as Scan, ScanLayer as Layer } from './scan-library-api';

export function disposeObject(root: Object3D) {
  root.traverse(object => {
    if (!(object instanceof Mesh || object instanceof Points)) return;
    object.geometry.dispose();
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      for (const value of Object.values(material)) if ((value as Texture)?.isTexture) (value as Texture).dispose();
      material.dispose();
    }
  });
}

export async function loadObject(url: string, kind: Layer['kind'], mode = ''): Promise<Object3D> {
  if (kind !== 'obj') {
    const geometry = await new PLYLoader().loadAsync(url);
    if (!geometry.getAttribute('position')?.count) { geometry.dispose(); throw new Error('The scan has no geometry.'); }
    if (kind === 'cloud') return new Points(geometry, new PointsMaterial({ size: 2, sizeAttenuation: false,
      color: '#ffffff', vertexColors: !!geometry.getAttribute('color') }));
    if (mode === 'shaded' || mode === 'shaded-full') {
      if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
      return new Mesh(geometry, new MeshStandardMaterial({ color: '#b8b8b8', roughness: 1, metalness: 0 }));
    }
    return new Mesh(geometry, new MeshBasicMaterial({ color: '#ffffff', vertexColors: !!geometry.getAttribute('color') }));
  }
  // Keep the native manager open while MTL, OBJ and their texture images are loaded.
  const manager = new LoadingManager();
  let assetError = '';
  const complete = new Promise<void>(resolve => { manager.onLoad = resolve; });
  manager.onError = failed => { assetError = `Could not load scan asset: ${failed}`; };
  manager.itemStart('scan');
  let root: Object3D | undefined;
  try {
    // OpenMVS writes Tr=1 for opaque surfaces; its convention is the inverse of standard MTL.
    const materialLoader = new MTLLoader(manager);
    materialLoader.setMaterialOptions({ invertTrProperty: mode === 'photo' });
    const materials = await materialLoader.loadAsync(url.replace(/\.obj$/, '.mtl'));
    materials.preload();
    root = await new OBJLoader(manager).setMaterials(materials).loadAsync(url);
    manager.itemEnd('scan');
    await complete;
    if (assetError) throw new Error(assetError);
    root.traverse(object => {
      if (!(object instanceof Mesh)) return;
      const unlit = (original: Material) => {
        const source = original as MeshPhongMaterial;
        const material = new MeshBasicMaterial({ color: source.color, map: source.map,
          opacity: source.opacity, transparent: source.transparent, vertexColors: !source.map && source.vertexColors });
        original.dispose();
        return material;
      };
      object.material = Array.isArray(object.material) ? object.material.map(unlit) : unlit(object.material);
    });
    return root;
  } catch (error) {
    if (root) disposeObject(root);
    throw error;
  }
}

export function layerUrl(scan: Scan, layer: Layer) {
  return scan.id
    ? `/api/v1/scans/runs/${encodeURIComponent(scan.id)}/assets/${layer.asset.split('/').map(encodeURIComponent).join('/')}`
    : `/api/v1/scans/${encodeURIComponent(scan.name)}`;
}
