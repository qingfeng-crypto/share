#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库布局校验脚本（防结构错配兜底）。

校验 `数学建模比赛完整学习知识/` 下各章是否均为标准结构：
    第X章 XXX/        (章目录)
        第Y节/        (节目录)
            *.md      (单篇内容，每节目录应恰好 1 个 md)

同时检查：
    - 不该出现在知识库根的平铺 .md（应归入某章/节）
    - 章节结构异常（章目录内直接放 md 而非节目录）

用法：
    python check_kb_layout.py
    python check_kb_layout.py --root <知识库绝对路径>

退出码：0=通过，1=发现异常。
"""
import os
import sys
import argparse


def is_chapter(name):
    """章目录：以「第」开头且含「章」"""
    return name.startswith("第") and "章" in name


def is_section(name):
    """节目录：以「第」开头且含「节」"""
    return name.startswith("第") and "节" in name


def check(root):
    errors = []
    if not os.path.isdir(root):
        print(f"[FAIL] 知识库目录不存在: {root}")
        return [f"missing root: {root}"]

    # 知识库根的合法元文件/目录（非「第X章」但属既有合法内容，允许平铺）
    ALLOWED_ROOT_FILES = {
        "学习路径总览.md",
        "积累足够之后如何对技能进行修改.md",
    }
    ALLOWED_ROOT_DIRS = {
        "02_优化模型",
        "12_常见错误与审查案例",
    }

    top_entries = sorted(os.listdir(root))
    chapters = [e for e in top_entries if is_chapter(e)]
    stray_md_at_root = [
        e for e in top_entries
        if e.lower().endswith(".md") and e not in ALLOWED_ROOT_FILES
    ]
    stray_other_at_root = [
        e for e in top_entries
        if not is_chapter(e)
        and not os.path.isdir(os.path.join(root, e))
        and e not in ALLOWED_ROOT_FILES
    ]
    stray_dir_at_root = [
        e for e in top_entries
        if not is_chapter(e)
        and os.path.isdir(os.path.join(root, e))
        and e not in ALLOWED_ROOT_DIRS
    ]
    if stray_dir_at_root:
        errors.append(
            "知识库根目录存在非「第X章」的目录（若属合法元目录请加入白名单）: "
            + ", ".join(stray_dir_at_root)
        )

    if stray_md_at_root:
        errors.append(
            "知识库根目录存在平铺 .md（应归入某章/节）: "
            + ", ".join(stray_md_at_root)
        )
    if stray_other_at_root:
        errors.append(
            "知识库根目录存在非章目录的条目: " + ", ".join(stray_other_at_root)
        )

    if not chapters:
        errors.append("未找到任何「第X章」目录")

    for ch in chapters:
        ch_path = os.path.join(root, ch)
        if not os.path.isdir(ch_path):
            errors.append(f"「{ch}」不是目录")
            continue
        sec_entries = sorted(os.listdir(ch_path))
        sections = [s for s in sec_entries if is_section(s)]
        md_direct_in_chapter = [s for s in sec_entries if s.lower().endswith(".md")]
        non_section_dirs = [
            s for s in sec_entries
            if not is_section(s) and os.path.isdir(os.path.join(ch_path, s))
        ]

        if md_direct_in_chapter:
            errors.append(
                f"章「{ch}」内直接放了 .md（应放进节目录）: "
                + ", ".join(md_direct_in_chapter)
            )
        if non_section_dirs:
            errors.append(
                f"章「{ch}」内存在非「第Y节」目录: "
                + ", ".join(non_section_dirs)
            )
        if not sections and not md_direct_in_chapter:
            errors.append(f"章「{ch}」内无任何节目录")

        for sec in sections:
            sec_path = os.path.join(ch_path, sec)
            if not os.path.isdir(sec_path):
                errors.append(f"「{ch}/{sec}」不是目录")
                continue
            md_files = [f for f in os.listdir(sec_path) if f.lower().endswith(".md")]
            if len(md_files) == 0:
                errors.append(f"节「{ch}/{sec}」内无 .md 文件")
            elif len(md_files) > 1:
                errors.append(
                    f"节「{ch}/{sec}」内有多个 .md（标准应为单篇）: "
                    + ", ".join(md_files)
                )

    return errors


def main():
    parser = argparse.ArgumentParser(description="知识库布局校验")
    # 脚本位于 <skill>/references/roles/编程手核心/scripts/
    # skill 根目录 = 向上 5 级
    skill_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    default_root = os.path.join(skill_root, "数学建模比赛完整学习知识")
    parser.add_argument("--root", default=default_root, help="知识库根目录")
    args = parser.parse_args()

    print(f"校验知识库: {args.root}")
    errors = check(args.root)
    if errors:
        print("\n[FAIL] 发现以下结构异常:")
        for e in errors:
            print("  - " + e)
        sys.exit(1)
    print("[OK] 所有章节结构符合「章/节/单md」规范")
    sys.exit(0)


if __name__ == "__main__":
    main()
