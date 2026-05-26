from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

try:
    from ai.training.prepare_dataset import DEFAULT_SYSTEM_PROMPT, build_chat_example, load_records
except ModuleNotFoundError:
    from prepare_dataset import DEFAULT_SYSTEM_PROMPT, build_chat_example, load_records


DEFAULT_OUTPUT_DIR = Path("ai/output/smartcito-lora")
DEFAULT_TARGET_MODULES = "q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj"


def _default_base_model() -> str:
    return os.getenv("SMARTCITO_BASE_MODEL_ID", "")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fine-tune SmartCito adapters with LoRA.")
    parser.add_argument("--dataset", default="ai/datasets/sample_training_data.json")
    parser.add_argument("--base-model", default=_default_base_model())
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-strategy", default="epoch")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", default=DEFAULT_TARGET_MODULES)
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser


def _resolve_base_model_id(args: argparse.Namespace) -> str:
    base_model = str(args.base_model or "").strip()
    if base_model:
        return base_model
    raise RuntimeError(
        "A base model id is required. Set SMARTCITO_BASE_MODEL_ID or pass --base-model with a compatible model from an official provider source."
    )


def _torch_dtype(args) -> Any:
    import torch

    if args.bf16:
        return torch.bfloat16
    return torch.float16


def _load_dependencies(load_in_4bit: bool):
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        raise RuntimeError(
            "Training requires torch, datasets, transformers, peft, and trl. Install ai_models/requirements.txt first."
        ) from exc

    bits_and_bytes_config = None
    if load_in_4bit:
        try:
            from transformers import BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError(
                "QLoRA requires BitsAndBytesConfig support from transformers."
            ) from exc
        bits_and_bytes_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

    return {
        "torch": torch,
        "Dataset": Dataset,
        "LoraConfig": LoraConfig,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoTokenizer": AutoTokenizer,
        "TrainingArguments": TrainingArguments,
        "SFTTrainer": SFTTrainer,
        "BitsAndBytesConfig": bits_and_bytes_config,
    }


def run_training(args: argparse.Namespace, *, load_in_4bit: bool = False) -> dict[str, Any]:
    deps = _load_dependencies(load_in_4bit)
    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN") or os.getenv("HF_TOKEN")
    base_model_id = _resolve_base_model_id(args)

    records = load_records(args.dataset)
    prepared_examples = [build_chat_example(record, system_prompt=args.system_prompt) for record in records]
    train_dataset = deps["Dataset"].from_list(prepared_examples)

    tokenizer = deps["AutoTokenizer"].from_pretrained(base_model_id, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = deps["AutoModelForCausalLM"].from_pretrained(
        base_model_id,
        token=hf_token,
        device_map=args.device_map,
        torch_dtype=_torch_dtype(args),
        quantization_config=deps["BitsAndBytesConfig"],
    )
    model.config.use_cache = False

    peft_config = deps["LoraConfig"](
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[item.strip() for item in args.target_modules.split(",") if item.strip()],
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = deps["TrainingArguments"](
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        logging_steps=args.logging_steps,
        save_strategy=args.save_strategy,
        report_to="none",
        remove_unused_columns=False,
        bf16=bool(args.bf16),
        fp16=bool(args.fp16),
    )

    trainer = deps["SFTTrainer"](
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
    )
    train_result = trainer.train()

    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    summary = {
        "model_name": "SmartCito Model",
        "base_model": base_model_id,
        "training_mode": "qlora" if load_in_4bit else "lora",
        "records": len(prepared_examples),
        "output_dir": str(output_dir),
        "adapter_only_export": True,
        "final_loss": getattr(train_result, "training_loss", None),
    }
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    args = build_arg_parser().parse_args()
    summary = run_training(args, load_in_4bit=False)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())