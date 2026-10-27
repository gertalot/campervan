/** One renderer and one Three.js runtime, shared with the app and its GLTF loader. */
import { assetUrl } from './site-runtime';
const rendererUrl = assetUrl('viewer-assets/js/shared-renderer.js');
const renderer = await import(/* @vite-ignore */ rendererUrl);
const sharedThree = renderer.sharedThree as typeof import('three');
export const { Viewer, Display, Timer } = renderer;
// Vite resolves bare 'three' imports here, including imports inside the loader
// and its BufferGeometryUtils / SkeletonUtils dependencies. npm supplies the
// matching addon sources and types; its second Three.js runtime is never loaded.
export const {
  REVISION, AnimationClip, AnimationMixer, Bone, Box3, BoxGeometry, BufferAttribute, BufferGeometry,
  ClampToEdgeWrapping, Color, ColorManagement, DirectionalLight, DoubleSide, FileLoader, Float32BufferAttribute,
  EdgesGeometry, FrontSide, Group, ImageBitmapLoader, InstancedBufferAttribute, InstancedMesh, InterleavedBuffer,
  InterleavedBufferAttribute, Interpolant, InterpolateDiscrete, InterpolateLinear, IntType, Line, LineBasicMaterial,
  LineLoop, LineSegments, LinearFilter, LinearMipmapLinearFilter, LinearMipmapNearestFilter, LinearSRGBColorSpace,
  Loader, LoaderUtils, Material, MathUtils, Matrix4, Mesh, MeshBasicMaterial, MeshPhysicalMaterial, MeshStandardMaterial,
  MirroredRepeatWrapping, NearestFilter, NearestMipmapLinearFilter, NearestMipmapNearestFilter, NumberKeyframeTrack,
  Object3D, OrthographicCamera, PerspectiveCamera, PointLight, Points, PointsMaterial, PropertyBinding, Quaternion,
  QuaternionKeyframeTrack, RepeatWrapping, Scene, Skeleton, SkeletonHelper, SkinnedMesh, Sphere, SpotLight,
  Raycaster, SRGBColorSpace, Texture, TextureLoader, TriangleFanDrawMode, TriangleStripDrawMode, TrianglesDrawMode,
  Uint32BufferAttribute, Vector2, Vector3, VectorKeyframeTrack,
} = sharedThree;
