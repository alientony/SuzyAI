import torch
import os
import bitsandbytes as bnb
from datasets import Dataset
import transformers
from transformers import LlamaForCausalLM, LlamaTokenizer
from peft import (
    prepare_model_for_int8_training,
    LoraConfig,
    get_peft_model,
    get_peft_model_state_dict,
)

# Training parameters
MICRO_BATCH_SIZE = 2
BATCH_SIZE = 128
GRADIENT_ACCUMULATION_STEPS = BATCH_SIZE // MICRO_BATCH_SIZE
EPOCHS = 3
LEARNING_RATE = 3e-4
CUTOFF_LEN = 256
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
VAL_SET_SIZE = 200
TARGET_MODULES = [
    "q_proj",
    "v_proj",
]

# Load data from JSON
import json

DATA_PATH = "restructured_data.json"
with open(DATA_PATH, "r") as f:
    raw_data = json.load(f)

# Convert the raw data into a list of dictionaries
data_list = []
for entry in raw_data:
    input_text = entry["Input"]
    output_text = entry["Output"]
    data_list.append({"input": input_text, "output": output_text})

# Create a Dataset object from the list of dictionaries
data = Dataset.from_dict({"input": [d["input"] for d in data_list], "output": [d["output"] for d in data_list]})

# Change the checkpoint folder path to your local folder
CHECKPOINT_FOLDER = "./llama-2-7b-hf"

# Load the model and tokenizer
model = LlamaForCausalLM.from_pretrained(
    CHECKPOINT_FOLDER,
    load_in_8bit=True,
    device_map="auto",
)
tokenizer = LlamaTokenizer.from_pretrained(
    CHECKPOINT_FOLDER, add_eos_token=True
)

model = prepare_model_for_int8_training(model)

config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=TARGET_MODULES,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, config)
tokenizer.pad_token_id = 0

if len(data) < 2:
    raise ValueError("The dataset must have at least two samples to perform the train/test split.")

train_val = data.train_test_split(test_size=0.2, seed=42)

train_data = train_val["train"]
val_data = train_val["test"]

def format_example(example):
    input_text = example['input']
    output_text = example['output']
    return tokenizer(input_text, output_text, truncation=True, padding='max_length', max_length=CUTOFF_LEN)

train_data = train_data.map(format_example, batched=True)
val_data = val_data.map(format_example, batched=True)

trainer = transformers.Trainer(
    model=model,
    train_dataset=train_data,
    eval_dataset=val_data,
    args=transformers.TrainingArguments(
        per_device_train_batch_size=MICRO_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        warmup_steps=100,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=True,
        logging_steps=20,
        evaluation_strategy="steps",
        save_strategy="steps",
        eval_steps=200,
        save_steps=200,
        output_dir="lora-example-book",
        save_total_limit=3,
        load_best_model_at_end=True,
    ),
    data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
)
model.config.use_cache = False

old_state_dict = model.state_dict
model.state_dict = (
    lambda self, *_, **__: get_peft_model_state_dict(self, old_state_dict())
).__get__(model, type(model))

trainer.train()

model.save_pretrained("lora-example-book")

print("\n If there's a warning about missing keys above, please disregard :)")

