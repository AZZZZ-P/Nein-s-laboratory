#!/usr/bin/env python3
"""把 PDF 抽成纯文本，句子重建的原料。

用法：
  extract_pdf.py paper.pdf -o _work/source.txt

依次尝试 PyMuPDF(fitz) → pdfplumber → 系统 pdftotext。
输出带 `=== PAGE n ===` 标记；成功后打印字符数与每页行数。
"""
import argparse, os, shutil, subprocess, sys


def with_fitz(path):
    import fitz
    doc = fitz.open(path)
    return [(p.get_text('text'), i + 1) for i, p in enumerate(doc)]


def with_pdfplumber(path):
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        for i, p in enumerate(pdf.pages):
            out.append((p.extract_text() or '', i + 1))
    return out


def with_pdftotext(path):
    if not shutil.which('pdftotext'):
        raise RuntimeError('pdftotext 未安装')
    tmp = path + '.pdftotext.txt'
    subprocess.run(['pdftotext', '-layout', path, tmp], check=True)
    txt = open(tmp, encoding='utf-8', errors='replace').read()
    os.remove(tmp)
    pages = txt.split('\f')
    return [(p, i + 1) for i, p in enumerate(pages)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    errs = []
    for name, fn in (('PyMuPDF', with_fitz), ('pdfplumber', with_pdfplumber), ('pdftotext', with_pdftotext)):
        try:
            pages = fn(a.pdf)
            break
        except Exception as e:
            errs.append('%s: %s' % (name, str(e)[:80]))
            pages = None
    if pages is None:
        print('三种抽取方式都不可用：\n  ' + '\n  '.join(errs))
        print('改用 Read 工具直接读取 PDF（可分页），或 pip install pymupdf。')
        return 1
    body = []
    for txt, no in pages:
        txt = txt.replace('\u00ad', '').replace('\ufb01', 'fi').replace('\ufb02', 'fl')
        body.append('=== PAGE %d ===\n%s' % (no, txt.rstrip()))
    out = '\n\n'.join(body) + '\n'
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(out)
    print('已抽取 %d 页 / %d 字符 → %s' % (len(pages), len(out), a.out))
    print('提醒：抽取文本会有断行、页眉页脚、字距拉开（如 s h o r t）等噪声，切句前先按页清理。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
