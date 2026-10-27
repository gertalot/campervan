/** Horizontal, two-pivot steering for the mounted Lagun table. */
import { Box3, Vector3, type Camera, type Mesh, type Object3D } from 'three';

type Pose = Record<string, number>;
type XY = { x: number; y: number };
const ARM = 'table_arm_swivel_deg', TOP = 'table_top_rotation_deg';
const RAD = Math.PI / 180;
const near = (angle: number, reference: number) => reference
  + Math.atan2(Math.sin(angle - reference), Math.cos(angle - reference));
const clamp = (value: number, low: number, high: number) => Math.max(low, Math.min(high, value));

/** Bounds in the tabletop joint's coordinates, including the current fold and offset.
 * Only bamboo contributes; hinge details and selection/drag overlays do not move its centre.
 */
function tabletopBounds(wood: Object3D, top: Object3D): Box3 {
  const bounds = new Box3();
  const inverse = top.matrixWorld.clone().invert();
  const leaves: Mesh[] = [], fallback: Mesh[] = [];
  wood.traverse(object => {
    const mesh = object as Mesh;
    if (!mesh.isMesh || !mesh.geometry || mesh.userData.dragOverlay || mesh.renderOrder >= 10000) return;
    fallback.push(mesh);
    let bamboo = false;
    for (let ancestor: Object3D | null = object; ancestor && ancestor !== wood; ancestor = ancestor.parent) {
      if (ancestor.name.toLowerCase().includes('bamboo leaf')) bamboo = true;
    }
    if (bamboo) leaves.push(mesh);
  });
  // Some renderer versions omit labels from Object3D.name. Use their complete local wood envelope.
  for (const mesh of leaves.length ? leaves : fallback) {
    if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
    const box = mesh.geometry.boundingBox;
    if (!box || box.isEmpty()) continue;
    const matrix = inverse.clone().multiply(mesh.matrixWorld);
    for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) {
      for (const z of [box.min.z, box.max.z]) bounds.expandByPoint(new Vector3(x, y, z).applyMatrix4(matrix));
    }
  }
  if (bounds.isEmpty()) bounds.expandByPoint(top.worldToLocal(wood.getWorldPosition(new Vector3())));
  return bounds;
}

