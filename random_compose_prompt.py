#!/usr/bin/env python3
import argparse
import json
import random
import re
import sys
from pathlib import Path

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


def parse_fragments(value: str):
    """Parse -fragments like: 1,3,5"""
    if not value:
        raise ValueError("-fragments cannot be empty")

    result = []
    seen = set()
    for chunk in value.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            n = int(chunk)
        except ValueError:
            raise ValueError(f"Invalid fragment number: {chunk}")
        if n not in CATEGORY_MAP:
            raise ValueError(f"Fragment number out of range: {n} (must be 1-8)")
        if n not in seen:
            result.append(n)
            seen.add(n)

    if not result:
        raise ValueError("No valid fragment numbers found in -fragments")
    return result


def parse_range_spec(value: str):
    """
    Parse -range like: 1:[3-6],3:[3-4]
    Meaning:
      category 1 => only choose from entries 3..6 (1-based, inclusive)
      category 3 => only choose from entries 3..4 (1-based, inclusive)
    """
    if not value:
        return {}

    specs = {}
    matches = re.findall(r'(\d+)\s*:\s*\[(\d+)\s*-\s*(\d+)\]', value)
    if not matches:
        raise ValueError(
            "Invalid -range format. Example: 1:[3-6],3:[3-4]"
        )

    # Validate that the whole string is composed only of valid specs joined by commas.
    cleaned = re.sub(r'\s+', '', value)
    rebuilt = ','.join(f'{a}:[{b}-{c}]' for a, b, c in matches)
    if cleaned != rebuilt:
        raise ValueError(
            "Invalid -range format. Example: 1:[3-6],3:[3-4]"
        )

    for cat_s, start_s, end_s in matches:
        cat = int(cat_s)
        start = int(start_s)
        end = int(end_s)

        if cat not in CATEGORY_MAP:
            raise ValueError(f"Range category out of range: {cat} (must be 1-8)")
        if start < 1 or end < 1:
            raise ValueError(f"Range indices must be >= 1: {cat}:[{start}-{end}]")
        if start > end:
            raise ValueError(f"Range start > end: {cat}:[{start}-{end}]")

        specs[cat] = (start, end)

    return specs


def load_categories(json_path: Path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def pick_from_category(data, cat_num, range_specs):
    cat_name = CATEGORY_MAP[cat_num]
    entries = data[cat_name]

    if cat_num in range_specs:
        start, end = range_specs[cat_num]
        if end > len(entries):
            raise ValueError(
                f"Range {cat_num}:[{start}-{end}] exceeds category '{cat_name}' size ({len(entries)})"
            )
        # Convert 1-based inclusive to Python slice.
        pool = entries[start - 1:end]
    else:
        pool = entries

    if not pool:
        raise ValueError(f"No entries available for category {cat_num} ({cat_name})")

    return random.choice(pool)


def main():
    parser = argparse.ArgumentParser(
        description="Compose a random prompt from selected fragment categories."
    )
    parser.add_argument(
        '-fragments',
        required=True,
        help='Comma-separated category numbers, e.g. 1,3,5'
    )
    parser.add_argument(
        '-range',
        dest='range_spec',
        default='',
        help='Optional range restriction, e.g. 1:[3-6],3:[3-4]'
    )
    parser.add_argument(
        '-json',
        default='/mnt/data/camera_pose_categories_v2.json',
        help='Path to the category JSON file'
    )
    parser.add_argument(
        '-seed',
        type=int,
        default=None,
        help='Optional random seed'
    )
    parser.add_argument(
        '--show-indices',
        action='store_true',
        help='Show selected category numbers and names before the final prompt'
    )

    args = parser.parse_args()

    try:
        fragment_nums = parse_fragments(args.fragments)
        range_specs = parse_range_spec(args.range_spec)
        data = load_categories(Path(args.json))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.seed is not None:
        random.seed(args.seed)

    chosen = []
    try:
        for cat_num in fragment_nums:
            value = pick_from_category(data, cat_num, range_specs)
            chosen.append((cat_num, CATEGORY_MAP[cat_num], value))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.show_indices:
        for cat_num, cat_name, value in chosen:
            print(f"[{cat_num}] {cat_name}: {value}")
        print()

    prompt = ', '.join(value for _, _, value in chosen)
    print(prompt)


if __name__ == '__main__':
    main()
