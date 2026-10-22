import assert from "node:assert/strict";
import test from "node:test";

import { dragToRect, insidePage, noteRect } from "./annotation.ts";

test("drag becomes a rectangle in page points", () => {
  // CSS scale 1.3333 (100 % zoom): 100 CSS px = 75 pt.
  const scale = 4 / 3;
  const rect = dragToRect({ x: 100, y: 200 }, { x: 300, y: 260 }, scale);
  assert.ok(rect);
  assert.deepEqual(rect.map((v) => Math.round(v * 100) / 100), [75, 150, 225, 195]);
});

test("drag direction does not matter", () => {
  const a = dragToRect({ x: 10, y: 10 }, { x: 110, y: 60 }, 1)!;
  const b = dragToRect({ x: 110, y: 60 }, { x: 10, y: 10 }, 1)!;
  assert.deepEqual(a, b);
});

test("a click is not a drag", () => {
  assert.equal(dragToRect({ x: 50, y: 50 }, { x: 50, y: 50 }, 1), null);
  assert.equal(dragToRect({ x: 50, y: 50 }, { x: 51, y: 51 }, 1), null);
});

test("zoom is honoured: the same gesture covers fewer points when zoomed in", () => {
  const at100 = dragToRect({ x: 0, y: 0 }, { x: 100, y: 100 }, 4 / 3)!;
  const at200 = dragToRect({ x: 0, y: 0 }, { x: 100, y: 100 }, 8 / 3)!;
  assert.ok(at200[2] < at100[2], "pada zoom lebih besar, jarak titik lebih kecil");
  assert.ok(Math.abs(at200[2] * 2 - at100[2]) < 0.01);
});

test("gesture is limited to its own page", () => {
  const pageWidth = 595;
  const pageHeight = 842;
  assert.equal(insidePage({ x: 10, y: 10 }, pageWidth, pageHeight), true);
  assert.equal(insidePage({ x: 600, y: 10 }, pageWidth, pageHeight), false);
  assert.equal(insidePage({ x: 10, y: 900 }, pageWidth, pageHeight), false);
  // Small tolerance so a drag that ends 1 px outside is still accepted.
  assert.equal(insidePage({ x: 596, y: 10 }, pageWidth, pageHeight), true);
  assert.equal(insidePage({ x: 700, y: 10 }, pageWidth, pageHeight), false);
});

test("note is anchored at the click position", () => {
  const r = noteRect({ x: 200, y: 300 }, 2, 20);
  assert.deepEqual(r, [100, 130, 120, 150]);
});
