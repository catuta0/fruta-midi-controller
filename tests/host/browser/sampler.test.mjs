// T-020: headless-Chrome tests of docs/index.html MIDI behaviour with a stubbed Web MIDI API.
// Run: node --test --test-reporter=tap tests/host/browser/sampler.test.mjs
// Env: SAMPLER_MUTATION=<name from server.mjs> serves a deliberately broken page (mutation check).
//      SAMPLER_FILE=<path> serves another file as index.html (e.g. fixtures/index_e4668d4.html).
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { startServer } from './server.mjs';
import { installStub } from './stub.mjs';
import fs from 'node:fs';

const PT = JSON.parse(fs.readFileSync(new URL('./pt_strings.json', import.meta.url), 'utf8')).strings;

const FRUTA = { id: 'in-fruta', name: 'FrutaMIDI' };
const OK_CFG = { mode: 'ok', inputs: [FRUTA] };
const T = { timeout: 30000 };

let browser, srv;

before(async () => {
  srv = await startServer(process.env.SAMPLER_MUTATION || '', process.env.SAMPLER_FILE || '');
  browser = await chromium.launch({
    channel: 'chrome', headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'],
  });
});
after(async () => {
  if (browser) await browser.close();
  if (srv) srv.server.close();
});

async function openPage(cfg = OK_CFG, { gate = true, context = null } = {}) {
  const ctx = context || await browser.newContext();
  await ctx.addInitScript(installStub, cfg);
  const page = await ctx.newPage();
  page.errors = [];
  page.on('pageerror', (e) => page.errors.push(String(e)));
  await page.goto(srv.url);
  await page.waitForFunction(() => !['Looking for MIDI…', 'A procurar MIDI…'].includes(document.getElementById('statusText').textContent));
  if (gate) await page.click('#start');
  return { ctx, page };
}

// Send one MIDI message and snapshot the page synchronously (the pad "hit" flash lasts 110 ms).
function send(page, bytes, id = FRUTA.id) {
  return page.evaluate(([id, bytes]) => {
    window.__probe.reset();
    // Clear any flash left by a previous message (it lasts 110 ms) so each snapshot is independent.
    document.querySelectorAll('#grid .pad.hit').forEach((e) => e.classList.remove('hit'));
    const delivered = window.__midi.send(id, bytes);
    const pads = [...document.querySelectorAll('#grid .pad')];
    return {
      delivered,
      hits: pads.map((p, i) => (p.classList.contains('hit') ? i : -1)).filter((i) => i >= 0),
      log: document.getElementById('log').textContent,
      starts: window.__probe.starts, stops: window.__probe.stops,
      paramSets: window.__probe.paramSets, targets: window.__probe.targets,
      atWidths: pads.map((p) => p.querySelector('.at').style.width),
    };
  }, [id, bytes]);
}

const status = (page) => page.evaluate(() => ({
  text: document.getElementById('statusText').textContent,
  dot: document.getElementById('dot').className.trim(),
}));
const padNotes = (page) => page.$$eval('#grid .pad .note', (els) => els.map((e) => e.textContent));
const close = async ({ ctx, page }) => { assert.deepEqual(page.errors, [], 'page errors'); await ctx.close(); };

// --------------------------------------------------------------------------------------------
test('connected device is auto-selected and shown', T, async () => {
  const p = await openPage();
  const s = await status(p.page);
  assert.equal(s.text, 'Connected: FrutaMIDI');
  assert.equal(s.dot, 'dot on');
  const req = await p.page.evaluate(() => window.__probe.midiRequests);
  assert.equal(req.length, 1, 'requestMIDIAccess called once');
  await close(p);
});

test('port open statechange does not re-open the port', T, async () => {
  const p = await openPage();
  await p.page.waitForTimeout(100);
  assert.equal(await p.page.evaluate((id) => window.__midi.openCalls(id), FRUTA.id), 1);
  await close(p);
});

