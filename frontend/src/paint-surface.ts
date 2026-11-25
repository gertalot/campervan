import {
  MirroredRepeatWrapping, RepeatWrapping, SRGBColorSpace, TextureLoader, type BufferGeometry, Color, Mesh, type Intersection,
  type MeshBasicMaterial, type MeshStandardMaterial, type Object3D, type Texture,
} from 'three';
import type { ScanPaintPanel } from './scan-panels';
import { floorFinishTint } from './floor-finish';
import { paintTextures, samePaint, type PaintSwatch } from './paint-swatch';

type FaceMaterial = MeshStandardMaterial | MeshBasicMaterial;
type Face = Mesh<BufferGeometry, FaceMaterial>;
interface CadSolid extends Object3D {
  front: Face;
  back?: Face;
  originalColor: Color;
  originalBackColor?: Color;
  alpha: number;
  opacity: number;
  transparent: boolean;
}

// CAD tessellation has no UV coordinates. Project the image onto the three local planes.
// Local coordinates keep the image attached to the solid when a door or lid moves.
function grainAxes(geometry: BufferGeometry) {
  if (!geometry.boundingBox) geometry.computeBoundingBox();
  const { min, max } = geometry.boundingBox!;
  const x = max.x - min.x, y = max.y - min.y, z = max.z - min.z;
  if (z > x && z > y) return 'zxy';
  return y > x ? 'yxz' : 'xyz';
}

function projectedMap(material: FaceMaterial, nativeCompile: FaceMaterial['onBeforeCompile'], axes: string):
  FaceMaterial['onBeforeCompile'] {
  return (shader, renderer) => {
    nativeCompile.call(material, shader, renderer);
    const varyings = 'varying vec3 paintPosition, paintNormal;\n';
    shader.vertexShader = varyings + shader.vertexShader.replace('#include <project_vertex>', `
      #include <project_vertex>
      paintPosition = transformed.${axes};
      paintNormal = normal.${axes};
    `);
    shader.fragmentShader = varyings + 'uniform mat3 mapTransform;\n' +
      shader.fragmentShader.replace('#include <map_fragment>', `
        vec3 weights = pow(abs(normalize(paintNormal)), vec3(6.0));
        weights /= max(dot(weights, vec3(1.0)), 0.0001);
        vec2 uvX = (mapTransform * vec3(paintPosition.yz, 1.0)).xy;
        vec2 uvY = (mapTransform * vec3(paintPosition.xz, 1.0)).xy;
        vec2 uvZ = (mapTransform * vec3(paintPosition.xy, 1.0)).xy;
        diffuseColor *= texture2D(map, uvX) * weights.x
                      + texture2D(map, uvY) * weights.y
                      + texture2D(map, uvZ) * weights.z;
      `);
  };
}

function faceFinish(face: Face, original?: Color) {
  const material = face.material;
  const colour = (original ?? material.color).clone();
  const { map, vertexColors, customProgramCacheKey, onBeforeCompile } = material;
  const nativeTexture = map && paintTextures.find(item => item.id === map.name)?.id;
  const nativeKey = material.customProgramCacheKey();
  const floorTint = floorFinishTint(material);
  return {
    colour, nativeTexture, floor: Boolean(floorTint),
    apply(swatch: PaintSwatch | undefined, texture: Texture | null, textureId?: string) {
      if (swatch) material.color.set(swatch.colour);
      else material.color.copy(colour);
      original?.copy(material.color); // OCP restores this colour after hover or selection.
      material.map = texture ?? (swatch ? null : map);
      material.vertexColors = swatch || texture ? false : vertexColors;
      // Sewn surfaces already have texture coordinates in millimetres.
      const project = texture && !nativeTexture;
      const axes = textureId === 'pine' ? grainAxes(face.geometry) : 'xyz';
      material.onBeforeCompile = project ? projectedMap(material, onBeforeCompile, axes) : onBeforeCompile;
      material.customProgramCacheKey = project ? () => nativeKey + '/paint-map/' + axes : customProgramCacheKey;
      if (floorTint) {
        const { r, g, b } = material.color;
        if (!swatch) floorTint.set(1, 1, 1, 1);
        else floorTint.set(r, g, b, Number(swatch.texture === 'chevron'));
      }
      material.needsUpdate = true;
    },
  };
}

function visibleFace(face: Face) {
  if (!face.material.visible) return false;
  for (let object: Object3D | null = face; object; object = object.parent) {
    if (!object.visible) return false;
  }
  return true;
}

