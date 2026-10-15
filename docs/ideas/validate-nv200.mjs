import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(root, 'nv200-interior.fs'), 'utf8');
const checks = fs.readFileSync(path.join(root, 'nv200-drawer-checks.fs'), 'utf8');
// UI defaults and runtime defaults are distinct contracts. Test both.
assert.match(source, /"longBenchWidth"\s*:\s*600\s*\*\s*millimeter/);
assert.match(source, /isLength\(definition\.longBenchWidth,\s*\{\s*\(millimeter\)\s*:\s*\[100,\s*600,\s*10000\]/);
assert.doesNotMatch(source, /isLength\(definition\.(?:benchWidth|seatWidth),/);
assert.equal((source.match(/export const \w+ = defineFeature/g) || []).length, 1);

const mutation = process.argv[2];
assert.ok(!mutation || ['old-header', 'raised-post'].includes(mutation), 'Unknown mutation');
let adapted = source
  .replace(/^FeatureScript.*\nimport.*\n/, '')
  .replace(/export enum NV200Layout[\s\S]*?\n\}/, '')
  .replaceAll('NV200Layout.DAY', '"DAY"')
  .replaceAll('NV200Layout.NIGHT', '"NIGHT"')
  .replaceAll('is NV200Layout', 'is string')
  .replace(/function (\w+)([\s\S]*?)\n\}/g, (match, name, body) => 'const ' + name + ' = function' + body + '\n};')
  .replace('export const nv200Interior', 'const nv200Interior');

if (mutation === 'old-header') {
  const before = 'vector(p.frameX+d.frameThickness,p.frameStart,height-d.memberWidth),\n' +
    '        vector(width-d.frameThickness,p.frameStart+d.frameThickness,height)';
  assert.ok(adapted.includes(before), 'Header mutation target changed');
  adapted = adapted.replace(before,
    'vector(p.frameX+d.frameThickness,p.frameStart+7*millimeter,height-d.memberWidth),\n' +
    '        vector(width-d.frameThickness,p.frameStart+d.frameThickness+7*millimeter,height)');
}
if (mutation === 'raised-post') {
  const before = 'vector(p.frameX,zero,d.drawerFrameHeight),\n' +
    '        vector(p.frameX+d.frameThickness,postEnd,bedFrameTop)';
  assert.ok(adapted.includes(before), 'Post mutation target changed');
  adapted = adapted.replace(before,
    'vector(p.frameX,7*millimeter,d.drawerFrameHeight),\n' +
    '        vector(p.frameX+d.frameThickness,postEnd+7*millimeter,bedFrameTop)');
}
const probe = '\nvar d=DEFAULTS; d.cabinetHeight=400*millimeter; ' +
  'nv200Interior(context,makeId("mutation"),d); ' +
  'return "Mutation probe: require expected Rear alignment failed notice in evaluator response";\n}';
const output = 'function(context,queries) {\n' + adapted + '\n' + (mutation ? probe : checks);
const filename = mutation ? 'nv200-drawer-mutation-' + mutation + '.fs' : 'nv200-drawer-validation.fs';
fs.writeFileSync(path.join(root, filename), output);
console.log('PASS explicit 600 mm UI/runtime defaults; generated ' + filename + ' from current production source.');
