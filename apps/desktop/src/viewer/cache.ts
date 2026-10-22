/**
 * Cache for rendered page bitmaps.
 *
 * Key parts: document identity, document revision, page number, render scale and the
 * page rotation (a rotated page renders differently). The cache is bounded and evicts
 * the least recently used entries; evicted bitmaps are closed so the GPU memory is
 * released.
 */

export interface BitmapCacheEntry {
  bitmap: ImageBitmap;
  width: number;
  height: number;
}

export class BitmapCache {
  private map = new Map<string, BitmapCacheEntry>();
  private inflight = new Map<string, Promise<BitmapCacheEntry | null>>();

  constructor(private readonly maxEntries = 40) {}

  static key(docId: number, revision: number, pageIndex: number, scale: number, rotation: number): string {
    // Scale is rounded to 0.01 to avoid a cache miss for floating point noise.
    return `${docId}:${revision}:${pageIndex}:${scale.toFixed(2)}:${rotation}`;
  }

  get(key: string): BitmapCacheEntry | undefined {
    const e = this.map.get(key);
    if (e) {
      this.map.delete(key);
      this.map.set(key, e);
    }
    return e;
  }

  set(key: string, entry: BitmapCacheEntry): void {
    const old = this.map.get(key);
    if (old && old.bitmap !== entry.bitmap) old.bitmap.close();
    this.map.delete(key);
    this.map.set(key, entry);
    while (this.map.size > this.maxEntries) {
      const oldest = this.map.keys().next();
      if (oldest.done) break;
      const e = this.map.get(oldest.value);
      this.map.delete(oldest.value);
      if (e) e.bitmap.close();
    }
  }

  /** Registers an in-flight render so the same page is not requested twice. */
  track(key: string, promise: Promise<BitmapCacheEntry | null>): Promise<BitmapCacheEntry | null> {
    this.inflight.set(key, promise);
    const done = () => {
      if (this.inflight.get(key) === promise) this.inflight.delete(key);
    };
    promise.then(done, done);
    return promise;
  }

  isInflight(key: string): boolean {
    return this.inflight.has(key);
  }

  clear(): void {
    for (const e of this.map.values()) e.bitmap.close();
    this.map.clear();
    this.inflight.clear();
  }

  get size(): number {
    return this.map.size;
  }
}
