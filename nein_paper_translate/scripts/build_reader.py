#!/usr/bin/env python3
"""校验逐词对照数据，并把数据注入阅读器模板生成单文件 HTML。

用法：
  build_reader.py data.json -o 三栏对照阅读.html          # 校验 + 生成
  build_reader.py data.json --check                        # 只校验，不生成
  build_reader.py data.json --fix-suggest                  # 校验并打印定位失败词条的上下文

定位规则（与阅读器 JS 完全一致）：英文句子里只保留 Unicode 字母与数字并小写，
词条词面按同样方式压缩后，从上一词条之后的游标开始向前查找。
"""
import argparse, json, os, re, sys

CJK = re.compile(r'[一-鿿㐀-䶿]')
TEMPLATE_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'reader-template.html')


def compact(t):
    return ''.join(c.lower() for c in t if c.isalnum())


def ckey(w):
    return compact(w)


def sentences(data):
    out = []
    for si, sec in enumerate(data.get('sections', [])):
        for pi, par in enumerate(sec.get('paras', [])):
            for s in par.get('sents', []):
                out.append((si + 1, sec.get('id', '?'), par.get('key', '?'), par.get('kind', 'para'), s))
    return out


def audit(data, show = 12):
    """返回 (errors, warnings, stats)。errors 非空时不应生成 HTML。"""
    errors, warns = [], []
    meta = data.get('meta') or {}
    for k in ('titleEn', 'titleZh', 'slug'):
        if not meta.get(k):
            warns.append('meta.%s 缺失（标题/笔记存储键会用兜底值）' % k)
    if not data.get('sections'):
        errors.append('sections 为空')
        return errors, warns, {'sections': 0, 'sentences': 0, 'tokens': 0, 'miss': 0,
                               'backward': 0, 'empty_gloss': 0, 'gloss_no_cjk': 0, 'weird_word': 0}, ''

    n_sent = n_tok = 0
    miss, back, empty_gloss, no_cjk, weird = [], [], [], [], []
    for sno, sid, pkey, kind, s in sentences(data):
        n_sent += 1
        en = s.get('en', '')
        if not en:
            errors.append('第 %d 句（%s/%s）缺少 en' % (n_sent, sid, pkey)); continue
        if not (s.get('zh') or '').strip():
            errors.append('第 %d 句（%s/%s）缺少 zh 译文' % (n_sent, sid, pkey))
        if 't' not in s or not isinstance(s['t'], list):
            errors.append('第 %d 句（%s/%s）缺少逐词数组 t' % (n_sent, sid, pkey)); continue
        comp = compact(en)
        cur = 0
        for it in s['t']:
            n_tok += 1
            if not (isinstance(it, list) and len(it) >= 2 and isinstance(it[0], str) and isinstance(it[1], str)):
                errors.append('第 %d 句词条格式应为 [词面, 释义]：%r' % (n_sent, it)); continue
            w, g = it[0], it[1]
            k = ckey(w)
            if not k:
                miss.append((n_sent, sid, w, '词面无字母数字')); continue
            if not g.strip():
                empty_gloss.append((n_sent, sid, w))
            elif not CJK.search(g):
                no_cjk.append((n_sent, sid, w, g[:24]))
            if CJK.search(w):
                weird.append((n_sent, sid, w, '词面含中文'))
            p = comp.find(k, cur)
            if p < 0:
                p0 = comp.find(k)
                if p0 < 0:
                    miss.append((n_sent, sid, w, en[:70]))
                else:
                    back.append((n_sent, sid, w, en[:70]))
                    cur = p0 + len(k)
            else:
                cur = p + len(k)
    if miss:
        errors.append('硬漏定位 %d 个词条（词面在句中不存在）' % len(miss))
    if back:
        errors.append('回溯匹配 %d 个词条（顺序与原文不一致，会打断高亮游标）' % len(back))
    if empty_gloss:
        errors.append('空释义 %d 个' % len(empty_gloss))

    stats = {'sections': len(data['sections']), 'sentences': n_sent, 'tokens': n_tok,
             'miss': len(miss), 'backward': len(back), 'empty_gloss': len(empty_gloss),
             'gloss_no_cjk': len(no_cjk), 'weird_word': len(weird)}
    rep = []
    for name, lst in (('HARD MISS', miss), ('BACKWARD', back), ('EMPTY GLOSS', empty_gloss),
                      ('NO CJK GLOSS', no_cjk), ('WEIRD', weird)):
        if not lst:
            continue
        rep.append('%s (%d):' % (name, len(lst)))
        for x in lst[:show]:
            rep.append('  s%-4d %-10s %s' % (x[0], x[1] if len(x) > 1 else '', ' | '.join(str(y) for y in x[2:])))
        if len(lst) > show:
            rep.append('  … 还有 %d 条' % (len(lst) - show))
    return errors, warns, stats, '\n'.join(rep)


def build(data_path, out_path, template_path, force=False, check=False):
    data = json.load(open(data_path, encoding='utf-8'))
    errors, warns, stats, report = audit(data)
    print('sections=%(sections)s sentences=%(sentences)s tokens=%(tokens)s '
          'miss=%(miss)s backward=%(backward)s empty_gloss=%(empty_gloss)s' % stats)
    if report:
        print(report)
    for w in warns:
        print('warn: %s' % w)
    if check:
        for e in errors:
            print('ERROR: %s' % e)
        print('校验%s通过' % ('' if not errors else '未'))
        return 0 if not errors else 1
    if errors and not force:
        for e in errors:
            print('ERROR: %s' % e)
        print('未生成 HTML。修复数据后重试，或加 --force 跳过（漏定位的词条在阅读器里只无法高亮）。')
        return 1
    tpl = open(template_path, encoding='utf-8').read()
    if tpl.count('__DATA__') != 1:
        print('ERROR: 模板里的 __DATA__ 占位符应恰好出现 1 次，实际 %d 次' % tpl.count('__DATA__'))
        return 1
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = tpl.replace('__DATA__', js)
    if out_path == '-':
        sys.stdout.write(html)
    else:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print('已生成 %s（%d 字节）' % (out_path, os.path.getsize(out_path)))
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('data')
    ap.add_argument('-o', '--out', default=None)
    ap.add_argument('--template', default=TEMPLATE_DEFAULT)
    ap.add_argument('--check', action='store_true', help='只校验，不生成 HTML')
    ap.add_argument('--force', action='store_true', help='有定位错误也生成')
    a = ap.parse_args()
    out = '-' if a.check else (a.out or os.path.splitext(os.path.basename(a.data))[0] + '.html')
    sys.exit(build(a.data, out, a.template, a.force, a.check))
