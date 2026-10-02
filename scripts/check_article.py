#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_article.py —— 「Youtube 转文章」成稿校验器（零依赖，仅用 Python 标准库）

用法：
    python check_article.py 成稿.md
    python check_article.py 成稿1.md 成稿2.md
    python check_article.py 目录/                  # 批量校验目录下所有 .md
    python check_article.py 成稿.md --strict       # 严格模式：任何一项不过即以非零码退出
    python check_article.py 成稿.md --allow OK,AI,API   # 追加允许保留的英文词
    python check_article.py 成稿.md --fix-spaces   # 顺手清掉中文字符之间的多余空格

检查项（对应 SKILL.md 的交付前自检）：
    [1] 首行是否带 skill 署名标记
    [2] 小标题是否被编号（「一、」「1.」等）—— 应无
    [3] 加粗 ** 是否闭合、是否满足 Obsidian flanking 连接性
    [4] 正文英文残留（已跳过代码块 / 行内 code / URL / 图片链接 / frontmatter）
    [5] 是否残留 Markdown 链接写法 [文字](url) —— 公众号渲染不了，应拆成代码块
    [6] 是否残留占位符（如「⬜ 我的笔记：」）
    [7] 文末是否有「原文/来源」信息块
    [8] 中文字符之间是否夹了多余空格（常见于批量替换英文后）
