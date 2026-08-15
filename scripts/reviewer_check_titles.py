import re
with open('P7_manuscript_clean.md', encoding='utf-8') as f:
    text = f.read()

print("=== FIGURE TITLES (first sentence of legend) — limit <=15 words ===")
figsec = text.split('## Figure Legends')[1].split('## Supplemental')[0]
figs = re.findall(r'\*\*Figure (\d+)\.\s+(.*?)\*\*(.*?)(?=\n\n\*\*Figure|\Z)', figsec, re.S)
for num, title, legend in figs:
    tw = len(title.split())
    # legend words after the bold title portion
    legend_body = legend.strip()
    lw = len(legend_body.split())
    print(f"Fig{num}: title words={tw} ({'OK' if tw<=15 else 'OVER'}) | legend words={lw} ({'OK' if lw<=300 else 'OVER'})")
    print(f"   Title: {title[:90]}")

print("\n=== TABLE TITLES — limit <=15 words ===")
tablesec = text.split('## Tables')[1].split('## Figure Legends')[0]
titles = re.findall(r'### Table (\d+)\.\s+(.+)', tablesec)
for num, t in titles:
    tw = len(t.split())
    print(f"Table{num}: {tw} words ({'OK' if tw<=15 else 'OVER'}): {t[:90]}")
