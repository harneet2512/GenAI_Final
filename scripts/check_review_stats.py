import json

ps5 = json.load(open('data/processed/reviews_ps5_B0CL61F39H.json', encoding='utf-8'))
stanley = json.load(open('data/processed/reviews_stanley_B0CJZMP7L1.json', encoding='utf-8'))
jordans = json.load(open('data/processed/reviews_jordans_B0DJ9SVTB6.json', encoding='utf-8'))

print(f"PS5: {len(ps5)} reviews")
print(f"Stanley: {len(stanley)} reviews")
print(f"Jordans: {len(jordans)} reviews")

print(f"\nAverage review length (characters):")
print(f"PS5: {sum(len(r.get('body', '')) for r in ps5) / len(ps5):.0f} chars")
print(f"Stanley: {sum(len(r.get('body', '')) for r in stanley) / len(stanley):.0f} chars")
print(f"Jordans: {sum(len(r.get('body', '')) for r in jordans) / len(jordans):.0f} chars")

print(f"\nTotal text content:")
print(f"PS5: {sum(len(r.get('body', '')) for r in ps5):,} chars")
print(f"Stanley: {sum(len(r.get('body', '')) for r in stanley):,} chars")
print(f"Jordans: {sum(len(r.get('body', '')) for r in jordans):,} chars")