test('each pad plays on its default note 36..47', T, async () => {
  const p = await openPage();
  for (let i = 0; i < 12; i++) {
    const r = await send(p.page, [0x90, 36 + i, 100]);
    assert.deepEqual(r.hits, [i], `note ${36 + i} must flash pad ${i} only`);
    assert.ok(r.starts.length >= 1, `note ${36 + i} must start at least one source`);
  }
  await close(p);
});

test('note on is logged with name, velocity and channel', T, async () => {
  const p = await openPage();
  const r = await send(p.page, [0x90, 36, 100]);
  assert.equal(r.log, 'Note On  C1 (36)  vel 100  channel 1');
  const r2 = await send(p.page, [0x9f, 60, 1]);
  assert.equal(r2.log, 'Note On  C3 (60)  vel 1  channel 16');
  await close(p);
});

test('pad velocity scales output gain as (v/127)^1.5', T, async () => {
  const p = await openPage();
  for (const v of [127, 64, 1]) {
    const r = await send(p.page, [0x90, 36, v]);
    const g = r.paramSets.find((s) => s.owner === 'GainNode' && s.name === 'gain');
    assert.ok(g, 'pad output gain set');
    assert.ok(Math.abs(g.value - (v / 127) ** 1.5) < 1e-9, `vel ${v}: gain ${g.value}`);
  }
  await close(p);
});

test('kick pad (note 36) starts a sine oscillator', T, async () => {
  const p = await openPage();
  const r = await send(p.page, [0x90, 36, 100]);
  assert.deepEqual(r.starts.map((s) => [s.kind, s.type]), [['OscillatorNode', 'sine']]);
  await close(p);
});

test('unmapped note starts a two-oscillator synth voice at equal-tempered pitch', T, async () => {
  const p = await openPage();
  const r = await send(p.page, [0x90, 60, 100]);
  assert.deepEqual(r.hits, []);
  const saws = r.starts.filter((s) => s.kind === 'OscillatorNode' && s.type === 'sawtooth');
  assert.equal(saws.length, 2);
  for (const s of saws) assert.ok(Math.abs(s.freq - 440 * 2 ** ((60 - 69) / 12)) < 0.01, `freq ${s.freq}`);
  assert.deepEqual(saws.map((s) => s.detune).sort((a, b) => a - b), [-7, 7]);
  await close(p);
});

test('synth checkbox off silences unmapped notes', T, async () => {
  const p = await openPage();
  await p.page.uncheck('#synthOn');
  const r = await send(p.page, [0x90, 60, 100]);
  assert.equal(r.starts.length, 0);
  await close(p);
});

test('note off (0x80) stops the synth voice', T, async () => {
  const p = await openPage();
  const on = await send(p.page, [0x90, 60, 100]);
  const ids = on.starts.map((s) => s.id).sort();
  const off = await send(p.page, [0x80, 60, 64]);
  assert.deepEqual(off.stops.map((s) => s.id).sort(), ids, 'both oscillators stopped');
  assert.ok(off.targets.some((t) => t.owner === 'GainNode' && t.target === 0), 'gain released to 0');
  const again = await send(p.page, [0x80, 60, 64]);
  assert.equal(again.stops.length, 0, 'second note off is a no-op');
  await close(p);
});

test('note on velocity 0 acts as note off', T, async () => {
  const p = await openPage();
  const on = await send(p.page, [0x90, 60, 100]);
  const off = await send(p.page, [0x90, 60, 0]);
  assert.equal(off.starts.length, 0, 'velocity 0 must not start a voice');
  assert.deepEqual(off.stops.map((s) => s.id).sort(), on.starts.map((s) => s.id).sort());
  const pad = await send(p.page, [0x90, 36, 0]);
  assert.deepEqual(pad.hits, [], 'velocity 0 must not trigger a pad');
  assert.equal(pad.starts.length, 0);
  await close(p);
});

test('retriggering a held synth note replaces the old voice', T, async () => {
  const p = await openPage();
  const a = await send(p.page, [0x90, 60, 100]);
  const b = await send(p.page, [0x90, 60, 100]);
  assert.deepEqual(b.stops.map((s) => s.id).sort(), a.starts.map((s) => s.id).sort());
  assert.equal(b.starts.length, 2);
  await close(p);
});

