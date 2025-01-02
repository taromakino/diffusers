import os
import torch
from argparse import ArgumentParser
from diffusers import StableDiffusionPipeline
from .prepare_kanji_dataset import get_prompt


def main(args):
    os.makedirs(args.out_dir, exist_ok=True)
    pipe = StableDiffusionPipeline.from_pretrained(args.model_dir, torch_dtype=torch.float16)
    pipe.to("cuda")
    for meaning in args.meanings:
        image = pipe(prompt=get_prompt(meaning)).images[0]
        image.save(os.path.join(args.out_dir, f"{meaning}.png"))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--model_dir", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--meanings", nargs='+', type=str)
    main(parser.parse_args())