"""

import os
import re
import sys
import io
import argparse

# ---------------------------------------------------------------- 常量

# 视为「标点/引号」的字符：加粗标记内侧若紧贴这些字符，Obsidian 编辑模式会解析失败
PUNCT = set(
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "。，、；：？！“”‘’（）《》〈〉【】「」『』…—～·"
    "　・〈〉《》「」『』【】〔〕〖〗〘〙"
)

# 小标题编号的违规写法
HEADING_NUM_RE = re.compile(r'^(#{1,6})\s+(?:[0-9]+(?:\.[0-9]+)*\s*[.、)）]|[一二三四五六七八九十]+\s*[、.])')

# 默认允许保留的英文（极保守，只放几乎所有场景都该留的）
DEFAULT_ALLOW = {
    'YouTube', 'Google', 'iPhone', 'iPad', 'Mac', 'Windows', 'Linux',
    'Obsidian', 'Markdown', 'Twitter', 'Facebook', 'Instagram', 'LinkedIn',
    'TED', 'NASA', 'FBI', 'CIA',
}

# 占位符残留
PLACEHOLDER_RE = re.compile(r'(⬜|☐|\[\s*\]|我的笔记[:：]|TODO[:：]|待补[:：])')

# 首行署名标记
SIGNATURE_RE = re.compile(r'由「Youtube 转文章」skill\s*整理生成')

# 文末来源
SOURCE_RE = re.compile(r'^>\s*原文[:：]', re.M)


def is_word_char(ch):
    """既非空白也非标点 —— 用于 flanking 判定。"""
    return bool(ch) and not ch.isspace() and ch not in PUNCT


# ---------------------------------------------------------------- 预处理

def strip_non_prose(text):
    """
    剥掉不该参与「英文残留」检查的部分，返回纯散文文本。
    保留行号对应关系（删除内容替换为空串，不删行）。
    """
    lines = text.split('\n')
    out = []
    in_code = False
    in_front = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        # frontmatter
        if i == 0 and s == '---':
            in_front = True
            out.append('')
            continue
        if in_front:
            if s == '---':
                in_front = False
            out.append('')
            continue
        # 代码块围栏
        if s.startswith('```') or s.startswith('~~~'):
            in_code = not in_code
            out.append('')
            continue
        if in_code:
            out.append('')
            continue
        # 元数据行不参与英文检查：
        #   - 首行 skill 署名（含 skill / 触发词 等字样）
        #   - 引用块里的「原文 / 来源 / 讲者」信息行，以及几乎无中文的引用行
        #     （如 > 原文：How I Turn Joy into Art | Yinka Ilori | TED）
        # 中文引用块（金句）仍会正常参与检查。
        if i == 0 and SIGNATURE_RE.search(s):
            out.append('')
            continue
        if s.startswith('>'):
            if re.search(r'原文[:：]|来源[:：]|讲者[:：]|整理生成', s) or \
               len(re.findall(r'[\u4e00-\u9fff]', s)) < 2:
                out.append('')
                continue
        # 图片 / 链接：丢掉目标，保留文字
        ln2 = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', ln)
        ln2 = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', ln2)
        # 行内 code
        ln2 = re.sub(r'`[^`]*`', '', ln2)
        # 裸 URL
        ln2 = re.sub(r'https?://\S+', '', ln2)
        out.append(ln2)
    return '\n'.join(out)


# ---------------------------------------------------------------- 各检查项

def check_signature(lines):
    if not lines:
        return False, []
    return bool(SIGNATURE_RE.search(lines[0])), []


def check_heading_number(lines):
    bad = []
    for i, ln in enumerate(lines, 1):
        if HEADING_NUM_RE.match(ln):
            bad.append((i, ln.strip()[:60]))
    return (len(bad) == 0), bad


def check_bold(lines):
    """
    返回 (odd_ok, flank_ok, odd_list, flank_list)
    规则：
      - 每行 ** 的数量必须为偶数（禁止跨行未闭合）
      - 开 ** 后若紧跟标点/引号，则其前方必须是空白或标点
      - 闭 ** 前若紧跟标点/引号，则其后方必须是空白、标点或行尾
    """
    odd_list, flank_list = [], []
    for i, ln in enumerate(lines, 1):
        cnt = ln.count('**')
        if cnt == 0:
            continue
        if cnt % 2 == 1:
            odd_list.append((i, ln.strip()[:60]))
            continue
        # 成对拆解
        for m in re.finditer(r'\*\*', ln):
            s = m.start()
            # 判断这对是开还是闭：本行内第奇数个是开，偶数个是闭
            idx = ln.count('**', 0, s)
            is_open = (idx % 2 == 0)
            if is_open:
                after = ln[s + 2:s + 3]
                before = ln[s - 1:s]
                if after == '':
                    flank_list.append((i, '开标记后无内容', ln.strip()[:60]))
                elif not is_word_char(after):
                    # 内侧是标点/引号 -> 外侧必须是空白或标点
                    if before and is_word_char(before):
                        flank_list.append((i, '开标记内侧贴标点、外侧是普通字', ln.strip()[:60]))
            else:
                before = ln[s - 1:s]
                after = ln[s + 2:s + 3]
                if before == '':
                    flank_list.append((i, '闭标记前无内容', ln.strip()[:60]))
                elif not is_word_char(before):
                    # 内侧是标点 -> 外侧必须是空白/标点/行尾
                    if after and is_word_char(after):
                        flank_list.append((i, '闭标记内侧贴标点、外侧是普通字', ln.strip()[:60]))
    return (not odd_list), (not flank_list), odd_list, flank_list


def check_english(prose, allow):
    """统计正文中 >=3 个连续字母的英文词（已剥离代码/链接/URL/原文行）。"""
    allow_lc = set(x.lower() for x in allow)
    words = {}
    for m in re.finditer(r'[A-Za-z][A-Za-z\'\-]{2,}', prose):
        w = m.group(0).strip("'-")
        if len(w) < 3:
            continue
        if w.lower() in allow_lc:
            continue
        words[w] = words.get(w, 0) + 1
    return words


def check_md_link(lines):
    bad = []
    for i, ln in enumerate(lines, 1):
        if re.search(r'(?<!!)\[[^\]]+\]\((?!#)', ln):
            # 排除纯锚点链接
            bad.append((i, ln.strip()[:70]))
    return (len(bad) == 0), bad


def check_placeholder(lines):
    bad = []
    for i, ln in enumerate(lines, 1):
        if PLACEHOLDER_RE.search(ln):
            bad.append((i, ln.strip()[:60]))
    return (len(bad) == 0), bad


def check_source(text):
    return bool(SOURCE_RE.search(text)), []


CJK = r'[\u4e00-\u9fff]'
CJK_SPACE_RE = re.compile(r'(?<=' + CJK + r') (?=' + CJK + r')')


def check_cjk_space(text):
    n = len(CJK_SPACE_RE.findall(text))
    return (n == 0), [('', '共 %d 处中文间空格' % n)] if n else []


# ---------------------------------------------------------------- 主流程

def check_file(path, allow, strict=False, fix_spaces=False):
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    lines = raw.split('\n')
    prose = strip_non_prose(raw)

    print('=' * 68)
    print('文件：%s' % path)
    print('      共 %d 行 / %d 字' % (len(lines), len(raw)))

    results = {}

    ok, extra = check_signature(lines)
    results['首行署名'] = ok
    print('[1] 首行 skill 署名          : %s' % ('OK' if ok else '缺 —— 第一行应写「由「Youtube 转文章」skill 整理生成 · 触发词：整理成文章」'))

    ok, bad = check_heading_number(lines)
    results['小标题不编号'] = ok
    print('[2] 小标题未被编号            : %s' % ('OK' if ok else '有 %d 处' % len(bad)))
    for i, s in bad[:8]:
        print('      L%d  %s' % (i, s))

    ok_odd, ok_fl, odd, fl = check_bold(lines)
    results['加粗闭合'] = ok_odd
    results['加粗flanking'] = ok_fl
    print('[3] 加粗闭合（** 偶数）        : %s' % ('OK' if ok_odd else '有 %d 行奇数' % len(odd)))
    for i, s in odd[:8]:
        print('      L%d  %s' % (i, s))
    print('    加粗 flanking 连接性      : %s' % ('OK' if ok_fl else '有 %d 处' % len(fl)))
    for i, why, s in fl[:10]:
        print('      L%d  %s —— %s' % (i, why, s))

    words = check_english(prose, allow)
    results['英文残留'] = True   # 英文残留需人工判断，只报告
    total = sum(words.values())
    print('[4] 英文残留（需人工判定）      : %d 个不同词 / 共 %d 次' % (len(words), total))
    if words:
        top = sorted(words.items(), key=lambda x: -x[1])[:30]
        print('      ' + ', '.join('%s×%d' % (w, c) for w, c in top))
        print('      判据：人名/地名/品牌/公司/作品名/术语可留；普通名词、动词、形容词、副词、口语词必须译。')

    ok, bad = check_md_link(lines)
    results['链接已拆分'] = ok
    print('[5] 无 [文字](url) 写法        : %s' % ('OK' if ok else '有 %d 处' % len(bad)))
    for i, s in bad[:8]:
        print('      L%d  %s' % (i, s))

    ok, bad = check_placeholder(lines)
    results['无占位符'] = ok
    print('[6] 无占位符残留              : %s' % ('OK' if ok else '有 %d 处' % len(bad)))
    for i, s in bad[:8]:
        print('      L%d  %s' % (i, s))

    ok, _ = check_source(raw)
    results['文末来源'] = ok
    print('[7] 文末有「原文：」来源块      : %s' % ('OK' if ok else '缺 —— 文末应写 > 原文：{英文原题} | {讲者} | {来源}'))

    ok, bad = check_cjk_space(raw)
    results['中文间空格'] = ok
    print('[8] 中文之间无多余空格         : %s' % ('OK' if ok else '有 %d 处' % len(bad)))

    if fix_spaces and not ok:
        fixed = CJK_SPACE_RE.sub('', raw)
        io.open(path, 'w', encoding='utf-8', newline='\n').write(fixed)
        print('      （已清理并写回文件）')

    hard = ['首行署名', '小标题不编号', '加粗闭合', '加粗flanking', '链接已拆分', '无占位符', '文末来源', '中文间空格']
    failed = [k for k in hard if not results[k]]
    print('-' * 68)
    if failed:
        print('结论：不合格 —— %s' % '、'.join(failed))
    else:
        print('结论：格式项全部通过（英文残留请按上面清单人工确认）')
    return (not failed) or (not strict), failed


def main():
    ap = argparse.ArgumentParser(description='「Youtube 转文章」成稿校验器')
    ap.add_argument('targets', nargs='+', help='md 文件或目录')
    ap.add_argument('--strict', action='store_true', help='任一项不过即以退出码 1 结束')
    ap.add_argument('--allow', default='', help='逗号分隔的额外允许保留英文词')
    ap.add_argument('--fix-spaces', action='store_true', help='自动清理中文之间的多余空格')
    args = ap.parse_args()

    allow = set(DEFAULT_ALLOW)
    if args.allow:
        allow |= set(x.strip() for x in args.allow.split(',') if x.strip())

    files = []
    for t in args.targets:
        if os.path.isdir(t):
            for root, _, names in os.walk(t):
                if os.path.basename(root).startswith('.'):
                    continue
                for n in sorted(names):
                    if n.endswith('.md'):
                        files.append(os.path.join(root, n))
        elif os.path.isfile(t):
            files.append(t)
        else:
            print('跳过（不存在）：%s' % t)

    if not files:
        print('没有可校验的文件')
        return 2

    all_ok = True
    for f in files:
        ok, _ = check_file(f, allow, strict=args.strict, fix_spaces=args.fix_spaces)
        all_ok = all_ok and ok

    print()
    print('=' * 68)
    print('全部文件：%s' % ('通过' if all_ok else '存在不合格项'))
    return 0 if all_ok else (1 if args.strict else 0)


if __name__ == '__main__':
    sys.exit(main())
