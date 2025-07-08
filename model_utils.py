import torch
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.auto.modeling_auto import AutoModelForCausalLM, AutoModelForSeq2SeqLM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# GPT-2 (as a general foundation model alternative)
ds_tokenizer = AutoTokenizer.from_pretrained("gpt2")
ds_model = AutoModelForCausalLM.from_pretrained("gpt2").to(device)

# BioGPT (using a smaller biomedical model alternative)
bio_tokenizer = AutoTokenizer.from_pretrained("gpt2")
bio_model = AutoModelForCausalLM.from_pretrained("gpt2").to(device)

# Legal-BERT (Proxy with FLAN-T5)
legal_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
legal_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base").to(device)

def generate_response(model_name, prompt):
    if model_name == "DeepSeek-R1":
        input_ids = ds_tokenizer.encode(prompt, return_tensors="pt").to(device)
        output = ds_model.generate(input_ids, max_length=150, do_sample=True, temperature=0.8, pad_token_id=ds_tokenizer.eos_token_id)
        return ds_tokenizer.decode(output[0], skip_special_tokens=True)

    elif model_name == "BioGPT":
        # Add biomedical context to the prompt
        bio_prompt = f"As a medical AI assistant, please provide information about: {prompt}"
        input_ids = bio_tokenizer.encode(bio_prompt, return_tensors="pt").to(device)
        output = bio_model.generate(input_ids, max_length=150, do_sample=True, temperature=0.8)
        return bio_tokenizer.decode(output[0], skip_special_tokens=True)

    elif model_name == "Legal-BERT":
        formatted = "summarize: " + prompt
        input_ids = legal_tokenizer.encode(formatted, return_tensors="pt").to(device)
        output = legal_model.generate(input_ids, max_length=150, do_sample=True, temperature=0.8)
        return legal_tokenizer.decode(output[0], skip_special_tokens=True)
    
    else:
        return "Invalid model selected."
