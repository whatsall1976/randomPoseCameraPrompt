#!/usr/bin/env python3
"""
promptGen.py

通用版：CSV 中每一列都支持作为检索条件。

用法：
    python promptGen.py -target captions.csv \
        -AspectRatio 2:3 \
        -EmotionalScore 0.5-0.65 \
        -Clothing blanket,boots \
        -Feature partial \
        -ArtisticQuality 0.4-0.6

规则（按列的数据类型自动判断）：
  1. 列表列（单元格形如 ['a', 'b']）：传入逗号分隔的标签，要求全部包含。
     例：-Clothing blanket,boots
  2. 数值列 + 值形如 "下限-上限"：按闭区间匹配（含边界）。
     例：-EmotionalScore 0.5-0.65
  3. 其他情况：精确字符串匹配。
     例：-AspectRatio 2:3  /  -Feature partial

列名匹配时忽略空格和大小写，因此 "Aspect Ratio" 列可用 -AspectRatio。
"""

import argparse
import ast
import csv
import random
import re
import sys


# ---------- 列名规范化 ----------

def normalize_column_name(name):
    """去掉空格、下划线、连字符，转小写，用于命令行参数与列名匹配。"""
    return re.sub(r"[\s_\-]+", "", name).lower()


def build_column_map(fieldnames):
    """返回 {规范化列名: 原始列名}。"""
    mapping = {}
    for name in fieldnames:
        key = normalize_column_name(name)
        if key:
            mapping[key] = name
    return mapping


# ---------- 列类型推断 ----------

def is_list_cell(cell):
    cell = (cell or "").strip()
    return cell.startswith("[") and cell.endswith("]")


def is_numeric_cell(cell):
    try:
        float((cell or "").strip())
        return True
    except (ValueError, TypeError):
        return False


def infer_column_types(rows, fieldnames):
    """
    推断每列类型：'list' / 'numeric' / 'text'。
    只要有一个非空样本是列表字面量就判为 list；
    否则只要大部分非空样本可转 float 就判为 numeric；
    其余为 text。
    """
    col_types = {}
    for col in fieldnames:
        samples = [(r.get(col) or "").strip() for r in rows]
        samples = [s for s in samples if s]
        if not samples:
            col_types[col] = "text"
            continue
        if any(is_list_cell(s) for s in samples):
            col_types[col] = "list"
            continue
        numeric_count = sum(1 for s in samples if is_numeric_cell(s))
        if numeric_count / len(samples) >= 0.8:
            col_types[col] = "numeric"
        else:
            col_types[col] = "text"
    return col_types


# ---------- 值解析 ----------

RANGE_PATTERN = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*$")


def parse_range(value):
    """若值形如 '0.5-0.65' 返回 (low, high)，否则返回 None。"""
    m = RANGE_PATTERN.match(value)
    if not m:
        return None
    low, high = float(m.group(1)), float(m.group(2))
    if low > high:
        raise ValueError(f"区间下限不能大于上限: {value!r}")
    return low, high


def parse_list_cell(cell):
    """解析列表列单元格，兼容 ['a','b'] 与逗号分隔文本。"""
    cell = (cell or "").strip()
    if not cell:
        return []
    if cell.startswith("[") and cell.endswith("]"):
        try:
            value = ast.literal_eval(cell)
            if isinstance(value, list):
                return [str(item).strip() for item in value]
        except (ValueError, SyntaxError):
            pass
    return [item.strip().strip("'\"") for item in cell.split(",") if item.strip()]


# ---------- 单行匹配 ----------

def row_matches(row, col_name, col_type, raw_value):
    """判断单行是否满足某列的过滤条件。"""
    cell = (row.get(col_name) or "").strip()

    # 列表列：要求传入的所有标签都在该单元格列表中
    if col_type == "list":
        required = [t.strip() for t in raw_value.split(",") if t.strip()]
        actual = parse_list_cell(cell)
        return all(tag in actual for tag in required)

    # 数值列：若传入值是区间则闭区间匹配，否则按精确数值匹配
    if col_type == "numeric":
        rng = parse_range(raw_value)
        if rng is not None:
            if not cell:
                return False
            try:
                num = float(cell)
            except ValueError:
                return False
            low, high = rng
            return low <= num <= high
        # 非区间：精确数值比较
        if not cell:
            return False
        try:
            return float(cell) == float(raw_value.strip())
        except ValueError:
            return cell == raw_value.strip()

    # 文本列：精确字符串匹配
    return cell == raw_value.strip()


# ---------- 主流程 ----------

def parse_args():
    parser = argparse.ArgumentParser(
        description="按任意列条件从 CSV 中随机抽取一条 Caption。",
        add_help=True,
    )
    parser.add_argument("-target", required=True, help="目标 CSV 文件路径")
    # 其余参数通过 parse_known_args 动态捕获
    args, extra = parser.parse_known_args()
    return args, extra


def parse_extra_filters(extra, column_map):
    """
    把未知参数解析成 [(原始列名, 原始值), ...]。
    支持 -Key value 和 --Key value 两种形式。
    """
    filters = []
    i = 0
    while i < len(extra):
        token = extra[i]
        if not token.startswith("-"):
            raise ValueError(f"意外的参数: {token!r}（期望 -列名 值）")
        key = token.lstrip("-")
        if i + 1 >= len(extra) or extra[i + 1].startswith("-"):
            raise ValueError(f"参数 -{key} 缺少对应的值")
        value = extra[i + 1]
        i += 2

        norm = normalize_column_name(key)
        if norm not in column_map:
            available = ", ".join(sorted(column_map.keys()))
            raise ValueError(
                f"未知列: {key!r}（规范化后 {norm!r}）。\n可用列（忽略空格大小写）: {available}"
            )
        filters.append((column_map[norm], value))
    return filters


def main():
    args, extra = parse_args()

    # 读取 CSV
    try:
        with open(args.target, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.target!r}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("CSV 中没有数据行。", file=sys.stderr)
        sys.exit(2)

    column_map = build_column_map(fieldnames)
    col_types = infer_column_types(rows, fieldnames)

    # 解析动态过滤条件
    try:
        filters = parse_extra_filters(extra, column_map)
    except ValueError as e:
        print(f"参数错误：{e}", file=sys.stderr)
        sys.exit(1)

    # 逐行过滤
    matched = []
    for row in rows:
        ok = True
        for col_name, raw_value in filters:
            if not row_matches(row, col_name, col_types.get(col_name, "text"), raw_value):
                ok = False
                break
        if ok:
            matched.append(row)

    if not matched:
        print("没有找到满足条件的条目。", file=sys.stderr)
        sys.exit(3)

    chosen = random.choice(matched)
    caption = (chosen.get("Caption") or "").strip()
    print(caption)


if __name__ == "__main__":
    main()
#（注：内容由AI生成）
