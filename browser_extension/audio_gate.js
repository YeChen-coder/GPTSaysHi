export class AudioGate {
  constructor(send) { this.send = send; this.preroll = []; this.speaking = false; this.trailing = 0; this.packets = 0; this.chunks = 0; this.maxRms = 0; }
  push(samples) {
    let squared = 0;
    const packet = new ArrayBuffer(8 + samples.length * 2), view = new DataView(packet);
    view.setFloat64(0, Date.now(), true);
    for (let i = 0; i < samples.length; i++) {
      const value = Math.max(-1, Math.min(1, samples[i]));
      squared += value * value;
      view.setInt16(8 + i * 2, Math.round(value < 0 ? value * 32768 : value * 32767), true);
    }
    const rms = Math.sqrt(squared / samples.length);
    this.chunks++; this.maxRms = Math.max(this.maxRms, rms);
    const audible = rms >= .001;
    const emit = data => { this.send(data); this.packets++; };
    if (audible) {
      if (!this.speaking) { this.preroll.forEach(emit); this.preroll = []; }
      this.speaking = true; this.trailing = 2; emit(packet);
    } else if (this.speaking && this.trailing > 0) { emit(packet); this.trailing--; }
    else { this.speaking = false; this.preroll.push(packet); if (this.preroll.length > 2) this.preroll.shift(); }
  }
}
