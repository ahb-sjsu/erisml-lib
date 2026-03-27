"""Systematically fix ALL unclosed/broken em tags across ALL books.

Strategy:
1. Protect <em class="math">...</em> pairs (these are correct)
2. Remove ALL plain <em> and orphaned </em> (these are broken markdown italic)
3. Restore math em tags
4. Verify balance
"""
import os
import re


def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Step 1: Extract and protect all <em class="math">...</em> pairs
    # Replace them with unique placeholders
    math_spans = []
    def protect_math(m):
        math_spans.append(m.group(0))
        return f'__MATH_PLACEHOLDER_{len(math_spans)-1}__'

    content = re.sub(
        r'<em class="math">(.*?)</em>',
        protect_math,
        content,
        flags=re.DOTALL
    )

    # Step 2: Remove ALL remaining <em> and </em> tags (broken italic from markdown)
    plain_em_removed = content.count('<em>') + content.count('<em ')
    content = re.sub(r'<em(?:\s[^>]*)?>',  '', content)  # remove <em> and <em ...>
    content = content.replace('</em>', '')  # remove orphaned </em>

    # Step 3: Restore math em tags
    for i, span in enumerate(math_spans):
        content = content.replace(f'__MATH_PLACEHOLDER_{i}__', span)

    # Step 4: Fix any <em class="math"> that contain * not escaped as ^*
    # Pattern: <em class="math">...*</em> where * should be ^*
    def fix_star_in_math(m):
        inner = m.group(1)
        # If it ends with * (not ^*), fix it
        if inner.endswith('*') and not inner.endswith('^*'):
            inner = inner[:-1] + '^*'
        # Fix internal unescaped * that aren't ^*
        # But be careful: * in \text{...} is fine
        return '<em class="math">' + inner + '</em>'

    content = re.sub(
        r'<em class="math">(.*?)</em>',
        fix_star_in_math,
        content,
        flags=re.DOTALL
    )

    # Step 5: Verify balance
    opens = content.count('<em')
    closes = content.count('</em>')

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, plain_em_removed, opens, closes
    return False, 0, opens, closes


total_fixed = 0
total_em_removed = 0
imbalanced = []

for book in ['book', 'geometric-reasoning', 'geometric-economics', 'geometric-law',
             'geometric-cognition', 'geometric-communication', 'geometric-medicine']:
    book_dir = os.path.join('docs', book)
    if not os.path.isdir(book_dir):
        continue
    for fn in sorted(os.listdir(book_dir)):
        if not fn.endswith('.html') or fn == 'index.html':
            continue
        path = os.path.join(book_dir, fn)
        fixed, em_removed, opens, closes = fix_file(path)
        if fixed:
            total_fixed += 1
            total_em_removed += em_removed
            status = 'OK' if opens == closes else f'IMBALANCED ({opens} opens, {closes} closes)'
            if opens != closes:
                imbalanced.append(f'{book}/{fn}')
            print(f'  {book}/{fn}: removed {em_removed} plain <em>, {status}')

print(f'\nTotal: {total_fixed} files fixed, {total_em_removed} plain <em> tags removed')
if imbalanced:
    print(f'Still imbalanced ({len(imbalanced)}):')
    for f in imbalanced:
        print(f'  {f}')
else:
    print('All files balanced!')
