import { Color, SRGBColorSpace } from 'three';

function toHSV(colour: string, previousHue: number) {
  const { h, s, l } = new Color(colour).getHSL({ h: 0, s: 0, l: 0 }, SRGBColorSpace);
  const value = l + s * Math.min(l, 1 - l);
  return { h: s ? h * 360 : previousHue, s: value ? 200 * (1 - l / value) : 0, v: value * 100 };
}

function fromHSV(hue: number, saturation: number, value: number) {
  const v = value / 100;
  const l = v * (1 - saturation / 200);
  const s = l <= 0 || l >= 1 ? 0 : (v - l) / Math.min(l, 1 - l);
  return '#' + new Color().setHSL(hue / 360, s, l, SRGBColorSpace).getHexString();
}

type Model = 'RGB' | 'HSV';

// Each pair gives the horizontal and vertical axes for the selected rail.
// These orders follow the box picker at https://colordesigner.io/color-picker.
const models = {
  RGB: { names: ['Red', 'Green', 'Blue'], max: [255, 255, 255], axes: [[2, 1], [2, 0], [0, 1]] },
  HSV: { names: ['Hue', 'Saturation', 'Value'], max: [360, 100, 100], axes: [[1, 2], [0, 2], [0, 1]] },
} as const;

function rgbBytes(colour: string) {
  return [1, 3, 5].map(start => parseInt(colour.slice(start, start + 2), 16));
}

function encode(model: Model, values: number[]) {
  if (model === 'HSV') return fromHSV(values[0], values[1], values[2]);
  return '#' + values.map(value => Math.round(value).toString(16).padStart(2, '0')).join('');
}

