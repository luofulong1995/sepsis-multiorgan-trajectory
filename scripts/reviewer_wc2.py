import re
with open('P7_manuscript_clean.md', encoding='utf-8') as f:
    text = f.read()
# From Introduction heading through Conclusions section end (stop at List of Abbreviations)
m = re.search(r'^## Introduction\s*$', text, re.M)
start = m.start()
m2 = re.search(r'^## List of Abbreviations', text, re.M)
end = m2.start()
seg = text[start:end]
# remove markdown headings and em-dash markers, count words
seg_nohead = re.sub(r'^#{1,6} .*$', '', seg, flags=re.M)
words_incl = len(seg.split())
words_excl = len(seg_nohead.split())
print(f"Intro->Conclusions incl headings: {words_incl}")
print(f"Intro->Conclusions excl headings: {words_excl}")

# Check what P5 manuscript had
with open('P5_manuscript.md', encoding='utf-8') as f:
    t5 = f.read()
m = re.search(r'^## Introduction\s*$', t5, re.M)
m2 = re.search(r'^## List of Abbreviations', t5, re.M)
if m and m2:
    seg5 = t5[m.start():m2.start()]
    print(f"P5 Intro->Conclusions words: {len(seg5.split())}")
