"""Fix unclosed <em class="math"> tags caused by * being treated as italic.

The pattern: <em class="math">\gamma_i* should be <em class="math">\gamma_i^*</em>
The * gets eaten by markdown as italic start/end, leaving unclosed tags.
"""

import os
import re


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Fix pattern: <em class="math">...*. (asterisk at end of math, no closing tag)
    # Replace with proper closing
    content = re.sub(
        r'(<em class="math">)(.*?)\*\.\s*(?:The|A|Each|This|In|For|When|Where|If|Since|Let|Given|Note)',
        lambda m: (
            m.group(1) + m.group(2) + "^*</em>. " + m.group(0).split(". ", 1)[1]
            if ". " in m.group(0)
            else m.group(0)
        ),
        content,
    )

    # More targeted: find <em class="math"> without matching </em> before next tag
    # Strategy: ensure every <em class="math"> has a </em>
    parts = content.split('<em class="math">')
    if len(parts) > 1:
        fixed_parts = [parts[0]]
        for part in parts[1:]:
            # Check if </em> comes before the next < tag (excluding </em> itself)
            em_close = part.find("</em>")
            next_tag = re.search(r"<(?!/)(?!em)", part)

            if em_close == -1:
                # No closing tag at all - find a reasonable place to close
                # Look for end of math content (period, comma, space followed by word)
                match = re.search(r"([^<]*?)(\.\s|\,\s|\s(?=[A-Z]))", part)
                if match:
                    math_content = match.group(1)
                    # Clean up the math content - replace trailing * with ^*
                    if math_content.endswith("*"):
                        math_content = math_content[:-1] + "^*"
                    fixed_parts.append(
                        math_content
                        + "</em>"
                        + part[match.end() - len(match.group(2)) :]
                    )
                else:
                    fixed_parts.append(part)  # can't fix safely
            elif next_tag and next_tag.start() < em_close:
                # Closing tag comes after another HTML tag - might be unclosed
                # Check if there's meaningful math content before the next tag
                pre_tag = part[: next_tag.start()]
                if "*" in pre_tag and "</em>" not in pre_tag:
                    # Fix: close before the *, treat * as ^*
                    pre_tag = pre_tag.replace("*", "^*</em>", 1)
                    fixed_parts.append(pre_tag + part[next_tag.start() :])
                else:
                    fixed_parts.append(part)
            else:
                fixed_parts.append(part)

        content = '<em class="math">'.join(fixed_parts)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


count = 0
for book in [
    "book",
    "geometric-reasoning",
    "geometric-economics",
    "geometric-law",
    "geometric-cognition",
    "geometric-communication",
    "geometric-medicine",
]:
    book_dir = os.path.join("docs", book)
    if not os.path.isdir(book_dir):
        continue
    for fn in sorted(os.listdir(book_dir)):
        if not fn.endswith(".html") or fn == "index.html":
            continue
        if fix_file(os.path.join(book_dir, fn)):
            count += 1
            print(f"  Fixed: {book}/{fn}")

print(f"\nTotal: {count} files fixed")