test('poly aftertouch opens the synth filter', T, async () => {
  const p = await openPage();
  await send(p.page, [0x90, 60, 100]);
  const r = await send(p.page, [0xa0, 60, 127]);
  const f = r.targets.find((t) => t.owner === 'BiquadFilterNode' && t.ownerType === 'lowpass' && t.name === 'frequency');
  assert.ok(f, 'lowpass frequency target set');
  assert.equal(f.target, 900 + 127 * 45);
  const other = await send(p.page, [0xa0, 61, 127]);
  assert.equal(other.targets.length, 0, 'aftertouch on a note without a voice changes no filter');
  await close(p);
});

test('poly aftertouch on a pad note drives the pad bar; note off resets it', T, async () => {
  const p = await openPage();
  await send(p.page, [0x90, 37, 100]);
  let r = await send(p.page, [0xa0, 37, 127]);
  assert.equal(r.atWidths[1], '100%');
  r = await send(p.page, [0xa0, 37, 64]);
  // CSS serialises the width with ~6 significant digits, so compare to 1e-3 %.
  assert.ok(Math.abs(parseFloat(r.atWidths[1]) - 64 / 127 * 100) < 1e-3, r.atWidths[1]);
  assert.ok(r.atWidths.every((w, i) => i === 1 || w === '' || parseFloat(w) === 0), 'other pads untouched');
  r = await send(p.page, [0x80, 37, 0]);
  assert.equal(parseFloat(r.atWidths[1]), 0);
  await close(p);
});

test('notes on any channel are accepted (omni)', T, async () => {
  const p = await openPage();
  for (const ch of [0, 1, 9, 15]) {
    const r = await send(p.page, [0x90 | ch, 38, 90]);
    assert.deepEqual(r.hits, [2], `channel ${ch + 1}`);
  }
  await close(p);
});

test('non-note messages are ignored without errors', T, async () => {
  const p = await openPage();
  for (const m of [[0xf8], [0xfe], [0xc0, 5], [0xb0, 64, 127], [0xe0, 0, 64], [0xd0, 100]]) {
    const r = await send(p.page, m);
    assert.equal(r.starts.length, 0, `message ${m} must not start a voice`);
    assert.deepEqual(r.hits, []);
  }
  await close(p);
});

test('MIDI access rejected shows the permission error', T, async () => {
  const p = await openPage({ mode: 'reject' }, { gate: false });
  const s = await status(p.page);
  assert.match(s.text, /^MIDI access denied/);
  assert.equal(s.dot, 'dot err');
  await close(p);
});

test('browser without Web MIDI shows the unsupported error', T, async () => {
  const p = await openPage({ mode: 'absent' }, { gate: false });
  const s = await status(p.page);
  assert.match(s.text, /^This browser has no Web MIDI/);
  assert.equal(s.dot, 'dot err');
  await close(p);
});

test('busy device shows the busy error', T, async () => {
  const p = await openPage({ mode: 'ok', inputs: [{ ...FRUTA, busy: true }] }, { gate: false });
  await p.page.waitForFunction(() => document.getElementById('dot').className.trim() !== 'dot');
  const s = await status(p.page);
  assert.match(s.text, /^FrutaMIDI is being used by another program/);
  assert.equal(s.dot, 'dot err');
  await close(p);
});

test('busy device next to a free one is listed as busy', T, async () => {
  const cfg = { mode: 'ok', inputs: [{ id: 'in-other', name: 'Other' }, { ...FRUTA, busy: true }] };
  const p = await openPage(cfg, { gate: false });
  await p.page.waitForFunction(() => document.getElementById('dot').className.trim() !== 'dot');
  const s = await status(p.page);
  assert.equal(s.text, 'Connected: Other · busy: FrutaMIDI');
  assert.equal(s.dot, 'dot on');
  await close(p);
});

