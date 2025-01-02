import json
import os
import subprocess
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path
from typing import List


def get_paths_from_kanji(
        kanji: ET.Element
) -> List[str]:
    paths = []
    for path in kanji.findall(".//path"):
        d = path.get("d")
        if d:
            paths.append(d)
    return paths


def get_svg(paths: List[str]) -> str:
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g stroke="black" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        {chr(10).join(f'        <path d="{path}"/>' for path in paths)}
    </g>
</svg>'''
    return svg


def save_images(
        data_dir: Path
) -> None:
    kanjivg_path = os.path.join(data_dir, "kanjivg-20220427.xml")
    tree = ET.parse(kanjivg_path)
    root = tree.getroot()

    images_dir = os.path.join(data_dir, "train")
    os.makedirs(images_dir)

    for kanji in root.findall(".//kanji"):
        kanji_id = kanji.get("id", "").replace("kvg:kanji_", "")
        if not kanji_id:
            continue

        paths = get_paths_from_kanji(kanji)
        if not paths:
            continue

        svg = get_svg(paths)
        temp_svg_path = os.path.join(images_dir, "temp.svg")
        with open(temp_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)

        image_path = os.path.join(images_dir, f"{kanji_id}.png")
        subprocess.run(['rsvg-convert', '-o', image_path, temp_svg_path], check=True)
        os.remove(temp_svg_path)


def save_metadata(
        data_dir: Path,
):
    kanjidic_path = os.path.join(data_dir, "kanjidic2.xml")
    tree = ET.parse(kanjidic_path)
    root = tree.getroot()

    list_of_dicts = []
    for character in root.findall("character"):
        kanji_id = character.find('.//cp_value[@cp_type="ucs"]')
        meaning = character.find(".//meaning")
        if kanji_id is not None and meaning is not None:
            image_path = os.path.join(data_dir, "train", f"{kanji_id.text.zfill(5)}.png")
            if os.path.exists(image_path):
                list_of_dicts.append(
                    {
                        "file_name": image_path,
                        "text": meaning.text,
                    }
                )

    metadata_path = os.path.join(data_dir, "train", "metadata.jsonl")
    with open(metadata_path, "w") as f:
        for item in list_of_dicts:
            json_line = json.dumps(item)
            f.write(json_line + "\n")


def main(args):
    save_images(args.data_dir)
    save_metadata(args.data_dir)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True)
    args = parser.parse_args()
    main(args)