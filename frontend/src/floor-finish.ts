import { Box3, Matrix4, RepeatWrapping, SRGBColorSpace, Texture, Vector2, Vector4, type Mesh, type Material } from 'three';
import { floorPattern, floorPieces, floorRoot, floorPatternTransform, type FloorPatternSettings } from './floor-pattern';

function makePaintTile() {
  const { width, height, stripe, cream, brown, bandPath } = floorPattern;
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const brush = canvas.getContext('2d')!;
  brush.fillStyle = cream;
  brush.fillRect(0, 0, width, height);
  brush.scale(stripe, stripe);
  brush.fillStyle = brown;
  brush.fill(new Path2D(bandPath));
  const texture = new Texture(canvas);
  texture.wrapS = texture.wrapT = RepeatWrapping;
  texture.colorSpace = SRGBColorSpace;
  texture.flipY = false; // Artwork Y increases from the rear towards the cab.
  texture.needsUpdate = true;
  return texture;
}

let paint: Texture | undefined;
// RGB tints the artwork. W enables it on the upper face.
const tints = new WeakMap<Material, Vector4>();
export const floorFinishTint = (material: Material) => tints.get(material);
export function applyFloorFinish(groups: Record<string, unknown>) {
  const front = (piece: string) =>
    (groups[`/Campervan/${floorRoot}/${piece}`] as { front?: Mesh } | undefined)?.front;
  const bench = front(floorPieces.bench), aisle = front(floorPieces.aisle);
  if (!bench || !aisle) return;
  // Bounds of the two sheets establish a single datum, including the door wings.
  const bounds = new Box3().setFromObject(bench, true).expandByObject(aisle, true);
  const origin = new Vector2(bounds.min.x, bounds.min.y);
  const repeat = new Vector2(floorPattern.width / floorPattern.stripe, floorPattern.height / floorPattern.stripe);
  const lookup = new Matrix4();
  paint ??= makePaintTile();
  for (const mesh of [bench, aisle, front(floorPieces.lid)]) {
    if (!mesh) continue;
    const material = mesh.material as Material;
    const tint = new Vector4(1, 1, 1, 1);
    tints.set(material, tint);
    const previous = material.onBeforeCompile.bind(material);
    const key = material.customProgramCacheKey();
    material.customProgramCacheKey = () => key + '/floor-paint';
    material.onBeforeCompile = (shader, renderer) => {
      previous(shader, renderer); // Keep OCP's face highlight and clipping.
      shader.uniforms.floorPaint = { value: paint };
      shader.uniforms.floorTint = { value: tint };
      shader.uniforms.floorOrigin = { value: origin };
      shader.uniforms.floorRepeat = { value: repeat };
      shader.uniforms.floorLookup = { value: lookup };
      shader.vertexShader = 'varying vec3 floorCoord;\nuniform vec2 floorOrigin, floorRepeat;\nuniform mat4 floorLookup;\n' +
        shader.vertexShader.replace('#include <project_vertex>', `
          #include <project_vertex>
          vec2 mm = (modelMatrix * vec4(transformed, 1.0)).xy - floorOrigin;
          floorCoord.xy = (floorLookup * vec4(mm, 0.0, 1.0)).xy / floorRepeat;
          floorCoord.z = normalize(mat3(modelMatrix) * normal).z;
        `);
      shader.fragmentShader = 'varying vec3 floorCoord;\nuniform sampler2D floorPaint;\nuniform vec4 floorTint;\n' +
        shader.fragmentShader.replace('#include <color_fragment>', `
          #include <color_fragment>
          if (floorTint.w > 0.0 && floorCoord.z > 0.99)
            diffuseColor.rgb = floorTint.rgb * texture2D(floorPaint, floorCoord.xy).rgb;
        `);
    };
    material.needsUpdate = true;
  }
  return (settings: FloorPatternSettings) => {
    const transform = floorPatternTransform(settings, bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y);
    lookup.fromArray(transform.inverse().toFloat32Array());
  };
}
