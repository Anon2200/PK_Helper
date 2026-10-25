import time, queue
import numpy as np
import sounddevice as sd

SR = 16000

def record_utterance(threshold, silence_sec, quit_event, max_sec=20, min_sec=0.4):
    """Ждёт речь, пишет до паузы. Возвращает (audio float32, t_start, t_end) или None."""
    q = queue.Queue()

    def cb(indata, frames, t, status):
        q.put(indata[:, 0].copy())

    pre, chunks = [], []
    started, t_start, last_voice = False, 0.0, 0.0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=1600, callback=cb):
        while not quit_event.is_set():
            try:
                block = q.get(timeout=0.2)
            except queue.Empty:
                continue
            now = time.time()
            rms = float(np.sqrt(np.mean(block ** 2)))
            if rms > threshold:
                last_voice = now
                if not started:
                    started, t_start = True, now
                    chunks = list(pre)
            if started:
                chunks.append(block)
                if now - last_voice > silence_sec or now - t_start > max_sec:
                    break
            else:
                pre.append(block)
                pre = pre[-3:]
    if not started or not chunks:
        return None
    audio = np.concatenate(chunks)
    if len(audio) / SR < min_sec:
        return None
    return audio, t_start, time.time()
