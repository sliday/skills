// 9:16 recompose of the finished 16:9 frames, shot by shot: a focal x (0..1) or a pan [x0, x1] across the shot.
import { createCanvas, loadImage } from '@napi-rs/canvas';
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { readFileSync, writeFileSync, renameSync, existsSync, mkdirSync, readdirSync } from 'fs';
import { fileURLToPath } from 'url';
const ROOT = new URL('..', import.meta.url).pathname, FPS = 24, SW = 1920, SH = 1080, OW = 1080, OH = 1920, CW = Math.round(SH * 9 / 16);
const SHOTS = JSON.parse(readFileSync(ROOT + 'docs/shots.json'));
const FOCUS = {
  b01: .6, b02: .35, b03: .4, b04: .5, b05: .45, b06: .42, b07: [.3, .55], b08: .5, b09: .5, b10: .55, b11: .45, b12: [.35, .82],
  b13: .45, b14: [.5, .8], b15: .35, b16: .5, b17: .45, b18: [.25, .45], b19: .55, b20: [.3, .7], b21: .35, b22: .5, b23: .45,
  b24: [.3, .75], b25: .4, b26: .5, b27: [.3, .6], b28: [.35, .72], b29: .4, b30: [.4, .68], b31: .4, b32: .3, b33: [.3, .55],
  b34: .5, b35: .45, b36: .45, b37: .45, b38: .45, b39: [.35, .55], b40: [.5, .82],
};
const ease = (t) => t * t * (3 - 2 * t);
const shotAt = (t) => SHOTS.find(s => t >= s.t0 && t < s.t1) || SHOTS.at(-1);
async function frame(f) {
  const t = f / FPS, s = shotAt(t), fc = FOCUS[s.id] ?? .5, k = ease(Math.min(1, Math.max(0, (t - s.t0) / (s.t1 - s.t0))));
  const fx = Array.isArray(fc) ? fc[0] + (fc[1] - fc[0]) * k : fc;
  const sx = Math.min(SW - CW, Math.max(0, Math.round(fx * SW - CW / 2)));
  const im = await loadImage(`${ROOT}render/frames/${String(f).padStart(5, '0')}.jpg`);
  const c = createCanvas(OW, OH), g = c.getContext('2d'); g.imageSmoothingQuality = 'high';
  g.drawImage(im, sx, 0, CW, SH, 0, 0, OW, OH); return c.toBuffer('image/jpeg', 90);
}
if (isMainThread) {
  const out = ROOT + 'render/vframes'; mkdirSync(out, { recursive: true });
  const n = readdirSync(ROOT + 'render/frames').filter(x => x.endsWith('.jpg')).length, list = [...Array(n).keys()], N = 14; let left = N;
  for (let k = 0; k < N; k++) new Worker(fileURLToPath(import.meta.url), { workerData: { frames: list.filter((_, i) => i % N === k), out } }).on('exit', () => { if (--left === 0) console.log('done', n); });
} else {
  for (const f of workerData.frames) { const p = `${workerData.out}/${String(f).padStart(5, '0')}.jpg`; writeFileSync(p + '.tmp', await frame(f)); renameSync(p + '.tmp', p); }
}
