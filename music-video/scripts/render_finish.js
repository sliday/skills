// BERLOGA: deterministic finishing renderer. NO TEXT. Only painterly effects:
// canvas weave, grain, gentle breathing camera, lightning flashes on beats in the storm, ember/ash drift, retimes.
// node render/render.js [--from s] [--to s] [--only b01,b02] [--workers N] [--out dir] [--force] [--every n]
import { createCanvas, loadImage } from '@napi-rs/canvas';
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { readFileSync, writeFileSync, renameSync, existsSync, mkdirSync, readdirSync } from 'fs';
import { cpus } from 'os';
import { fileURLToPath } from 'url';

const W = 1920, H = 1080, FPS = 24, DUR = 197.96, NF = Math.ceil(DUR * FPS);
const ROOT = new URL('..', import.meta.url).pathname;
const SHOTS = JSON.parse(readFileSync(ROOT + 'docs/shots.json'));
const BEATS = JSON.parse(readFileSync(ROOT + 'sound/analysis.json')).beats;

const hash = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
function lcg(seed) { let s = (seed >>> 0) || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
function beatPulse(t, k = 6) { let last = -9; for (const b of BEATS) { if (b > t) break; last = b; } return Math.exp(-(t - last) * k); }

// per-shot finishing: ember = khokhloma ember drift, ash = falling ash/sleet, bolt = lightning on beats
const FX = {
  b14: { ember: .5 }, b22: { ember: 1 }, b23: { ember: .8 }, b24: { ember: .7 }, b25: { ember: .8 }, b26: { ember: .8 },
  b27: { ember: 1, bolt: 1 }, b28: { ember: .6 }, b29: { ember: 1, bolt: .6 }, b31: { bolt: 1 }, b32: { ash: .6 }, b33: { ash: .5 },
  b34: { ember: .6 }, b35: { ash: .5 }, b39: { ash: .8, winter: true }, b40: { ash: 1, winter: true },
};
const RETIME = {};                                  // filled after plate QA (e.g. { b21: 0.85 })

const nFrames = {};
const count = (sid) => nFrames[sid] ??= (existsSync(`${ROOT}frames/${sid}`) ? readdirSync(`${ROOT}frames/${sid}`).filter(f => f.endsWith('.jpg')).length : 0);
async function plate(sid, pt) { const n = count(sid); if (!n) return null; const i = clamp(Math.floor(pt * FPS) + 1, 1, n); return loadImage(`${ROOT}frames/${sid}/${String(i).padStart(4, '0')}.jpg`); }
const shotAt = (t) => SHOTS.find(s => t >= s.t0 && t < s.t1) || SHOTS.at(-1);

let WEAVE = null, GRAIN = null, VIG = null;
function textures() {
  if (WEAVE) return;
  WEAVE = new Float32Array(W * H); VIG = new Float32Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {       // coarse woven canvas: two sine threads + irregularity
    const i = y * W + x, n = hash(Math.floor(x / 3) * 31 + Math.floor(y / 3) * 7);
    WEAVE[i] = 1 - 0.045 * (0.5 + 0.5 * Math.sin(x * 1.9)) * (0.5 + 0.5 * Math.sin(y * 1.9 + Math.sin(x * .05))) - 0.02 * n;
    const dx = (x / W - .5) * 1.1, dy = (y / H - .5) * 1.3; VIG[i] = 1 - 0.28 * smooth(0.35, 0.95, Math.sqrt(dx * dx + dy * dy));
  }
  GRAIN = []; for (let k = 0; k < 6; k++) { const r = lcg(31 + k), a = new Float32Array(W * H); for (let i = 0; i < a.length; i++) a[i] = (r() - 0.5) * 7; GRAIN.push(a); }
}
function finish(d, t, flash, cold) {
  textures(); const g = GRAIN[Math.floor(t * 12) % 6];
  for (let i = 0, p = 0; i < W * H; i++, p += 4) {
    const m = WEAVE[i] * VIG[i];
    let r = d[p] * m + g[i], gg = d[p + 1] * m + g[i], b = d[p + 2] * m + g[i];
    if (flash > 0) { const l = (r + gg + b) / 3; r += (230 - l * 0.2) * flash; gg += (235 - l * 0.2) * flash; b += (255 - l * 0.2) * flash; }
    if (cold) { const l = (r + gg + b) / 3; r = l + (r - l) * 0.8 - 4; b = l + (b - l) * 0.8 + 6; }
    d[p] = r; d[p + 1] = gg; d[p + 2] = b;
  }
}
function particles(g, t, s, fx) {
  const r = lcg(s.id.charCodeAt(1) * 97 + s.id.charCodeAt(2));
  if (fx.ember) for (let i = 0; i < 70 * fx.ember; i++) {   // khokhloma embers: small red/gold dabs rising and curling
    const x0 = r() * W, sp = 40 + r() * 90, ph = r() * 20, life = 3 + r() * 3, age = ((t + ph) % life) / life;
    const x = x0 + Math.sin((t + ph) * 1.3) * 30, y = H - age * (H * 0.9) - (r() * 60);
    g.globalAlpha = Math.sin(age * Math.PI) * 0.8; g.fillStyle = r() < 0.5 ? '#E23A1C' : '#E8B23A';
    g.beginPath(); g.ellipse(x, y, 3 + r() * 4, 2 + r() * 3, (t + ph) % 6, 0, 7); g.fill();
  }
  if (fx.ash) for (let i = 0; i < 160 * fx.ash; i++) {       // ash in autumn, dirty sleet in winter
    const x0 = r() * W, sp = 50 + r() * 80, ph = r() * 30;
    const y = ((t + ph) * sp) % (H + 40) - 20, x = x0 + Math.sin((t + ph) * 0.8) * 25;
    g.globalAlpha = 0.35 + r() * 0.35; g.fillStyle = fx.winter ? '#CFCBC2' : '#3A3430';
    g.beginPath(); g.arc(x, y, 1.5 + r() * 2.5, 0, 7); g.fill();
  }
  g.globalAlpha = 1;
}

let CAN = null;
async function renderFrame(f) {
  CAN ??= createCanvas(W, H); const g = CAN.getContext('2d');
  const t = f / FPS, s = shotAt(t), lt = t - s.t0, fx = FX[s.id] ?? {};
  const im = await plate(s.id, lt * (RETIME[s.id] ?? 1));
  g.fillStyle = '#0b1020'; g.fillRect(0, 0, W, H);
  if (im) { // painted-canvas "breathing": a very slow 1-2% drift, like looking at a canvas on a wall
    const k = 1.02 + 0.01 * Math.sin(t * 0.21), dx = Math.sin(t * 0.13 + s.t0) * 10, dy = Math.cos(t * 0.11) * 6;
    g.drawImage(im, (W - W * k) / 2 + dx, (H - H * k) / 2 + dy, W * k, H * k);
  }
  const flash = fx.bolt ? fx.bolt * 0.45 * Math.pow(beatPulse(t, 14), 2) * (hash(Math.floor(t * 129.2 / 60)) > 0.5 ? 1 : 0) : 0;
  const id = g.getImageData(0, 0, W, H); finish(id.data, t, flash, !!fx.winter); g.putImageData(id, 0, 0);
  particles(g, t, s, fx);
  if (t < 1.2) { g.fillStyle = `rgba(0,0,0,${1 - smooth(0, 1.2, t)})`; g.fillRect(0, 0, W, H); }
  if (t > DUR - 2.5) { g.fillStyle = `rgba(0,0,0,${smooth(DUR - 2.5, DUR - 0.2, t)})`; g.fillRect(0, 0, W, H); }
  return CAN.toBuffer('image/jpeg', 92);
}

function args() { const a = process.argv.slice(2), o = {}; for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) { const k = a[i].slice(2); o[k] = a[i + 1] && !a[i + 1].startsWith('--') ? a[++i] : true; } return o; }
if (isMainThread) {
  const o = args(), out = ROOT + (o.out ?? 'render/frames'); mkdirSync(out, { recursive: true });
  let list = []; const from = Math.floor((+o.from || 0) * FPS), to = Math.min(NF, Math.ceil((o.to ? +o.to : DUR) * FPS));
  for (let f = from; f < to; f++) list.push(f);
  if (o.only) { const ids = o.only.split(','); list = list.filter(f => ids.includes(shotAt(f / FPS).id)); }
  if (o.every) list = list.filter((_, i) => i % +o.every === 0);
  if (!o.force) list = list.filter(f => !existsSync(`${out}/${String(f).padStart(5, '0')}.jpg`));
  const N = Math.min(+o.workers || Math.max(1, cpus().length - 2), list.length || 1); let done = 0, pending = N; const t0 = Date.now();
  console.log(`rendering ${list.length} frames with ${N} workers -> ${out}`);
  for (let k = 0; k < N; k++) {
    const w = new Worker(fileURLToPath(import.meta.url), { workerData: { frames: list.filter((_, i) => i % N === k), out } });
    w.on('message', () => { done++; }); w.on('error', e => { console.error('worker error', e); process.exitCode = 1; });
    w.on('exit', () => { if (--pending === 0) console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`); });
  }
} else {
  const { frames, out } = workerData;
  for (const f of frames) { const buf = await renderFrame(f), p = `${out}/${String(f).padStart(5, '0')}.jpg`; writeFileSync(p + '.tmp', buf); renameSync(p + '.tmp', p); parentPort.postMessage(f); }
}
