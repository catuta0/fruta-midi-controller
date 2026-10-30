// Minimal static server for docs/ on 127.0.0.1 with an optional in-memory mutation of
// index.html (used only to prove the tests fail on wrong behaviour; docs/ is never written).
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../docs');

// name -> [original text, replacement text, test expected to fail]
export const MUTATIONS = {
  vel0_is_note_on: ['type === 0x90 && d2 > 0', 'type === 0x90 && d2 >= 0', 'note on velocity 0 acts as note off'],
  pad_base_note_35: ['note: 36 + i, buffer', 'note: 35 + i, buffer', 'each pad plays on its default note 36..47'],
  busy_reported_as_ok: ['() => busy.push(input.name)', '() => names.push(input.name)', 'busy device shows the busy error'],
  aftertouch_ignored: ['} else if (type === 0xa0) {', '} else if (type === 0xa1) {', 'poly aftertouch opens the synth filter'],
  learn_ignored: ['if (learning >= 0) { assignNote(', 'if (learning < -1) { assignNote(', 'learn mode assigns the next note and persists it'],
  learn_no_swap: ['if (other >= 0) pads[other].note = pads[i].note;', '', 'learning a note already used by another pad swaps the two pads notes'],
  gate_no_flash: ['if (!ctx) { flash(i); nudgeGate(); return; }', 'if (!ctx) return;', 'notes before the audio gate click flash the pad and emphasise the enable-sound hint'],
};

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.wav': 'audio/wav' };

// pageFile: optional alternative file served as index.html (e.g. the old revision fixture).
export async function startServer(mutation, pageFile) {
  let indexHtml = await fs.readFile(pageFile || path.join(DOCS, 'index.html'), 'utf8');
  if (mutation) {
    const m = MUTATIONS[mutation];
    if (!m) throw new Error('unknown mutation ' + mutation);
    if (!indexHtml.includes(m[0])) throw new Error('mutation anchor not found: ' + m[0]);
    indexHtml = indexHtml.replace(m[0], m[1]);
  }
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      let rel = decodeURIComponent(url.pathname);
      if (rel.endsWith('/')) rel += 'index.html';
      const file = path.resolve(DOCS, '.' + rel);
      if (!file.startsWith(DOCS + path.sep)) { res.writeHead(403).end(); return; }
      const body = file === path.join(DOCS, 'index.html') ? indexHtml : await fs.readFile(file);
      res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(body);
    } catch (e) {
      res.writeHead(404).end();
    }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  return { server, url: `http://127.0.0.1:${server.address().port}/` };
}
