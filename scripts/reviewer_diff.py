import re
# Check placeholder patterns in clean md
with open('P7_manuscript_clean.md', encoding='utf-8') as f:
    clean = f.read()
print("=== P7_manuscript_clean.md placeholder scan ===")
for pat in ['Figure to be generated', 'placeholder', 'PLACEHOLDER', 'To be confirmed', 'XXX', 'TODO', 'TBD']:
    n = len(re.findall(re.escape(pat), clean, re.I))
    print(f"  {pat}: {n}")
    for m in re.finditer(re.escape(pat), clean, re.I):
        s = max(0, m.start()-70)
        print("     ...", clean[s:m.start()+70].replace('\n',' '))

# compare P5 vs P7 (data tokens)
with open('P5_manuscript.md', encoding='utf-8') as f:
    p5 = f.read()
print("\n=== P5 vs P7 structural check ===")
print("P5 length:", len(p5), "| P7 clean length:", len(clean))
# key data in both
tokens = ['24,098','34,003','0.56','0.39','1.62','0.42','15,292','37.6','4.87','2.61','QNPY2023-30']
for t in tokens:
    print(f"  {t}: P5={'Y' if t in p5 else 'N'} P7={'Y' if t in clean else 'N'}")
