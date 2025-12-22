from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


class NMTBase:
    """
    NMT BASE – OPUS / MarianMT
    Ổn định trên Windows + Raspberry Pi
    """

    def __init__(self, model_dir: str):
        self.device = torch.device("cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_dir,
            use_fast=False,
        )

        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_dir,
            torch_dtype=torch.float32,
        )

        self.model.to(self.device)
        self.model.eval()

    def translate(self, text: str) -> str:
        if not text:
            return ""

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                num_beams=4,
                max_length=256,
                early_stopping=True,
                no_repeat_ngram_size=2,
            )

        return self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()
