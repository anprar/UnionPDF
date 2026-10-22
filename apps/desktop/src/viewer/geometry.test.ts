import assert from "node:assert/strict";
import test from "node:test";

import { measureRun, spanTransform, transformCss } from "./geometry.ts";

test("a run is stretched to the width the engine measured", () => {
  // Target: 100 px wide; the UI font renders the same text only 80 px wide.
  const t = spanTransform(
    { left: 10, top: 20, width: 100, height: 12 },
    { measuredWidth: 80, ascent: 10, descent: 2, lineHeight: 12 },
  );
  assert.ok(Math.abs(t.scaleX - 1.25) < 1e-6, `scaleX=${t.scaleX}`);
  assert.equal(t.fontSize, 12);
});

test("the correction is relative, so it survives zooming", () => {
  const small = spanTransform(
    { left: 0, top: 0, width: 50, height: 6 },
    { measuredWidth: 40, ascent: 5, descent: 1, lineHeight: 6 },
  );
  const big = spanTransform(
    { left: 0, top: 0, width: 150, height: 18 },
    { measuredWidth: 120, ascent: 15, descent: 3, lineHeight: 18 },
  );
  assert.ok(Math.abs(small.scaleX - big.scaleX) < 1e-9, "skala harus sama pada semua zoom");
  assert.ok(Math.abs(small.dy - big.dy) < 1e-9, "offset vertikal harus proporsional");
});

test("the vertical offset centres the ink box on the target box", () => {
  // Line box 12 px, ink box 10 px high -> 1 px of leading above and below.
  const t = spanTransform(
    { left: 0, top: 0, width: 100, height: 12 },
    { measuredWidth: 100, ascent: 10, descent: 0, lineHeight: 12 },
  );
  assert.ok(Math.abs(t.dy - -1) < 1e-6, `dy=${t.dy}`);
});

test("an empty measurement does not distort the run", () => {
  const t = spanTransform(
    { left: 0, top: 0, width: 100, height: 12 },
    { measuredWidth: 0, ascent: 0, descent: 0, lineHeight: 12 },
  );
  assert.equal(t.scaleX, 1);
  assert.equal(t.dy, 0);
});

test("transform css only contains the corrections that are needed", () => {
  const none = transformCss({ scaleX: 1, dy: 0, fontSize: 12 });
  assert.equal(none, "none");
  const scaled = transformCss({ scaleX: 1.25, dy: -1, fontSize: 12 });
  assert.match(scaled, /translateY\(-1\.00px\)/);
  assert.match(scaled, /scaleX\(1\.2500\)/);
});

test("measureRun falls back to sane metrics without a canvas", () => {
  const m = measureRun(null, "abc", 12, "Segoe UI");
  assert.equal(m.measuredWidth, 0);
  assert.equal(m.lineHeight, 12);
});
