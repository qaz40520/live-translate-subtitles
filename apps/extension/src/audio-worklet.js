class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.pending = [];
    this.pendingSamples = 0;
    this.chunkSamples = Math.round(sampleRate * 0.8);
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (!channel) {
      return true;
    }

    this.pending.push(new Float32Array(channel));
    this.pendingSamples += channel.length;
    if (this.pendingSamples < this.chunkSamples) {
      return true;
    }

    const pcm = new Int16Array(this.pendingSamples);
    let offset = 0;
    for (const block of this.pending) {
      for (let index = 0; index < block.length; index += 1) {
        const sample = Math.max(-1, Math.min(1, block[index] ?? 0));
        pcm[offset] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        offset += 1;
      }
    }

    this.pending = [];
    this.pendingSamples = 0;
    this.port.postMessage(pcm.buffer, [pcm.buffer]);
    return true;
  }
}

registerProcessor("pcm-capture-processor", PcmCaptureProcessor);

