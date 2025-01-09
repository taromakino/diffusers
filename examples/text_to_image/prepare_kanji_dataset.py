import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from PIL import Image
from typing import Dict, Tuple


KANJI_ID_LEN = 5


def get_prompt(meanings: str) -> str:
    """
    meanings is a comma-delimited list of English meanings.
    """
    return f"a kanji character with black strokes on a white background, with the following meanings: {meanings}"


def save_jpeg(
        jpeg_dir: str,
        kanji_id: str,
        svg: str,
) -> None:
    """
    Save the image in jpeg format, explicitly rendering the image with a white background.
    """
    temp_svg_path = os.path.join(jpeg_dir, "temp.svg")
    with open(temp_svg_path, "w", encoding="utf-8") as f:
        f.write(svg)

    temp_png_path = os.path.join(jpeg_dir, f"{kanji_id}.png")
    subprocess.run(["rsvg-convert", "-o", temp_png_path, temp_svg_path], check=True)

    jpeg_path = temp_png_path.replace(".png", ".jpeg")
    with Image.open(temp_png_path) as img:
        with Image.new("RGB", img.size, "WHITE") as background:
            background.paste(img, (0, 0), img)
            background.save(jpeg_path, "JPEG")

    os.remove(temp_svg_path)
    os.remove(temp_png_path)


def get_kanji_dicts(
        data_dir: str,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Reads the kanjivg-20220427 file and creates two dictionaries mapping each unicode kanji character to the svg string
    and kanji id.
    """
    kanji_char_to_id = {}
    kanji_char_to_svg = {}

    ET.register_namespace("kvg", "http://kanjivg.tagaini.net")
    kanjivg_path = os.path.join(data_dir, "kanjivg-20220427.xml")
    tree = ET.parse(kanjivg_path)
    root = tree.getroot()

    # Iterate through each kanji
    for kanji in root.findall(".//kanji"):
        # The top group represents the entire character. Skip those that do not have a unicode kanji character.
        top_group = kanji.find("./g")
        kanji_char = top_group.get("{http://kanjivg.tagaini.net}element")
        if kanji_char is None:
            continue

        # Each kanji has five digit id that will be used as the filename
        kanji_id = kanji.get("id").replace("kvg:kanji_", "")
        assert len(kanji_id) == KANJI_ID_LEN
        kanji_char_to_id[kanji_char] = kanji_id

        # Wrap the content of the top group with tags specifying the svg representation style
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 109 109">\n'
            '  <g transform="translate(2,2)" style="fill:none;stroke:#000000;stroke-width:3;stroke-linecap:round;stroke-linejoin:round">\n'
        )

        svg += ET.tostring(top_group, encoding="unicode")
        svg += "  </g>\n</svg>"

        kanji_char_to_svg[kanji_char] = svg

    return kanji_char_to_id, kanji_char_to_svg


def main(args: argparse.Namespace) -> None:
    jpeg_dir = os.path.join(args.data_dir, "train")
    shutil.rmtree(jpeg_dir, ignore_errors=True)
    os.makedirs(jpeg_dir)

    kanji_char_to_id, kanji_char_to_svg = get_kanji_dicts(args.data_dir)

    kanjidic_path = os.path.join(args.data_dir, "kanjidic2.xml")
    tree = ET.parse(kanjidic_path)
    root = tree.getroot()

    # This is used to construct the metadata file.
    list_of_filename_to_text = []

    # Iterate through each kanji
    for character in root.findall("character"):
        # Skip kanji that do not have a unicode character
        kanji_char = character.find("literal")
        if kanji_char is None:
            continue

        # Skip kanji that do not have a corresponding svg
        kanji_char = kanji_char.text
        if kanji_char not in kanji_char_to_svg:
            continue

        # Get the list of English meanings
        meanings = [m for m in character.findall(".//meaning") if "m_lang" not in m.attrib]
        if len(meanings) == 0:
            continue

        meanings = [meaning.text for meaning in meanings]
        meanings = ", ".join(meanings)

        kanji_id = kanji_char_to_id[kanji_char]
        save_jpeg(jpeg_dir, kanji_id, kanji_char_to_svg[kanji_char])

        # Populate the metadata entry
        list_of_filename_to_text.append(
            {
                "file_name": f"{kanji_id}.jpeg",
                "text": get_prompt(meanings),
            }
        )

    # Write the metadata file
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