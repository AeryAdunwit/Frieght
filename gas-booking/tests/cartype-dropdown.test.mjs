import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const indexHtml = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const scriptHtml = readFileSync(new URL('../script.html', import.meta.url), 'utf8');

assert.match(
  indexHtml,
  /<select id="fCartype" required data-field="cartype">/,
  'cartype field should be a required select dropdown'
);

assert.doesNotMatch(
  indexHtml,
  /id="fCartype"[^>]+list="cartypeList"/,
  'cartype field should not use a datalist text input'
);

['รอรอบส่ง', 'เฮี๊ยบ', 'เหมารถ', 'ไปขนส่ง'].forEach((cartype) => {
  assert.match(
    scriptHtml,
    new RegExp(`DEFAULT_CARTYPES = \\[[^\\]]*${cartype}[^\\]]*\\]`),
    `cartype dropdown should include ${cartype}`
  );
});

['parcel', 'pooling', 'hiab', 'triprate'].forEach((cartype) => {
  assert.match(
    scriptHtml,
    new RegExp(`REMOVED_CARTYPES = new Set\\(\\[[^\\]]*${cartype}[^\\]]*\\]\\)`),
    `cartype dropdown should remove ${cartype}`
  );
});

console.log('cartype dropdown ok');
