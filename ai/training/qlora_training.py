from __future__ import annotations

import json

try:
    from ai.training.lora_training import build_arg_parser, run_training
except ModuleNotFoundError:
    from lora_training import build_arg_parser, run_training


def build_qlora_arg_parser():
    parser = build_arg_parser()
    parser.description = "Fine-tune Orca adapters with QLoRA."
    parser.set_defaults(output_dir="ai/output/orca-lora")
    parser.set_defaults(fp16=True)
    return parser


def main() -> int:
    parser = build_qlora_arg_parser()
    args = parser.parse_args()
    summary = run_training(args, load_in_4bit=True)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())