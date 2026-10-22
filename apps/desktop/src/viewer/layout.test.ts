import assert from "node:assert/strict";
import test from "node:test";

import {
  type PageSize,
  anchorScrollTop,
  captureAnchor,
  computeLayout,
  dominantPage,
  fitPageScale,
  fitWidthScale,
  pageAt,
  visibleRange,
} from "./layout.ts";

const A4: PageSize = { width: 595, height: 842 };
const LETTER: PageSize = { width: 612, height: 792 };
const A5: PageSize = { width: 420, height: 595 };

test("layout stacks pages with a constant gap and keeps the exact size", () => {
  const pages = [A4, LETTER, A5];
  const l = computeLayout(pages, 1, 16);
  assert.equal(l.boxes.length, 3);
  assert.equal(l.boxes[0].top, 0);
  assert.equal(l.boxes[1].top, 842 + 16);
  assert.equal(l.boxes[2].top, 842 + 16 + 792 + 16);
  assert.equal(l.totalHeight, 842 + 16 + 792 + 16 + 595);
  assert.equal(l.contentWidth, 612);
  assert.equal(l.boxes[0].cssWidth, 595);
});

test("mixed page sizes keep their own height", () => {
  const l = computeLayout([A4, A5, LETTER], 0.5);
  assert.equal(l.boxes[0].cssHeight, 421);
  assert.equal(l.boxes[1].cssHeight, 298);
  assert.equal(l.boxes[2].cssHeight, 396);
  assert.ok(l.boxes[1].top > l.boxes[0].top);
  assert.ok(l.boxes[2].top > l.boxes[1].top);
});

test("pageAt maps a document offset to a page", () => {
  const l = computeLayout([A4, A4, A4], 1, 10);
  assert.equal(pageAt(l.boxes, 0), 0);
  assert.equal(pageAt(l.boxes, 841), 0);
  assert.equal(pageAt(l.boxes, 852), 1);
  assert.equal(pageAt(l.boxes, 2000), 2);
  assert.equal(pageAt(l.boxes, -5), 0);
});

test("dominant page uses the viewport centre and does not flicker in the gap", () => {
  const l = computeLayout([A4, A4, A4], 1, 10);
  // Viewport of 600 px showing the first page: centre is inside page 0.
  assert.equal(dominantPage(l.boxes, 0, 600), 0);
  // Centre inside the gap between page 0 and 1 -> the page above stays active.
  assert.equal(dominantPage(l.boxes, 545, 600), 0);
  // Centre clearly inside page 1 -> page 1.
  assert.equal(dominantPage(l.boxes, 842 + 100, 600), 1);
});

test("visible range includes overscan and is clamped to the document", () => {
  const pages = Array.from({ length: 20 }, () => A4);
  const l = computeLayout(pages, 0.2, 8);
  const [first, last] = visibleRange(l.boxes, 0, 400, 1);
  assert.equal(first, 0);
  assert.ok(last >= 1);
  const [f2, l2] = visibleRange(l.boxes, l.totalHeight, 400, 1);
  assert.equal(l2, 19);
  assert.ok(f2 <= 19);
});

test("anchor capture and restore keep the reading position across a zoom", () => {
  const l1 = computeLayout([A4, A4, A4], 1, 10);
  const anchor = captureAnchor(l1.boxes, 900); // 48 px into page 1
  assert.ok(anchor);
  assert.equal(anchor.page, 1);
  assert.ok(Math.abs(anchor.ratio - 48 / 842) < 0.01);

  const l2 = computeLayout([A4, A4, A4], 2, 10);
  const top = anchorScrollTop(l2.boxes, anchor);
  const box = l2.boxes[1];
  const restored = captureAnchor(l2.boxes, top);
  assert.ok(restored);
  assert.equal(restored.page, 1);
  assert.ok(Math.abs(restored.ratio - anchor.ratio) < 0.02, `${restored.ratio} vs ${anchor.ratio}`);
});

test("fit width uses the widest page, fit page uses the largest page", () => {
  const pages = [A4, LETTER, A5];
  assert.ok(Math.abs(fitWidthScale(pages, 1224) - 1224 / 612) < 1e-6);
  const s = fitPageScale(pages, 1000, 1400);
  assert.ok(Math.abs(s - Math.min(1000 / 612, 1400 / 842)) < 1e-6);
});

test("empty document does not produce a broken layout", () => {
  const l = computeLayout([], 1);
  assert.equal(l.totalHeight, 0);
  assert.equal(pageAt(l.boxes, 10), -1);
  assert.equal(dominantPage(l.boxes, 0, 600), -1);
  assert.equal(captureAnchor(l.boxes, 0), null);
});
