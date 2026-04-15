import argparse
import json
from pathlib import Path


def extract_channel_0_texts(data):
    paragraphs = data.get("results", {}).get("paragraphs", {}).get("paragraphs", [])
    texts = []

    for item in paragraphs:
        if item.get("channel") == 0:
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                sentences = item.get("sentences", [])
                if isinstance(sentences, list):
                    text = " ".join(
                        s.get("text", "").strip()
                        for s in sentences
                        if isinstance(s, dict) and isinstance(s.get("text"), str)
                    )

            if isinstance(text, str) and text.strip():
                texts.append(text.strip())

    return texts


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract one text per line from results.paragraphs.paragraphs where channel == 0"
        )
    )
    parser.add_argument("input_json", help="Path to input JSON file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output text file path (default: <input_name>_channel0.txt)",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_path = Path(args.output) if args.output else input_path.with_name(
        f"{input_path.stem}_channel0.txt"
    )

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    texts = extract_channel_0_texts(data)

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        for line in texts:
            f.write(line + "\n")

    print(f"Saved {len(texts)} lines to: {output_path}")


if __name__ == "__main__":
    main()
