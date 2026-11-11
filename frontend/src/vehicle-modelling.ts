/** Vehicle components fitted so far in the step-by-step scan modelling work. */
const modelledParts: { path: string; label: string }[] = [
  { path: '/Campervan/Vehicle references/Body floor/Rear floor/Rear edge', label: 'Rear-door floor edge' },
];
const activeParts = [
  '/Campervan/Vehicle references/Body floor/Rear floor/Rear edge',
  '/Campervan/Vehicle references/Body floor/Rear floor/Left rear pillar base',
  '/Campervan/Vehicle references/Body floor/Rear floor/Right rear pillar base',
];

export function isVehiclePartActive(path: string): boolean {
  return activeParts.some(root => path === root || path.startsWith(`${root}/`));
}

export function vehicleOutlineOpacity(path: string): number {
  return isVehiclePartActive(path) ? 1 : 0.12;
}

export function isVehiclePartModelled(path: string): boolean {
  return modelledParts.some(part => path === part.path || path.startsWith(`${part.path}/`));
}

export const vehicleModellingLegend = 'Magenta — rear edge, separate brace leading edge and return, rear pillar, diagonal pillar and straight sidewall. '
  + 'Cyan wireframe — unfinished vehicle parts. '
  + 'The outline currently stops at the side edges before the wheel arches.';
