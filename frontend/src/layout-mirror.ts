import { DoubleSide, Group, type Material, type Object3D } from 'three';

const roots = ['Long bench', 'Cross bench', 'Cabinet', 'Laptop table', 'Stored gear'];

/** Reflect display parents so native CAD placements and animation tracks stay untouched. */
export function createLayoutMirror() {
  const wrappers = new Map<Object3D, Group>();
  let enabled = false, width = 0, originalCoordinates = 0;

  function apply() {
    const reflect = enabled && originalCoordinates === 0;
    for (const wrapper of wrappers.values()) {
      const x = reflect ? width : 0, scale = reflect ? -1 : 1;
      if (wrapper.position.x === x && wrapper.scale.x === scale) continue;
      wrapper.position.x = x;
      wrapper.scale.x = scale;
      wrapper.updateWorldMatrix(true, true);
    }
  }

  function add(object: Object3D) {
    if (wrappers.has(object) || !object.parent) return;
    object.traverse(child => {
      const line = child as Object3D & { isLineSegments2?: boolean; material: Material | Material[] };
      if (!line.isLineSegments2) return;
      // These camera-facing ribbons keep their screen-space winding under reflection,
      // while Three.js reverses face culling for the negative world determinant.
      for (const material of Array.isArray(line.material) ? line.material : [line.material]) {
        material.side = DoubleSide;
        material.forceSinglePass = true;
        material.needsUpdate = true;
      }
    });
    const wrapper = new Group();
    wrapper.name = 'Layout reflection';
    object.parent.add(wrapper);
    wrapper.add(object);
    wrappers.set(object, wrapper);
    apply();
  }

  return {
    add,
    attach(groups: Record<string, unknown>) {
      for (const name of roots) {
        const object = groups[`/Campervan/${name}`] as Object3D | undefined;
        if (object) add(object);
      }
    },
    clear() {
      for (const [object, wrapper] of wrappers) {
        wrapper.parent?.add(object);
        wrapper.removeFromParent();
      }
      wrappers.clear();
    },
    setEnabled(value: boolean) { enabled = value; apply(); },
    setWidth(value: number) { width = value; apply(); },
    inOriginalCoordinates<T>(operation: () => T): T {
      if (!enabled) return operation();
      originalCoordinates++;
      apply();
      try { return operation(); }
      finally { originalCoordinates--; apply(); }
    },
  };
}