export function createPaintSurface(groups: Record<string, unknown>, groupFor: (path: string) => string | null,
  redraw: () => void, stockTextures: Record<string, string>) {
  const textures = new Map<string, Texture>();
  const loader = new TextureLoader();
  function textureFor(id: string) {
    const definition = paintTextures.find(item => item.id === id);
    if (!definition?.image) return null;
    let texture = textures.get(id);
    if (!texture) {
      texture = loader.load(definition.image, redraw);
      texture.colorSpace = SRGBColorSpace;
      texture.wrapS = RepeatWrapping;
      texture.wrapT = id === 'pine' ? MirroredRepeatWrapping : RepeatWrapping;
      texture.repeat.set(1 / definition.width, 1 / definition.height);
      textures.set(id, texture);
    }
    return texture;
  }

  type Entry = {
    path: string; target: string; object: Object3D; front: Face; alpha: number; faces: ReturnType<typeof faceFinish>[];
    setFinish(swatch?: PaintSwatch): void;
    stockTexture?: string; swatch?: PaintSwatch;
  };
  const cad: Entry[] = [];
  let entries = cad;
  for (const [path, object] of Object.entries(groups)) {
    const solid = object as CadSolid;
    if (!solid.front?.material?.color) continue;
    const target = groupFor(path);
    if (!target) continue;
    const faces = [faceFinish(solid.front, solid.originalColor)];
    if (solid.back) faces.push(faceFinish(solid.back, solid.originalBackColor));
    const stockTexture = stockTextures[path];
    const alpha = solid.alpha;
    const materials = [solid.front, ...(solid.back ? [solid.back] : [])].map(face => ({
      material: face.material, transparent: face.material.transparent,
    }));
    const entry: Entry = { path, target, object: solid, front: solid.front, faces, alpha, stockTexture, setFinish(swatch) {
      if (swatch) solid.userData.campervanPainted = true;
      else delete solid.userData.campervanPainted;
      solid.alpha = swatch?.opacity ?? alpha;
      for (const { material, transparent } of materials) {
        material.opacity = solid.alpha * (solid.transparent ? solid.opacity : 1);
        material.transparent = swatch ? true : transparent;
        material.depthWrite = !solid.transparent && solid.alpha === 1;
      }
    } };
    if (stockTexture) finish(entry, undefined, stockTexture);
    cad.push(entry);
  }

  function finish(entry: Entry, swatch?: PaintSwatch, textureId?: string) {
    entry.swatch = swatch;
    entry.setFinish(swatch);
    const texture = textureId ? textureFor(textureId) : null;
    for (const face of entry.faces) face.apply(swatch, texture, textureId);
  }

  function apply(assignments: Record<string, PaintSwatch>) {
    for (const entry of entries) {
      const swatch = assignments[entry.target];
      if (swatch === entry.swatch || (swatch && entry.swatch && samePaint(swatch, entry.swatch))) continue;
      finish(entry, swatch, swatch?.texture ?? entry.stockTexture);
    }
  }
  function entrySwatch(entry: Entry, floorTop: boolean): PaintSwatch {
    if (entry.swatch) return entry.swatch;
    const front = entry.faces[0];
    if (front.floor && floorTop) return { colour: '#ffffff', opacity: entry.alpha, texture: 'chevron' };
    return { colour: '#' + front.colour.getHexString(), opacity: entry.alpha,
      texture: entry.stockTexture ?? front.nativeTexture ?? 'solid' };
  }
  return {
    apply,
    sample(path: string, hit?: Intersection): PaintSwatch | undefined {
      const entry = entries.find(item => item.path === path);
      if (entry) {
        const normal = hit?.face?.normal.clone().transformDirection(hit.object.matrixWorld);
        return entrySwatch(entry, !normal || normal.z > 0.99);
      }
      // The photographed scan stores its colour at the three corners of each triangle.
      if (!hit || !(hit.object instanceof Mesh)) return;
      const mesh = hit.object;
      const material = Array.isArray(mesh.material) ? mesh.material[hit.face?.materialIndex ?? 0] : mesh.material;
      if (!material?.color) return;
      const colour: Color = material.color.clone();
      const rgb = mesh.geometry.getAttribute('color');
      const triangle = hit.face, weights = hit.barycoord;
      if (material.vertexColors && rgb && triangle && weights) {
        const { a, b, c } = triangle;
        const channel = (get: (i: number) => number) => get(a) * weights.x + get(b) * weights.y + get(c) * weights.z;
        colour.multiply(new Color(channel(i => rgb.getX(i)), channel(i => rgb.getY(i)), channel(i => rgb.getZ(i))));
      }
      return { colour: '#' + colour.getHexString(), texture: 'solid', opacity: material.opacity };
    },
    targetFor: (path: string) => groupFor(path) ?? (entries.some(entry => entry.target === path) ? path : null),
    setScanPaintPanels(panels: ScanPaintPanel[]) {
      for (const entry of entries.slice(cad.length)) if (entry.swatch) finish(entry);
      entries = cad.concat(panels.map(panel => {
        const showBase = panel.face.material.colorWrite;
        return {
          path: panel.target, target: panel.target, object: panel.face, front: panel.face, faces: [faceFinish(panel.face)], alpha: 1,
          setFinish(swatch?: PaintSwatch) {
            panel.face.material.colorWrite = showBase || Boolean(swatch);
            panel.finishOpacity = swatch?.opacity ?? 1;
          },
        };
      }));
    },
    members: (target: string): Object3D[] => entries
      .filter(entry => entry.target === target && visibleFace(entry.front)).map(entry => entry.object),
    used(): PaintSwatch[] {
      const used = new Map<string, PaintSwatch>();
      const add = (item: PaintSwatch) => used.set(`${item.colour.toLowerCase()}/${item.opacity}/${item.texture}`, item);
      for (const entry of entries) {
        if (!visibleFace(entry.front) || !entry.front.material.colorWrite) continue;
        add(entrySwatch(entry, false));
        if (entry.faces[0].floor && !entry.swatch) add(entrySwatch(entry, true));
      }
      return [...used.values()];
    },
    dispose() {
      for (const entry of entries) if (entry.stockTexture || entry.swatch) finish(entry);
      for (const texture of textures.values()) texture.dispose();
    },
  };
}