export function createColourField(onChange: (colour: string) => void) {
  let model: Model = 'RGB';
  const railIndex = { RGB: 0, HSV: 0 };
  let colour = '#ffffff';
  let hsv = toHSV(colour, 0);
  const element = document.createElement('div');
  element.className = 'paint-editor';
  element.innerHTML = `
    <div class="paint-axes" id="cad-paint-axes"></div>
    <div class="paint-box-layout">
      <div class="paint-plane" role="group" aria-labelledby="cad-paint-axes">
        <input class="visually-hidden" type="range"><input class="visually-hidden" type="range">
        <span class="paint-point" aria-hidden="true"></span>
      </div>
      <input class="paint-track paint-rail" type="range" aria-orientation="vertical">
      <div class="paint-tools">
        <fieldset class="paint-channel-choices"><legend>Slider channel</legend></fieldset>
        <div class="paint-colour-preview"></div>
        <label>Hex code<input class="paint-hex" type="text" spellcheck="false" maxlength="7"
          pattern="#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})" required></label>
      </div>
    </div>
    <div class="paint-channels"></div>`;
  const plane = element.querySelector<HTMLElement>('.paint-plane')!;
  const axesLabel = element.querySelector<HTMLElement>('.paint-axes')!;
  const axisInputs = Array.from(plane.querySelectorAll('input'));
  const rail = element.querySelector<HTMLInputElement>('.paint-rail')!;
  const hex = element.querySelector<HTMLInputElement>('.paint-hex')!;
  const choices = element.querySelector('fieldset')!;
  const rows = element.querySelector<HTMLElement>('.paint-channels')!;

  function values() {
    return model === 'RGB' ? rgbBytes(colour) : [hsv.h, hsv.s, hsv.v];
  }

  function apply(next: number[], editing?: HTMLInputElement) {
    colour = encode(model, next);
    hsv = model === 'HSV' ? { h: next[0], s: next[1], v: next[2] } : toHSV(colour, hsv.h);
    render(editing);
    onChange(colour);
  }

  function setChannel(index: number, value: number, editing?: HTMLInputElement) {
    const next = values();
    next[index] = value;
    apply(next, editing);
  }

  const controls = [0, 1, 2].map(index => {
    const choice = document.createElement('label');
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'cad-paint-rail';
    const initial = document.createElement('span');
    choice.append(radio, initial);
    choices.append(choice);
    radio.onchange = () => { railIndex[model] = index; render(); };

    const row = document.createElement('div');
    row.className = 'paint-channel-row';
    const label = document.createElement('label');
    const number = document.createElement('input');
    number.type = 'number';
    number.id = 'cad-paint-channel-' + index;
    number.min = '0';
    number.required = true;
    label.htmlFor = number.id;
    number.oninput = () => {
      if (number.validity.valid) setChannel(index, number.valueAsNumber, number);
    };
    number.onblur = () => render();
    const range = document.createElement('input');
    range.type = 'range';
    range.className = 'paint-track';
    range.oninput = () => setChannel(index, range.valueAsNumber);
    row.append(label, range, number);
    rows.append(row);
    return { radio, initial, label, number, range };
  });

  function pick(event: PointerEvent) {
    const rect = plane.getBoundingClientRect();
    const { axes, max } = models[model];
    const [x, y] = axes[railIndex[model]];
    const next = values();
    const scale = (fraction: number, limit: number) => Math.round(Math.max(0, Math.min(1, fraction)) * limit);
    next[x] = scale((event.clientX - rect.left) / rect.width, max[x]);
    next[y] = scale((rect.bottom - event.clientY) / rect.height, max[y]);
    apply(next);
  }
  plane.onpointerdown = event => {
    if (!event.isPrimary || event.button !== 0) return;
    event.preventDefault();
    plane.setPointerCapture(event.pointerId);
    axisInputs[0].focus({ preventScroll: true });
    pick(event);
  };
  plane.onpointermove = event => { if (plane.hasPointerCapture(event.pointerId)) pick(event); };
  axisInputs.forEach((input, i) => {
    input.oninput = () => setChannel(models[model].axes[railIndex[model]][i], input.valueAsNumber);
  });
  rail.oninput = () => setChannel(railIndex[model], rail.valueAsNumber);
  hex.oninput = () => {
    if (!hex.validity.valid) return;
    const digits = hex.value.replace('#', '').toLowerCase();
    colour = '#' + (digits.length === 3 ? [...digits].map(d => d + d).join('') : digits);
    hsv = toHSV(colour, hsv.h);
    render(hex);
    onChange(colour);
  };
  hex.onblur = () => render();

  function render(editing?: HTMLInputElement) {
    const { names, max, axes } = models[model];
    const fixed = railIndex[model];
    const [x, y] = axes[fixed];
    const current = values();
    element.dataset.rail = names[fixed];
    element.style.setProperty('--shade', colour);
    plane.style.setProperty('--shade-x', 100 * current[x] / max[x] + '%');
    plane.style.setProperty('--shade-y', 100 - 100 * current[y] / max[y] + '%');
    if (model === 'RGB') {
      const primaries = ['red', 'lime', 'blue'];
      plane.style.setProperty('--x-colour', primaries[x]);
      plane.style.setProperty('--y-colour', primaries[y]);
      plane.style.setProperty('--base', encode(model, current.map((v, i) => i === fixed ? v : 0)));
    } else {
      plane.style.setProperty('--hue', String(hsv.h));
      plane.style.setProperty('--wash', String(1 - hsv.s / 100));
      plane.style.setProperty('--darken', String(1 - hsv.v / 100));
    }
    axesLabel.textContent = names[x] + ' →  ·  ' + names[y] + ' ↑';
    [x, y].forEach((index, i) => {
      const axis = axisInputs[i];
      axis.max = String(max[index]);
      axis.value = String(Math.round(current[index]));
      axis.setAttribute('aria-label', names[index]);
      plane.dataset[i === 0 ? 'x' : 'y'] = names[index] + ' · ' + axis.value;
    });
    controls.forEach(({ radio, initial, label, number, range }, index) => {
      const name = names[index];
      const unit = model === 'RGB' ? '' : index === 0 ? '°' : '%';
      radio.checked = index === fixed;
      radio.setAttribute('aria-label', name);
      initial.textContent = name[0];
      initial.title = name;
      label.textContent = name + (unit ? ' (' + unit + ')' : '');
      range.setAttribute('aria-label', name);
      range.max = number.max = String(max[index]);
      range.value = String(Math.round(current[index]));
      range.setAttribute('aria-valuetext', range.value + unit);
      if (number !== editing) number.value = range.value;

      // HSV hue changes direction at each primary and secondary colour. Other channels are linear in sRGB.
      const segments = model === 'HSV' && index === 0 ? 6 : 1;
      const stops = Array.from({ length: segments + 1 }, (_, step) => {
        const sample = [...current];
        sample[index] = max[index] * step / segments;
        return encode(model, sample);
      }).join(', ');
      range.style.setProperty('--track', 'linear-gradient(to right in srgb, ' + stops + ')');
      if (index === fixed) {
        rail.style.setProperty('--track', 'linear-gradient(to top in srgb, ' + stops + ')');
        rail.max = range.max;
        rail.value = range.value;
        rail.setAttribute('aria-label', name + ' vertical slider');
        rail.setAttribute('aria-valuetext', range.value + unit);
      }
    });
    if (hex !== editing) hex.value = colour.toUpperCase();
  }

  return {
    element,
    show(nextModel: Model, nextColour: string) {
      model = nextModel;
      if (colour !== nextColour.toLowerCase()) {
        colour = nextColour.toLowerCase();
        hsv = toHSV(colour, hsv.h);
      }
      render();
    },
  };
}
