from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_NAME = "microsoft/DialoGPT-medium"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    use_safetensors=False
)
model.eval()

def generate_reply_from_history(history: list[str], max_new_tokens=150):
    """
    history: list of utterances, no role prefixes
    """

    prompt = tokenizer.eos_token.join(history + [""])

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        padding=True,
        truncation=True
    )
    with torch.no_grad():
        output_ids = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.7,
            temperature=0.5
        )

    generated = output_ids[0, inputs["input_ids"].shape[-1]:]
    reply = tokenizer.decode(generated, skip_special_tokens=True)

    return reply.strip()