test('no device shows the plug-in hint; hot-plug connects; unplug reverts', T, async () => {
  const p = await openPage({ mode: 'ok', inputs: [] });
  assert.equal((await status(p.page)).text, 'No MIDI device. Connect FrutaMIDI to USB.');
  await p.page.evaluate((d) => window.__midi.plug(d), FRUTA);
  await p.page.waitForFunction(() => document.getElementById('statusText').textContent.startsWith('Connected'));
  assert.equal((await status(p.page)).text, 'Connected: FrutaMIDI');
  const r = await send(p.page, [0x90, 36, 100]);
  assert.deepEqual(r.hits, [0], 'hot-plugged input delivers notes');
  await p.page.evaluate((id) => window.__midi.unplug(id), FRUTA.id);
  await p.page.waitForFunction(() => document.getElementById('statusText').textContent.startsWith('No MIDI device'));
  await close(p);
});

test('learn mode assigns the next note and persists it', T, async () => {
  const ctx = await browser.newContext();
  const p = await openPage(OK_CFG, { context: ctx });
  const learn = p.page.locator('#grid .pad').nth(3).locator('.learn');
  await learn.click();
  assert.ok(await p.page.locator('#grid .pad').nth(3).evaluate((e) => e.classList.contains('learning')));
  assert.match(await p.page.textContent('#log'), /^Learning: touch the fruit that should trigger "Open hi-hat"/);
  const r = await send(p.page, [0x90, 60, 100]);
  assert.deepEqual(r.hits, [3], 'learned pad plays immediately');
  assert.equal((await padNotes(p.page))[3], 'C3 · 60');
  assert.equal(await p.page.locator('#grid .pad.learning').count(), 0, 'learning cleared');
  const stored = await p.page.evaluate(() => JSON.parse(localStorage.getItem('frutamidi-sampler-notes')));
  assert.deepEqual(stored, [36, 37, 38, 60, 40, 41, 42, 43, 44, 45, 46, 47]);
  const r2 = await send(p.page, [0x90, 39, 100]);
  assert.deepEqual(r2.hits, [], 'old note 39 no longer maps to a pad');
  // persists across reload
  await p.page.reload();
  await p.page.waitForFunction(() => document.getElementById('statusText').textContent.startsWith('Connected'));
  await p.page.click('#start');
  assert.equal((await padNotes(p.page))[3], 'C3 · 60');
  // reset restores factory notes
  await p.page.click('#reset');
  assert.equal((await padNotes(p.page))[3], 'D#1 · 39');
  assert.equal(await p.page.textContent('#log'), 'Sounds and notes reset.');
  await close(p);
});

test('learn button pressed twice cancels learning', T, async () => {
  const p = await openPage();
  const learn = p.page.locator('#grid .pad').nth(5).locator('.learn');
  await learn.click();
  await learn.click();
  assert.equal(await p.page.locator('#grid .pad.learning').count(), 0);
  const r = await send(p.page, [0x90, 60, 100]);
  assert.deepEqual(r.hits, []);
  assert.equal((await padNotes(p.page))[5], 'F1 · 41');
  await close(p);
});

test('keyboard fallback plays pads (no MIDI needed)', T, async () => {
  const p = await openPage({ mode: 'absent' });
  const hit = await p.page.evaluate(() => {
    window.__probe.reset();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'w' }));
    return { hit: document.querySelectorAll('#grid .pad')[5].classList.contains('hit'), starts: window.__probe.starts.length };
  });
  assert.ok(hit.hit && hit.starts >= 1);
  await close(p);
});

