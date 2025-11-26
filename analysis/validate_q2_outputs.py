"""
Q2 Output Validator
===================
Validates Q2 analysis JSON outputs for correctness and completeness.
"""

import json
import os
import sys
from typing import Dict, List, Tuple

EXPECTED = {
    "ps5": {
        "product_name": "PlayStation\u00ae5 Digital Edition (Slim)",
        "forbidden_terms": ["PS5 Pro", "PSSR", "2TB"],
    },
    "stanley": {
        "product_name": "STANLEY Quencher H2.0 Tumbler",
        "forbidden_terms": [],
    },
    "jordans": {
        "product_name": "Nike Men's Court Vision Mid Next Nature Shoes",
        "forbidden_terms": [
            "Air Jordan",
            "Jordan 1",
            "Jordan 1 Low",
            "Court Vision 1 Low",
            "Low Sneaker",
        ],
    },
}

NON_VISUAL_KEYWORDS = [
    "box",
    "packaging",
    "shipping",
    "customer service",
    "support",
    "stiffness",
    "comfort",
    "durability",
]

ANALYSIS_DIR = "analysis"
PRODUCT_IDS = ["ps5", "stanley", "jordans"]


def load_analysis(product_id: str) -> Dict:
    """Load analysis JSON for a product."""
    path = os.path.join(ANALYSIS_DIR, f"{product_id}_analysis.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_product_name(product_id: str, analysis: Dict) -> Tuple[bool, str]:
    """Check if product_name matches expected."""
    expected_name = EXPECTED[product_id]["product_name"]
    actual_name = analysis.get("visual_attributes", {}).get("product_name", "")
    
    if actual_name == expected_name:
        return True, f'OK: product_name matches "{expected_name}"'
    else:
        return False, f'ERROR: product_name is "{actual_name}" but expected "{expected_name}"'


def check_forbidden_terms(product_id: str, analysis: Dict) -> List[str]:
    """Check for forbidden terms in all text fields."""
    forbidden = EXPECTED[product_id]["forbidden_terms"]
    if not forbidden:
        return []
    
    errors = []
    
    # Collect all text to search
    texts_to_search = [
        ("zero_shot_summary", analysis.get("zero_shot_summary", "")),
        ("rag_summary", analysis.get("rag_summary", "")),
        ("visual_attributes", json.dumps(analysis.get("visual_attributes", {}))),
        ("visual_sentiment", json.dumps(analysis.get("visual_sentiment", {}))),
    ]
    
    for field_name, text in texts_to_search:
        if not isinstance(text, str):
            continue
        text_lower = text.lower()
        for term in forbidden:
            if term.lower() in text_lower:
                errors.append(f'ERROR: forbidden term "{term}" found in {field_name}')
    
    return errors


def check_non_visual_pollution(product_id: str, analysis: Dict) -> List[str]:
    """Check for non-visual keywords in visual fields."""
    warnings = []
    
    # Check visual_sentiment features
    visual_sentiment = analysis.get("visual_sentiment", {})
    for key in ["positive_visual_features", "negative_visual_features"]:
        features = visual_sentiment.get(key, [])
        if isinstance(features, list):
            for i, feat in enumerate(features):
                if isinstance(feat, dict):
                    feature_name = feat.get("feature", "")
                    if isinstance(feature_name, str):
                        feature_lower = feature_name.lower()
                        for kw in NON_VISUAL_KEYWORDS:
                            if kw in feature_lower:
                                warnings.append(
                                    f'WARNING: {key}[{i}].feature contains non-visual keyword "{kw}": "{feature_name}"'
                                )
    
    # Check visual_attributes themes
    visual_attributes = analysis.get("visual_attributes", {})
    for key in ["positive_visual_themes", "negative_visual_themes"]:
        themes = visual_attributes.get(key, [])
        if isinstance(themes, list):
            for i, theme in enumerate(themes):
                if isinstance(theme, str):
                    theme_lower = theme.lower()
                    for kw in NON_VISUAL_KEYWORDS:
                        if kw in theme_lower:
                            warnings.append(
                                f'WARNING: visual_attributes.{key}[{i}] contains non-visual keyword "{kw}": "{theme}"'
                            )
    
    return warnings


def check_required_fields(product_id: str, analysis: Dict) -> List[str]:
    """Check that required visual attribute fields exist and are not empty."""
    warnings = []
    visual_attributes = analysis.get("visual_attributes", {})
    
    required_fields = {
        "shape": "visual_attributes.shape",
        "materials": "visual_attributes.materials",
        "color_palette": "visual_attributes.color_palette",
        "branding_elements": "visual_attributes.branding_elements",
        "distinctive_features": "visual_attributes.distinctive_features",
    }
    
    for field, path in required_fields.items():
        value = visual_attributes.get(field)
        if value is None:
            warnings.append(f'WARNING: {path} is missing')
        elif field in ["color_palette", "branding_elements", "distinctive_features"]:
            if isinstance(value, list) and len(value) == 0:
                warnings.append(f'WARNING: {path} is empty')
        elif isinstance(value, str) and (value == "" or value == "N/A"):
            warnings.append(f'WARNING: {path} is empty or N/A')
    
    return warnings


def main():
    """Run validation on all Q2 outputs."""
    print("=== Q2 Validation Report ===\n")
    
    all_errors = []
    all_warnings = []
    
    for product_id in PRODUCT_IDS:
        print(f"[{product_id}]")
        
        try:
            analysis = load_analysis(product_id)
        except FileNotFoundError as e:
            print(f"  ERROR: {e}\n")
            all_errors.append(f"{product_id}: File not found")
            continue
        
        # Check product_name
        is_ok, msg = check_product_name(product_id, analysis)
        print(f"  {msg}")
        if not is_ok:
            all_errors.append(f"{product_id}: {msg}")
        
        # Check forbidden terms
        forbidden_errors = check_forbidden_terms(product_id, analysis)
        for error in forbidden_errors:
            print(f"  {error}")
            all_errors.append(f"{product_id}: {error}")
        
        # Check non-visual pollution
        pollution_warnings = check_non_visual_pollution(product_id, analysis)
        for warning in pollution_warnings:
            print(f"  {warning}")
            all_warnings.append(f"{product_id}: {warning}")
        
        # Check required fields
        field_warnings = check_required_fields(product_id, analysis)
        for warning in field_warnings:
            print(f"  {warning}")
            all_warnings.append(f"{product_id}: {warning}")
        
        print()
    
    # Summary
    if all_errors:
        print(f"\nTotal ERRORS: {len(all_errors)}")
    if all_warnings:
        print(f"Total WARNINGS: {len(all_warnings)}")
    
    if not all_errors and not all_warnings:
        print("\n[OK] All validations passed!")
    
    # Exit with error code if any errors found
    if all_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

