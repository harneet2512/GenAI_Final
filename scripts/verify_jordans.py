"""Quick verification script for jordans output."""
import json

data = json.load(open('analysis/jordans_analysis.json', encoding='utf-8'))

print("=== JORDANS VALIDATION ===")
print(f"Product Name: {data['visual_attributes']['product_name']}")
print(f"Shape: {data['visual_attributes']['shape']}")
print(f"\nDistinctive Features: {data['visual_attributes']['distinctive_features']}")

print("\nChecking summaries for forbidden terms...")
summaries = data['zero_shot_summary'] + ' ' + data['rag_summary']
forbidden = ['Air Jordan', 'Jordan 1', 'Jordan 1 Low', 'Court Vision 1 Low', 'Low Sneaker', 'high-top', 'High-top']
found = [term for term in forbidden if term in summaries]
print(f"Forbidden terms in summaries: {found if found else 'None [OK]'}")

print("\nChecking visual attributes...")
va = data['visual_attributes']
print(f"Shape contains 'low': {'low' in va['shape'].lower()}")
print(f"Shape contains 'mid-top': {'mid-top' in va['shape'].lower()}")

print("\n[OK] All checks passed!" if not found and 'mid-top' in va['shape'].lower() else "\n[WARNING] Some issues found")


