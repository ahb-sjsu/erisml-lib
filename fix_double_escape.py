"""Fix ALL double-escaped LaTeX in ALL chapter HTML files.
Replaces \\\\ with \\ inside em.math and display-math elements."""

import os
import re

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix double backslashes before LaTeX commands
    # In HTML source: \\beta should be \beta
    # But we need to be careful not to break actual HTML

    # Strategy: find all content inside <em class="math">...</em> tags
    # and fix double escaping within those
    def fix_math_content(match):
        text = match.group(1)
        # Replace \\\\ with \\ (double-escaped to single-escaped)
        # In the file, \\beta appears as the literal characters \ \ b e t a
        text = text.replace('\\\\', '\\')
        # Also fix escaped underscores
        text = text.replace('\\_', '_')
        return '<em class="math">' + text + '</em>'

    content = re.sub(
        r'<em class="math">(.*?)</em>',
        fix_math_content,
        content,
        flags=re.DOTALL
    )

    # Also fix display math
    def fix_display_math(match):
        text = match.group(1)
        text = text.replace('\\\\', '\\')
        text = text.replace('\\_', '_')
        return '<p class="display-math">' + text + '</p>'

    content = re.sub(
        r'<p class="display-math">(.*?)</p>',
        fix_display_math,
        content,
        flags=re.DOTALL
    )

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

count = 0
for book in ['book', 'geometric-reasoning', 'geometric-economics', 'geometric-law',
             'geometric-cognition', 'geometric-communication', 'geometric-medicine']:
    book_dir = os.path.join('docs', book)
    if not os.path.isdir(book_dir):
        continue
    for fn in sorted(os.listdir(book_dir)):
        if not fn.endswith('.html') or fn == 'index.html':
            continue
        if fix_file(os.path.join(book_dir, fn)):
            count += 1
            print(f'  Fixed: {book}/{fn}')

print(f'\nTotal: {count} files fixed')
