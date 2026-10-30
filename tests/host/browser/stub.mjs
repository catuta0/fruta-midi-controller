// Init script injected into the sampler page before any page script runs (T-020).
// It replaces navigator.requestMIDIAccess with a controllable fake and wraps a few
// Web Audio methods so tests can observe which voices the page starts and stops.
// The function is serialised by Playwright, so it must be self-contained.

export function installStub(cfg) {
  // ------------------------------ audio probe ------------------------------
  const probe = {
    starts: [], stops: [], paramSets: [], targets: [], midiRequests: [],
    reset() { this.starts = []; this.stops = []; this.paramSets = []; this.targets = []; },
  };
  window.__probe = probe;
  let nodeId = 0;

  const tagParams = (node) => {
    for (const name of ['gain', 'frequency', 'detune', 'Q']) {
      const p = node[name];
      if (p instanceof AudioParam) { p.__owner = node; p.__name = name; }
    }
    node.__id = ++nodeId;
    return node;
  };
  for (const m of ['createGain', 'createBiquadFilter', 'createOscillator', 'createBufferSource']) {
    const orig = BaseAudioContext.prototype[m];
    BaseAudioContext.prototype[m] = function (...a) { return tagParams(orig.apply(this, a)); };
  }
  const describeParam = (p) => ({
    owner: p.__owner ? p.__owner.constructor.name : null,
    ownerType: p.__owner && 'type' in p.__owner ? p.__owner.type : null,
    ownerId: p.__owner ? p.__owner.__id : null,
    name: p.__name || null,
  });
  const valueDesc = Object.getOwnPropertyDescriptor(AudioParam.prototype, 'value');
  Object.defineProperty(AudioParam.prototype, 'value', {
    configurable: true, enumerable: valueDesc.enumerable,
    get() { return valueDesc.get.call(this); },
    set(v) { if (this.__owner) probe.paramSets.push({ ...describeParam(this), value: v }); valueDesc.set.call(this, v); },
  });
  const origTarget = AudioParam.prototype.setTargetAtTime;
  AudioParam.prototype.setTargetAtTime = function (target, t, tc) {
    if (this.__owner) probe.targets.push({ ...describeParam(this), target, tc });
    return origTarget.call(this, target, t, tc);
  };
  const desc = (n) => ({
    kind: n.constructor.name, id: n.__id,
    type: 'type' in n ? n.type : null,
    freq: n.frequency ? n.frequency.value : null,
    detune: n.detune ? n.detune.value : null,
  });
  // AudioBufferSourceNode defines its own start(when, offset, duration), so wrap every
  // prototype that owns start/stop, not only AudioScheduledSourceNode.
  for (const C of [AudioScheduledSourceNode, AudioBufferSourceNode, OscillatorNode, ConstantSourceNode]) {
    for (const [m, list] of [['start', 'starts'], ['stop', 'stops']]) {
      if (!Object.prototype.hasOwnProperty.call(C.prototype, m)) continue;
      const orig = C.prototype[m];
      C.prototype[m] = function (...a) { probe[list].push(desc(this)); return orig.apply(this, a); };
    }
  }

  // ------------------------------- MIDI stub -------------------------------
  const mode = cfg.mode || 'ok';
  if (mode === 'absent') {
    Object.defineProperty(Navigator.prototype, 'requestMIDIAccess', { value: undefined, configurable: true, writable: true });
    return;
  }

  const access = { inputs: new Map(), outputs: new Map(), sysexEnabled: false, onstatechange: null };
  const fireState = (port) => { if (typeof access.onstatechange === 'function') access.onstatechange({ port }); };

  class FakeInput {
    constructor(d) {
      this.id = d.id; this.name = d.name; this.manufacturer = d.manufacturer || 'Fruta';
      this.type = 'input'; this.version = '1.0';
      this.state = 'connected'; this.connection = 'closed';
      this.busy = !!d.busy; this.onmidimessage = null; this.openCalls = 0;
    }
    open() {
      this.openCalls++;
      if (this.busy) return Promise.reject(new DOMException('Port is busy', 'InvalidAccessError'));
      if (this.connection !== 'open') {
        this.connection = 'open';
        // Chrome fires a statechange when a port's connection changes; the page must not loop on it.
        queueMicrotask(() => fireState(this));
      }
      return Promise.resolve(this);
    }
    close() { this.connection = 'closed'; return Promise.resolve(this); }
  }

  for (const d of cfg.inputs || []) access.inputs.set(d.id, new FakeInput(d));

  window.__midi = {
    access,
    send(id, bytes) {
      const input = access.inputs.get(id);
      if (!input) throw new Error('no fake input ' + id);
      if (input.state !== 'connected' || typeof input.onmidimessage !== 'function') return false;
      input.onmidimessage({ data: Uint8Array.from(bytes), timeStamp: performance.now(), target: input });
      return true;
    },
    plug(d) { const i = new FakeInput(d); access.inputs.set(d.id, i); fireState(i); },
    unplug(id) { const i = access.inputs.get(id); i.state = 'disconnected'; i.connection = 'closed'; fireState(i); },
    openCalls(id) { return access.inputs.get(id).openCalls; },
  };

  const fake = function requestMIDIAccess(opts) {
    probe.midiRequests.push(opts || null);
    if (mode === 'reject') return Promise.reject(new DOMException('MIDI permission denied', 'NotAllowedError'));
    return Promise.resolve(access);
  };
  Object.defineProperty(Navigator.prototype, 'requestMIDIAccess', { value: fake, configurable: true, writable: true });
}
