// Host probe for FrutaMIDI pure logic headers (firmware/FrutaMIDI/fm_*.h).
// Reads one command per line on stdin, writes one result line per command on stdout.
// The Python tests in this folder hold the expected values; this file only calls the
// production functions, so a wrong header makes those tests fail.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "fm_time.h"
#include "fm_scales.h"
#include "fm_debounce.h"
#include "fm_aftertouch.h"
#include "fm_button.h"
#include "fm_pot.h"
#include "fm_midi.h"
#include "fm_blink.h"
#include "fm_mpr121.h"
#include "fm_notes.h"
#include "fm_sensor_health.h"

static const char* ev_name(fm::ButtonEvent e) {
  switch (e) {
    case fm::ButtonEvent::ShortPress: return "S";
    case fm::ButtonEvent::LongPress:  return "L";
    default:                          return "-";
  }
}

int main() {
  std::string line;
  while (std::getline(std::cin, line)) {
    std::istringstream in(line);
    std::string cmd;
    in >> cmd;
    std::ostringstream out;
    if (cmd == "nscales") {
      out << (int)fm::NUM_SCALES;
    } else if (cmd == "scale") {                 // scale <i> -> root len fixed steps...
      int i; in >> i;
      const fm::Scale& sc = fm::SCALES[i];
      out << (int)sc.root << ' ' << (int)sc.len << ' ' << (sc.fixed ? 1 : 0);
      for (int k = 0; k < sc.len; k++) out << ' ' << (int)sc.steps[k];
    } else if (cmd == "note") {                  // note <scale> <oct> <pad>
      int i, o, p; in >> i >> o >> p;
      out << (int)fm::note_for_pad(fm::SCALES[i], (int8_t)o, (uint8_t)p);
    } else if (cmd == "notec") {                 // notec <root> <fixed> <oct> <pad> <steps...>
      int root, fixed, o, p, v; in >> root >> fixed >> o >> p;
      fm::Scale sc = {"custom", (uint8_t)root, 0, {0}, fixed != 0};
      while (in >> v && sc.len < 12) sc.steps[sc.len++] = (int8_t)v;
      out << (int)fm::note_for_pad(sc, (int8_t)o, (uint8_t)p);
    } else if (cmd == "next") {                  // next <idx> <count>
      int i, n; in >> i >> n;
      out << (int)fm::next_scale_index((uint8_t)i, (uint8_t)n);
    } else if (cmd == "ge" || cmd == "gt") {     // ge|gt <now> <since> <interval>
      unsigned long a, b, c; in >> a >> b >> c;
      bool r = cmd == "ge" ? fm::elapsed_at_least((uint32_t)a, (uint32_t)b, (uint32_t)c)
                           : fm::elapsed_more_than((uint32_t)a, (uint32_t)b, (uint32_t)c);
      out << (r ? 1 : 0);
    } else if (cmd == "debounce") {              // debounce <touched> <active> <now> <last> <ms>
      int t, a; unsigned long now, last, ms; in >> t >> a >> now >> last >> ms;
      out << (fm::pad_change_allowed(t != 0, a != 0, (uint32_t)now, (uint32_t)last, (uint16_t)ms) ? 1 : 0);
    } else if (cmd == "touched") {               // touched <bits> <electrode>
      unsigned b; int e; in >> b >> e;
      out << (fm::pad_touched((uint16_t)b, (uint8_t)e) ? 1 : 0);
    } else if (cmd == "at") {                    // at <delta> <threshold> <max>
      int d, t, m; in >> d >> t >> m;
      out << (int)fm::pressure_from_delta(d, t, m);
    } else if (cmd == "atsend") {                // atsend <p> <last>
      int p, l; in >> p >> l;
      out << (fm::pressure_should_send((uint8_t)p, (uint8_t)l) ? 1 : 0);
    } else if (cmd == "pot") {                   // pot <adc> <current>
      int adc, cur; in >> adc >> cur;
      out << (int)fm::octave_from_adc(adc, (int8_t)cur);
    } else if (cmd == "bupdate") {               // bupdate t:d t:d ... (update() only, no sampling gate)
      fm::ButtonClassifier b; std::string tok; bool first = true;
      while (in >> tok) {
        size_t c = tok.find(':');
        uint32_t t = (uint32_t)std::strtoul(tok.substr(0, c).c_str(), nullptr, 10);
        bool d = tok.substr(c + 1) == "1";
        out << (first ? "" : " ") << ev_name(b.update(t, d)); first = false;
      }
    } else if (cmd == "bdue") {                  // bdue t t t ... -> 1/0 per call
      fm::ButtonClassifier b; unsigned long t; bool first = true;
      while (in >> t) { out << (first ? "" : " ") << (b.sample_due((uint32_t)t) ? 1 : 0); first = false; }
    } else if (cmd == "btrace") {                // btrace <bits>: char i = pin state at t=i ms, called every ms
      fm::ButtonClassifier b; std::string bits; in >> bits; bool first = true;
      for (uint32_t t = 0; t < bits.size(); t++) {
        if (!b.sample_due(t)) continue;
        fm::ButtonEvent e = b.update(t, bits[t] == '1');
        if (e != fm::ButtonEvent::None) { out << (first ? "" : " ") << t << ':' << ev_name(e); first = false; }
      }
    } else if (cmd == "status") {                // status <status> <channel>
      int s, c; in >> s >> c;
      out << (int)fm::channel_status((uint8_t)s, (uint8_t)c);
    } else if (cmd == "blink") {                 // blink <times> <ms> <tick_ms> <T>: start at t=0
      int times, ms, tick, T; in >> times >> ms >> tick >> T;
      fm::Blinker b; b.start(0, (uint8_t)times, (uint16_t)ms);
      bool lvl = false, first = true, ended = false;
      for (int t = 0; t < T; t += tick) {
        bool on = b.level_or((uint32_t)t, false);
        if (on != lvl || t == 0) { out << (first ? "" : " ") << t << ':' << (on ? 1 : 0); first = false; lvl = on; }
        if (!b.active() && !ended) { out << " END:" << t; ended = true; }
      }
    } else if (cmd == "padstep") {               // padstep <touched> <active> <now> <last> <ms> -> action new_last
      int t, a; unsigned long now, last, ms; in >> t >> a >> now >> last >> ms;
      uint32_t l = (uint32_t)last;
      fm::PadAction act = fm::pad_step(t != 0, a != 0, (uint32_t)now, l, (uint16_t)ms);
      out << (act == fm::PadAction::Press ? "P" : act == fm::PadAction::Release ? "R" : "-") << ' ' << l;
    } else if (cmd == "loopsim") {
      // loopsim <blocking 0|1> <scaleIdx> <debounce_ms> <button_bits> <pad_bits>
      // One char per ms (1 = pressed / touched). Mirrors loop(): handleButton, pad 0, LED.
      // blocking=1 models the old delay()-based blink(): nothing else runs until it ends.
      int blocking, idx, db; std::string bb, pb; in >> blocking >> idx >> db >> bb >> pb;
      fm::ButtonClassifier button; fm::Blinker led;
      uint8_t note = 255; uint32_t lastChange = 0, blockedUntil = 0; bool lvl = false, first = true;
      auto emit = [&](uint32_t t, const char* what, int v) {
        out << (first ? "" : " ") << t << ':' << what << ':' << v; first = false;
      };
      for (uint32_t t = 0; t < pb.size() && t < bb.size(); t++) {
        bool touched = pb[t] == '1';
        if (!(blocking && t < blockedUntil)) {
          if (button.sample_due(t)) {
            fm::ButtonEvent e = button.update(t, bb[t] == '1');
            if (e == fm::ButtonEvent::ShortPress) {
              idx = fm::next_scale_index((uint8_t)idx, fm::NUM_SCALES);
              led.start(t, (uint8_t)(idx + 1), fm::BLINK_SCALE_MS);
              if (blocking) blockedUntil = t + 2u * (idx + 1) * fm::BLINK_SCALE_MS;
              emit(t, "SCALE", idx);
            }
          }
          if (!(blocking && t < blockedUntil)) {
            fm::PadAction a = fm::pad_step(touched, note != 255, t, lastChange, (uint16_t)db);
            if (a == fm::PadAction::Press) { note = fm::note_for_pad(fm::SCALES[idx], 0, 0); emit(t, "ON", note); }
            else if (a == fm::PadAction::Release) { emit(t, "OFF", note); note = 255; }
          }
        }
        bool on = led.level_or(t, touched);
        if (on != lvl) { emit(t, "LED", on ? 1 : 0); lvl = on; }
      }
    } else if (cmd == "atreset") {               // atreset <last>
      int l; in >> l;
      out << (fm::pressure_reset_on_release((uint8_t)l) ? 1 : 0);
    } else if (cmd == "scalename") {             // scalename <i>
      int i; in >> i;
      out << fm::SCALES[i].name;
    } else if (cmd == "padsim") {
      // padsim <debounce_ms> <at_interval_ms> <thr> <max> <touched:delta> ... (one token per ms)
      // Mirrors one pad in loop(): pressureDue, pad_step, pressPad / releasePad, sendPressure.
      int db, iv, thr, mx; in >> db >> iv >> thr >> mx;
      uint8_t note = 255, last = 0; uint32_t lastChange = 0, lastPressureMs = 0; bool first = true;
      auto emit = [&](uint32_t t, const char* what, int v) {
        out << (first ? "" : " ") << t << ':' << what << ':' << v; first = false;
      };
      std::string tok;
      for (uint32_t t = 0; in >> tok; t++) {
        size_t c = tok.find(':');
        bool touched = tok.substr(0, c) == "1";
        int delta = std::atoi(tok.substr(c + 1).c_str());
        bool due = fm::elapsed_at_least(t, lastPressureMs, (uint32_t)iv);
        if (due) lastPressureMs = t;
        fm::PadAction a = fm::pad_step(touched, note != 255, t, lastChange, (uint16_t)db);
        if (a == fm::PadAction::Press) { note = 60; last = 0; emit(t, "ON", note); }
        else if (a == fm::PadAction::Release) {
          if (fm::pressure_reset_on_release(last)) emit(t, "AT", 0);
          last = 0; emit(t, "OFF", note); note = 255;
        }
        if (due && note != 255) {
          uint8_t pr = fm::pressure_from_delta(delta, thr, mx);
          if (fm::pressure_should_send(pr, last)) { last = pr; emit(t, "AT", pr); }
        }
      }
    } else if (cmd == "mpr") {                   // mpr <24 filt bytes hex> <12 base bytes hex>
      uint8_t filt[fm::MPR121_FILT_BYTES], base[fm::MPR121_BASE_BYTES]; unsigned v;
      for (auto& b : filt) { in >> std::hex >> v; b = (uint8_t)v; }
      for (auto& b : base) { in >> std::hex >> v; b = (uint8_t)v; }
      for (uint8_t e = 0; e < fm::MPR121_ELECTRODES; e++)
        out << std::dec << (e ? " " : "") << fm::mpr121_filtered(filt, e) << '/'
            << fm::mpr121_baseline(base, e) << '/' << fm::mpr121_delta(filt, base, e);
    } else if (cmd == "runs") {                  // runs <mask> -> lo:n ... (or "none")
      unsigned m; in >> m; uint8_t lo, n; bool any = false;
      for (uint8_t from = 0; fm::mpr121_next_run((uint16_t)m, from, lo, n); from = (uint8_t)(lo + n)) {
        out << (any ? " " : "") << (int)lo << ':' << (int)n; any = true;
      }
      if (!any) out << "none";
    } else if (cmd == "mprcfg") {                // mprcfg <vdd_mv> -> ac1 usl tl lsl
      int v; in >> v; uint8_t u = fm::mpr121_usl((uint16_t)v);
      out << (int)fm::MPR121_AUTOCONFIG1_VALUE << ' ' << (int)u << ' ' << (int)fm::mpr121_tl(u) << ' '
          << (int)fm::mpr121_lsl(u);
    } else if (cmd == "ac1") {                   // ac1 <scts> <oorie> <arfie> <acfie>
      int a, b, c, d; in >> a >> b >> c >> d;
      out << (int)fm::mpr121_autoconfig1(a != 0, b != 0, c != 0, d != 0);
    } else if (cmd == "mprregs") {
      out << (int)fm::MPR121_REG_ECR << ' ' << (int)fm::MPR121_REG_AUTOCONFIG0 << ' '
          << (int)fm::MPR121_REG_AUTOCONFIG1 << ' ' << (int)fm::MPR121_REG_UPLIMIT << ' '
          << (int)fm::MPR121_REG_LOWLIMIT << ' ' << (int)fm::MPR121_REG_TARGETLIMIT << ' ' << fm::MPR121_VDD_MV;
    } else if (cmd == "mprconsts") {
      out << (int)fm::MPR121_REG_FILTDATA_0 << ' ' << (int)fm::MPR121_REG_BASELINE_0 << ' '
          << (int)fm::MPR121_FILT_BYTES << ' ' << (int)fm::MPR121_BASE_BYTES;
    } else if (cmd == "notes") {                 // notes P<pad>:<note> R<pad> U<pad>:<v> A ...
      struct Rec { std::ostringstream* o; bool first = true;
        void put(const char* w, int n, int v) { *o << (first ? "" : " ") << w << ':' << n; if (v >= 0) *o << ':' << v; first = false; }
        void noteOn(uint8_t n) { put("ON", n, -1); }
        void noteOff(uint8_t n) { put("OFF", n, -1); }
        void pressure(uint8_t n, uint8_t v) { put("AT", n, v); } } rec; rec.o = &out;
      fm::PadNotes<24> pn; pn.reset(); std::string tok;
      while (in >> tok) {
        char op = tok[0]; size_t c = tok.find(':');
        int a = std::atoi(tok.substr(1, c == std::string::npos ? std::string::npos : c - 1).c_str());
        int b = c == std::string::npos ? 0 : std::atoi(tok.substr(c + 1).c_str());
        if (op == 'P') pn.press((uint8_t)a, (uint8_t)b, rec);
        else if (op == 'R') pn.release((uint8_t)a, rec);
        else if (op == 'U') pn.update_pressure((uint8_t)a, (uint8_t)b, rec);
        else if (op == 'A') for (uint8_t p = 0; p < 24; p++) pn.release(p, rec);
      }
      if (rec.first) out << "none";
    } else if (cmd == "touchbits") {             // touchbits <lsb> <msb>
      unsigned a, b; in >> a >> b; uint8_t st[2] = {(uint8_t)a, (uint8_t)b};
      out << fm::mpr121_touch_bits(st);
    } else if (cmd == "hreport") {               // hreport <1|0>...: started OK, then reports -> lost flags
      fm::SensorHealth h; h.started(true, 0, 0x8C); int v; bool first = true;
      while (in >> v) { out << (first ? "" : " ") << (h.report(v != 0) ? 1 : 0); first = false; }
    } else if (cmd == "healthconsts") {
      out << (int)fm::SENSOR_FAIL_LIMIT << ' ' << fm::SENSOR_CHECK_MS << ' ' << fm::SENSOR_RETRY_MS;
    } else if (cmd == "healthsim") {
      // healthsim <T> <fail_from> <fail_to> <reset_at>: one sensor, pad 0 held all the time,
      // 1 ms loop mirroring loop(): retry_due -> start; status read -> report; ECR check;
      // pad_step; LED error flag. Failing-bus stub: every transaction fails in
      // [fail_from, fail_to); at reset_at the chip resets (ECR reads 0, still ACKs).
      long T, ff, ft, ra; in >> T >> ff >> ft >> ra;
      fm::SensorHealth h; fm::PadNotes<12> pn; pn.reset();
      struct Rec { std::ostringstream* o; uint32_t t = 0; bool first = true;
        void put(const char* w) { *o << (first ? "" : " ") << t << ':' << w; first = false; }
        void noteOn(uint8_t) { put("ON"); } void noteOff(uint8_t) { put("OFF"); }
        void pressure(uint8_t, uint8_t) {} } rec; rec.o = &out;
      uint8_t chipEcr = 0; uint32_t lastChange = 0; bool err = false;
      auto bus = [&](uint32_t t) { return !(t >= (uint32_t)ff && t < (uint32_t)ft); };
      auto start = [&](uint32_t t) {
        bool ok = bus(t); if (ok) chipEcr = 0x8C;
        h.started(ok, t, chipEcr); rec.put(ok ? "START_OK" : "START_FAIL");
      };
      rec.t = 0; start(0);
      for (uint32_t t = 1; t < (uint32_t)T; t++) {
        rec.t = t;
        if ((long)t == ra) chipEcr = 0;
        if (h.retry_due(t)) start(t);
        if (h.ok) {
          bool rd = bus(t);
          if (h.report(rd)) { rec.put("LOST"); pn.release(0, rec); }
          else if (rd) {
            bool lost = false;
            if (h.check_due(t) && h.report_check(bus(t), chipEcr)) { rec.put("LOST"); pn.release(0, rec); lost = true; }
            if (!lost) {
              fm::PadAction a = fm::pad_step(chipEcr != 0, pn.sounding(0), t, lastChange, 15);
              if (a == fm::PadAction::Press) pn.press(0, 60, rec);
              else if (a == fm::PadAction::Release) pn.release(0, rec);
            }
          }
        }
        if (err != !h.ok) { err = !h.ok; rec.put(err ? "LED_ERR" : "LED_OK"); }
      }
    } else if (cmd == "blinkconsts") {
      out << (int)fm::BLINK_READY_TIMES << ' ' << fm::BLINK_READY_MS << ' ' << (int)fm::BLINK_RECAL_TIMES
          << ' ' << fm::BLINK_RECAL_MS << ' ' << fm::BLINK_SCALE_MS;
    } else if (cmd == "consts") {
      out << fm::BUTTON_SAMPLE_MS << ' ' << fm::BUTTON_LONG_MS << ' ' << fm::POT_READ_MS << ' '
          << (int)fm::AT_MIN_CHANGE << ' ' << (int)fm::CIN_NOTE_ON << ' ' << (int)fm::CIN_NOTE_OFF << ' '
          << (int)fm::CIN_POLY_PRESSURE;
    } else {
      out << "ERR unknown command: " << cmd;
    }
    std::cout << out.str() << std::endl;   // flush: the test keeps one probe process open
  }
  return 0;
}
