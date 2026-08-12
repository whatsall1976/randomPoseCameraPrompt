#!/usr/bin/env python3

import argparse
import json
import random
import re
import sys
from pathlib import Path

VERSION = "2.0-fixed"

CATEGORY_MAP = {
    1: "distance",
    2: "camera_angle",
    3: "lens_focal_length",
    4: "framing",
    5: "overall_pose",
    6: "hand_arm_expression",
    7: "leg_pose",
    8: "head_pose",
}

DEFAULT_FRAGMENTS = "1,2,3,4,5,6,7,8"
DEFAULT_JSON = Path(__file__).with_name("camera_pose_categories_v2.json")


def parse_fragments(value: str):
    result = []
    seen = set()

    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue

        try:
            number = int(chunk)
        except ValueError:
            raise ValueError(f"Invalid fragment number: {chunk}")

        if number not in CATEGORY_MAP:
            raise ValueError(f"Fragment number must be 1-8: {number}")

        if number not in seen:
            result.append(number)
            seen.add(number)

    if not result:
        raise ValueError("No valid fragment categories were selected")

    return result


def parse_range_spec(value: str):
    if not value:
        return {}

    compact = re.sub(r"\s+", "", value)
    pattern = re.compile(r"(\d+):\[(\d+)-(\d+)\]")
    matches = pattern.findall(compact)

    if not matches:
        raise ValueError("Invalid -range syntax. Example: 1:[3-6],3:[3-4]")

    reconstructed = ",".join(
        f"{category}:[{start}-{end}]"
        for category, start, end in matches
    )

    if reconstructed != compact:
        raise ValueError("Invalid -range syntax. Example: 1:[3-6],3:[3-4]")

    ranges = {}

    for category_text, start_text, end_text in matches:
        category = int(category_text)
        start = int(start_text)
        end = int(end_text)

        if category not in CATEGORY_MAP:
            raise ValueError(f"Range category must be 1-8: {category}")
        if start < 1 or end < 1:
            raise ValueError("Range indices are 1-based and must be >= 1")
        if start > end:
            raise ValueError(
                f"Range start cannot exceed end: {category}:[{start}-{end}]"
            )

        ranges[category] = (start, end)

    return ranges


def load_data(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {path}\n"
            "Put camera_pose_categories_v2.json in the same directory as this script, "
            "or specify another file with -json PATH."
        )

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def choose_entry(data, category_number, ranges):
    category_name = CATEGORY_MAP[category_number]

    if category_name not in data:
        raise KeyError(f"Missing category in JSON: {category_name}")

    entries = data[category_name]

    if category_number in ranges:
        start, end = ranges[category_number]

        if end > len(entries):
            raise ValueError(
                f"{category_number}:[{start}-{end}] exceeds "
                f"'{category_name}' size ({len(entries)})"
            )

        # User-facing ranges are 1-based and inclusive.
        entries = entries[start - 1:end]

    return random.choice(entries)


def main():
    parser = argparse.ArgumentParser(
        description="Randomly combine camera/pose prompt fragments."
    )

    parser.add_argument(
        "-fragments",
        default=DEFAULT_FRAGMENTS,
        help=(
            "Comma-separated category numbers. "
            "Default: 1,2,3,4,5,6,7,8 (all categories). "
            "Example: -fragments 1,3,5"
        ),
    )

    parser.add_argument(
        "-range",
        dest="range_spec",
        default="",
        help=(
            "Restrict one or more categories to 1-based inclusive ranges. "
            "Example: -range '1:[3-6],3:[3-4]'"
        ),
    )

    parser.add_argument(
        "-json",
        type=Path,
        default=DEFAULT_JSON,
        help="Path to JSON fragment database. Default: camera_pose_categories_v2.json beside this script.",
    )

    parser.add_argument(
        "-seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible output.",
    )

    parser.add_argument(
        "--show-indices",
        action="store_true",
        help="Print each selected category and value before the final prompt.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    args = parser.parse_args()

    try:
        fragment_numbers = parse_fragments(args.fragments)
        ranges = parse_range_spec(args.range_spec)
        data = load_data(args.json)

        if args.seed is not None:
            random.seed(args.seed)

        selected = []
        for category_number in fragment_numbers:
            value = choose_entry(data, category_number, ranges)
            selected.append(
                (category_number, CATEGORY_MAP[category_number], value)
            )

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.show_indices:
        for number, name, value in selected:
            print(f"[{number}] {name}: {value}")
        print()

    print(", ".join(value for _, _, value in selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
