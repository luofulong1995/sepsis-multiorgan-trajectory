import re
with open('P7_manuscript_clean.md', encoding='utf-8') as f:
    text = f.read()

# Count per section
sections = ['Introduction', 'Methods', 'Results', 'Discussion', 'Limitations', 'Conclusions']
idx = {}
for s in sections:
    m = re.search(r'^## ' + s + r'\s*$', text, re.M)
    if m:
        idx[s] = m.start()
# order
order = sorted(idx.items(), key=lambda x: x[1])
print("Section boundaries found:")
for s, pos in order:
    print(f"  {s} @ {pos}")

# word count from Introduction to List of Abbreviations
start = idx.get('Introduction')
end_m = re.search(r'^## List of Abbreviations', text, re.M)
end = end_m.start() if end_m else len(text)
main = text[start:end]
main_nohead = re.sub(r'^#{1,4} .*$', '', main, flags=re.M)
print("\nMain text (Intro->Conclusions, incl headings):", len(main.split()))
print("Main text (no headings):", len(main_nohead.split()))

# Also count P5_manuscript.md version
with open('P5_manuscript.md', encoding='utf-8') as f:
    text5 = f.read()
m5 = re.search(r'## Introduction\n(.*?)\n\n## List of Abbreviations', text5, re.S)
if m5:
    print("\nP5_manuscript.md main text words:", len(m5.group(1).split()))
