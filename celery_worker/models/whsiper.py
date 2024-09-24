import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from celery_worker.variables import variables


class WhisperModelProcessor:

    def __init__(self):
        print("initialization whisper")
        # self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(self.device)
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            variables.whisper_model,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )

        self.model.to(self.device)
        self.processor = AutoProcessor.from_pretrained(variables.whisper_model)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=1,
            return_timestamps=True,
            torch_dtype=self.torch_dtype,
            device=self.device
        )
        print("initialization completed")