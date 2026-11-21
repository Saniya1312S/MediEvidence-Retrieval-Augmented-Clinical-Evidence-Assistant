import os
import re

extracted_file = os.path.join("data", "extracted_text", "MED-DT-001_extracted.txt")
with open(extracted_file, "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect pages 1 to 5
pages = text.split("--- PAGE ")
for p in pages[1:5]:
    lines = p.split("\n")
    page_header = lines[0]
    content_sample = "\n".join(lines[1:10])
    print(f"=== PAGE {page_header} ===")
    print(content_sample)
    print()
