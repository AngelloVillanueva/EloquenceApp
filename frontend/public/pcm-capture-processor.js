/**
 * AudioWorklet: forwards Float32 mono frames to the main thread.
 * Downsampling + PCM16 conversion happens in the main thread (hooks).
 */
class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0]
    if (input && input[0] && input[0].length > 0) {
      // Copy — AudioWorklet recycles buffers
      this.port.postMessage(input[0].slice(0))
    }
    return true
  }
}

registerProcessor('pcm-capture-processor', PcmCaptureProcessor)