// ------------------------- ADR-005 intended behaviour (SW-1, SW-2) -------------------------
test('notes before the audio gate click flash the pad and emphasise the enable-sound hint', T, async () => {
  const p = await openPage(OK_CFG, { gate: false });
  assert.ok(await p.page.isVisible('#gate'), 'gate visible before the click');
  const r = await send(p.page, [0x90, 36, 100]);
  assert.equal(r.starts.length, 0, 'no sound before the gate');
  assert.deepEqual(r.hits, [0], 'pad 0 flashes even without audio');
  assert.ok(await p.page.$eval('#start', (b) => b.classList.contains('nudge')), 'hint emphasised');
  assert.equal(r.log, 'Note On  C1 (36)  vel 100  channel 1');
  assert.equal(await p.page.textContent('#start'), 'Click to enable sound');
  // unmapped (synth) note also emphasises the hint and starts nothing
  await p.page.$eval('#start', (b) => b.classList.remove('nudge'));
  const s = await send(p.page, [0x90, 60, 100]);
  assert.equal(s.starts.length, 0);
  assert.ok(await p.page.$eval('#start', (b) => b.classList.contains('nudge')), 'hint emphasised for synth note');
  // after the click, sound works and the gate is gone
  await p.page.click('#start');
  assert.equal(await p.page.$('#gate'), null);
  const after = await send(p.page, [0x90, 36, 100]);
  assert.ok(after.starts.length >= 1);
  await close(p);
});

test('learning a note already used by another pad swaps the two pads notes', T, async () => {
  const p = await openPage();
  await p.page.locator('#grid .pad').nth(0).locator('.learn').click();
  const learnHit = await send(p.page, [0x90, 37, 100]);   // pad 0 learns 37, which pad 1 used
  assert.deepEqual(learnHit.hits, [0]);
  const notes = await padNotes(p.page);
  assert.equal(notes[0], 'C#1 · 37');
  assert.equal(notes[1], 'C1 · 36', 'pad 1 receives pad 0 old note');
  assert.deepEqual((await send(p.page, [0x90, 37, 100])).hits, [0]);
  assert.deepEqual((await send(p.page, [0x90, 36, 100])).hits, [1], 'pad 1 still reachable');
  const stored = await p.page.evaluate(() => JSON.parse(localStorage.getItem('frutamidi-sampler-notes')));
  assert.deepEqual(stored, [37, 36, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]);
  // learning a free note does not touch other pads
  await p.page.locator('#grid .pad').nth(2).locator('.learn').click();
  await send(p.page, [0x90, 72, 100]);
  const n2 = await padNotes(p.page);
  assert.deepEqual(n2.slice(0, 4), ['C#1 · 37', 'C1 · 36', 'C4 · 72', 'D#1 · 39']);
  await close(p);
});

test('no Portuguese UI strings in any rendered state', T, async () => {
  const visible = PT.filter((x) => !/[<>"'$]/.test(x));
  const grab = (page) => page.evaluate(() => {
    const attrs = [...document.querySelectorAll('[title],[aria-label],[placeholder],[alt]')]
      .flatMap((e) => ['title', 'aria-label', 'placeholder', 'alt'].map((a) => e.getAttribute(a) || ''));
    return { lang: document.documentElement.lang, text: [document.title, document.body.innerText, ...attrs].join('\n') };
  });
  const seen = [];
  const check = async (page, label) => {
    const g = await grab(page);
    const bad = visible.filter((x) => g.text.includes(x));
    assert.deepEqual(bad, [], `${label}: Portuguese strings found`);
    assert.equal(g.lang, 'en', `${label}: html lang`);
    seen.push(label);
  };
  let p = await openPage(OK_CFG, { gate: false });
  await check(p.page, 'gate');
  await p.page.click('#start');
  await check(p.page, 'connected');
  await p.page.locator('#grid .pad').nth(3).locator('.learn').click();
  await check(p.page, 'learning');
  await p.page.click('#reset');
  await check(p.page, 'reset');
  await close(p);
  for (const [label, cfg] of [['rejected', { mode: 'reject' }], ['absent', { mode: 'absent' }],
    ['busy', { mode: 'ok', inputs: [{ ...FRUTA, busy: true }] }], ['none', { mode: 'ok', inputs: [] }]]) {
    p = await openPage(cfg, { gate: false });
    await p.page.waitForFunction(() => document.getElementById('dot').className.trim() !== 'dot'
      || document.getElementById('statusText').textContent.length > 20);
    await check(p.page, label);
    await close(p);
  }
  assert.equal(seen.length, 8);
});