export function createTableDrag(arm: Object3D, top: Object3D, wood: Object3D, point: Vector3,
  pose: Pose, camera: Camera, rect: DOMRect): { solve(clientX: number, clientY: number, current: Pose): Pose | null } {
  arm.updateWorldMatrix(true, true);
  const pivot = arm.getWorldPosition(new Vector3()), tip = top.getWorldPosition(new Vector3());
  // Derive the horizontal plane from the actual arm parent, rather than the camera's up vector.
  const parentMatrix = arm.parent?.matrixWorld ?? arm.matrixWorld;
  const xAxis = new Vector3(1, 0, 0).transformDirection(parentMatrix);
  const normal = new Vector3(0, 0, 1).transformDirection(parentMatrix);
  const yAxis = normal.clone().cross(xAxis).normalize();
  const xy = (v: Vector3): XY => ({ x: v.dot(xAxis), y: v.dot(yAxis) });
  const link = xy(tip.clone().sub(pivot));
  const length = Math.hypot(link.x, link.y), startArm = Math.atan2(link.y, link.x);
  const heading = xy(new Vector3(1, 0, 0).transformDirection(top.matrixWorld));
  const startHeading = Math.atan2(heading.y, heading.x);
  const grab = xy(point.clone().sub(tip)), radius = Math.hypot(grab.x, grab.y);
  const grabPhase = Math.atan2(grab.y, grab.x) - startHeading;
  const initial = { arm: pose[ARM] ?? 0, top: pose[TOP] ?? 0 };
  const bounds = tabletopBounds(wood, top), centre = bounds.getCenter(new Vector3());
  const size = bounds.getSize(new Vector3()), localPoint = top.worldToLocal(point.clone());
  const edgeDistance = Math.max(Math.abs(localPoint.x - centre.x) / Math.max(1, size.x / 2),
    Math.abs(localPoint.y - centre.y) / Math.max(1, size.y / 2));
  // Central 15%: keep world heading. At 90% of either half-extent: unrestricted two-joint IK.
  const amount = clamp((edgeDistance - 0.15) / 0.75, 0, 1);
  const freedom = amount * amount * (3 - 2 * amount);
  const projectedPoint = point.clone().project(camera);
  const anchorX = rect.left + (projectedPoint.x + 1) * rect.width / 2;
  const anchorY = rect.top + (1 - projectedPoint.y) * rect.height / 2;

  function planePoint(clientX: number, clientY: number): Vector3 | null {
    const x = (clientX - rect.left) / rect.width * 2 - 1;
    const y = 1 - (clientY - rect.top) / rect.height * 2;
    const from = new Vector3(x, y, -1).unproject(camera);
    const direction = new Vector3(x, y, 1).unproject(camera).sub(from).normalize();
    const denominator = direction.dot(normal);
    // Near the horizon, a pixel can imply a huge depth change; preserve the current pose instead.
    if (Math.abs(denominator) < 0.08) return null;
    const distance = point.clone().sub(from).dot(normal) / denominator;
    if (!Number.isFinite(distance) || distance < 0) return null;
    return from.addScaledVector(direction, distance);
  }
  const anchor = planePoint(anchorX, anchorY);

  function solve(clientX: number, clientY: number, current: Pose): Pose | null {
    const pointer = planePoint(clientX, clientY);
    if (!pointer || !anchor || length < 1e-6 || !rect.width || !rect.height) return null;
    // Keeping the initial pointer/wood offset avoids snapping the grabbed surface to a joint centre.
    const target = xy(pointer.sub(anchor).add(point).sub(pivot));
    const currentArm = startArm - ((current[ARM] ?? initial.arm) - initial.arm) * RAD;
    const currentHeading = startHeading - (((current[ARM] ?? initial.arm) - initial.arm)
      + ((current[TOP] ?? initial.top) - initial.top)) * RAD;
    const distance = Math.hypot(target.x, target.y);
    const minimum = Math.abs(length - radius), maximum = length + radius;
    const reachable = clamp(distance, minimum, maximum);
    if (distance > 1e-8) { target.x *= reachable / distance; target.y *= reachable / distance; }
    else {
      const direction = currentArm;
      target.x = Math.cos(direction) * reachable; target.y = Math.sin(direction) * reachable;
    }
    let a = currentArm, h = currentHeading;
    const preferredHeading = near(startHeading, currentHeading);

    if (freedom === 0 || radius < 1e-6) {
      h = preferredHeading;
      const gx = radius * Math.cos(h + grabPhase), gy = radius * Math.sin(h + grabPhase);
      const dx = target.x - gx, dy = target.y - gy;
      if (Math.hypot(dx, dy) > 1e-8) a = near(Math.atan2(dy, dx), currentArm);
    } else if (freedom === 1) {
      // Two exact solutions. Choose the nearest arm/joint pair, retaining turns across ±180°.
      if (reachable < 1e-6) {
        return {
          [ARM]: current[ARM] ?? initial.arm,
          [TOP]: initial.top - ((near(currentArm + Math.PI - grabPhase, currentHeading) - startHeading)
            - (currentArm - startArm)) / RAD,
        };
      }
      const relative = Math.acos(clamp((reachable * reachable - length * length - radius * radius)
        / (2 * length * radius), -1, 1));
      let best = Infinity;
      for (const bend of [relative, -relative]) {
        const candidateArm = near(Math.atan2(target.y, target.x)
          - Math.atan2(radius * Math.sin(bend), length + radius * Math.cos(bend)), currentArm);
        const candidateHeading = near(candidateArm + bend - grabPhase, currentHeading);
        const jointDelta = candidateHeading - candidateArm - (currentHeading - currentArm);
        const cost = (candidateArm - currentArm) ** 2 + jointDelta ** 2;
        if (cost < best) { best = cost; a = candidateArm; h = candidateHeading; }
      }
    } else {
      // Damped Gauss–Newton from the accepted pose keeps the same local branch. Heading regularisation
      // makes a central grab slide around the arm circle instead of unexpectedly turning the top.
      const penalty = 0.12 * (length * length + radius * radius) * ((1 - freedom) / freedom) ** 2;
      const objective = (armAngle: number, topHeading: number) => {
        const dx = length * Math.cos(armAngle) + radius * Math.cos(topHeading + grabPhase) - target.x;
        const dy = length * Math.sin(armAngle) + radius * Math.sin(topHeading + grabPhase) - target.y;
        return dx * dx + dy * dy + penalty * (topHeading - preferredHeading) ** 2;
      };
      // At a straight/folded singularity the radial gradient vanishes. A tiny coordinated bend can
      // reveal a descending direction without selecting a distant IK branch or making a large flip.
      if (Math.abs(Math.sin(h + grabPhase - a)) < 1e-5) {
        const da = 0.025 * Math.min(1, radius / length), dh = -da * length / radius;
        let best = objective(a, h), nextA = a, nextH = h;
        for (const sign of [-1, 1]) {
          const cost = objective(a + sign * da, h + sign * dh);
          if (cost < best) { best = cost; nextA = a + sign * da; nextH = h + sign * dh; }
        }
        a = nextA; h = nextH;
      }
      for (let iteration = 0; iteration < 18; iteration++) {
        const lx = length * Math.cos(a), ly = length * Math.sin(a);
        const gx = radius * Math.cos(h + grabPhase), gy = radius * Math.sin(h + grabPhase);
        const dx = lx + gx - target.x, dy = ly + gy - target.y;
        const aa = length * length + 1e-4, ah = lx * gx + ly * gy;
        const hh = radius * radius + penalty + 1e-4, determinant = aa * hh - ah * ah;
        if (determinant <= 1e-12) break;
        const ga = -ly * dx + lx * dy;
        const gh = -gy * dx + gx * dy + penalty * (h - preferredHeading);
        let da = -(hh * ga - ah * gh) / determinant;
        let dh = -(aa * gh - ah * ga) / determinant;
        const scale = Math.max(1, Math.abs(da) / 0.35, Math.abs(dh) / 0.35);
        da /= scale; dh /= scale;
        const before = objective(a, h);
        let fraction = 1;
        while (fraction > 1 / 64 && objective(a + da * fraction, h + dh * fraction) > before) fraction /= 2;
        if (fraction <= 1 / 64) break;
        a += da * fraction; h += dh * fraction;
        if (Math.abs(da * fraction) + Math.abs(dh * fraction) < 1e-6) break;
      }
    }
    return {
      [ARM]: initial.arm - (a - startArm) / RAD,
      [TOP]: initial.top - ((h - startHeading) - (a - startArm)) / RAD,
    };
  }
  return { solve };
}
