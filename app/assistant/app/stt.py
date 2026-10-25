class STT:
    def __init__(self, model_name, language=None):
        self.model_name = model_name
        self.language = language
        self.model = None

    def load(self):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(self.model_name, device="auto", compute_type="int8")

    def transcribe(self, audio):
        if self.model is None:
            self.load()
        segments, info = self.model.transcribe(audio, language=self.language, vad_filter=True, beam_size=1)
        return " ".join(s.text.strip() for s in segments).strip()
