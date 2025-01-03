import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from PIL import Image
from typing import Dict


def get_prompt(
        meanings: str,
) -> str:
    return f"a kanji character with black strokes on a white background, with the following meanings: {meanings}"


def save_jpeg(
        jpeg_dir: str,
        kanji_char: str,
        svg: str,
):
    temp_svg_path = os.path.join(jpeg_dir, "temp.svg")
    with open(temp_svg_path, "w", encoding="utf-8") as f:
        f.write(svg)

    temp_png_path = os.path.join(jpeg_dir, f"{kanji_char}.png")
    subprocess.run(["rsvg-convert", "-o", temp_png_path, temp_svg_path], check=True)

    jpeg_path = temp_png_path.replace(".png", ".jpeg")
    with Image.open(temp_png_path) as img:
        with Image.new("RGB", img.size, "WHITE") as background:
            background.paste(img, (0, 0), img)
            background.save(jpeg_path, "JPEG")

    os.remove(temp_svg_path)
    os.remove(temp_png_path)


def get_kanji_char_to_svg(
        data_dir: str,
) -> Dict[str, str]:
    kanji_char_to_svg = {}

    ET.register_namespace("kvg", "http://kanjivg.tagaini.net")
    kanjivg_path = os.path.join(data_dir, "kanjivg-20220427.xml")
    tree = ET.parse(kanjivg_path)
    root = tree.getroot()

    for kanji in root.findall(".//kanji"):
        top_group = kanji.find("./g")
        kanji_char = top_group.get("{http://kanjivg.tagaini.net}element")
        if kanji_char is None:
            continue

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">\n'
            '  <g style="fill:none;stroke:#000000">\n'
        )
        svg += ET.tostring(top_group, encoding="unicode")
        svg += "  </g>\n</svg>"

        kanji_char_to_svg[kanji_char] = svg
    return kanji_char_to_svg


def main(args):
    jpeg_dir = os.path.join(args.data_dir, "train")
    shutil.rmtree(jpeg_dir, ignore_errors=True)
    os.makedirs(jpeg_dir)

    kanji_char_to_svg = get_kanji_char_to_svg(args.data_dir)

    kanjidic_path = os.path.join(args.data_dir, "kanjidic2.xml")
    tree = ET.parse(kanjidic_path)
    root = tree.getroot()

    list_of_filename_to_text = []
    for character in root.findall("character"):
        kanji_char = character.find("literal")
        if kanji_char is None:
            continue

        kanji_char = kanji_char.text
        if kanji_char not in kanji_char_to_svg:
            continue

        meanings = [m for m in character.findall(".//meaning") if "m_lang" not in m.attrib]
        if len(meanings) == 0:
            continue

        meanings = [meaning.text for meaning in meanings]
        meanings = ", ".join(meanings)

        save_jpeg(jpeg_dir, kanji_char, kanji_char_to_svg[kanji_char])
        list_of_filename_to_text.append(
            {
                "file_name": f"{kanji_char}.jpeg",
                "text": get_prompt(meanings),
            }
        )

    metadata_path = os.path.join(args.data_dir, "train", "metadata.jsonl")
    with open(metadata_path, "w") as f:
        for item in list_of_filename_to_text:
            json_line = json.dumps(item)
            f.write(json_line + "\n")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True)
    args = parser.parse_args()
    main(args)