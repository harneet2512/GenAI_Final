"""
Verify API keys are set correctly.
Handles encoding issues with .env file.
"""

import os
import sys

def read_env_manual():
    """Manually read .env file with error handling."""
    env_vars = {}
    
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found")
        return env_vars
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open('.env', 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[WARNING] Error reading .env with {encoding}: {e}")
            continue
    
    return env_vars

def main():
    print("=" * 60)
    print("API Key Verification")
    print("=" * 60)
    
    # Read .env manually
    env_vars = read_env_manual()
    
    # Check OpenAI key
    openai_key = env_vars.get('OPENAI_API_KEY', '')
    print(f"\n[1] OPENAI_API_KEY:")
    if not openai_key:
        print("   [ERROR] Not found in .env file")
    elif openai_key.startswith('your_') or len(openai_key) < 20:
        print("   [ERROR] Still has placeholder value")
        print(f"   Current value: {openai_key[:20]}...")
    else:
        print("   [OK] Found and configured")
        print(f"   Key preview: {openai_key[:10]}...{openai_key[-4:]}")
        if openai_key.startswith('sk-'):
            print("   [OK] Format looks correct (starts with 'sk-')")
        else:
            print("   [WARNING] Format unusual (should start with 'sk-')")
    
    # Check SDXL key
    sdxl_key = env_vars.get('SDXL_API_KEY', '')
    print(f"\n[2] SDXL_API_KEY:")
    if not sdxl_key:
        print("   [ERROR] Not found in .env file")
    elif sdxl_key.startswith('your_') or len(sdxl_key) < 10:
        print("   [ERROR] Still has placeholder value")
        print(f"   Current value: {sdxl_key[:20]}...")
    else:
        print("   [OK] Found and configured")
        print(f"   Key preview: {sdxl_key[:10]}...{sdxl_key[-4:]}")
    
    # Summary
    print("\n" + "=" * 60)
    openai_ok = openai_key and not openai_key.startswith('your_') and len(openai_key) >= 20
    sdxl_ok = sdxl_key and not sdxl_key.startswith('your_') and len(sdxl_key) >= 10
    
    if openai_ok and sdxl_ok:
        print("[SUCCESS] Both API keys are configured!")
        print("\nYou're ready to run the pipeline:")
        print("  python main.py --all")
        print("\nOr test with a single product:")
        print("  python main.py --product-id B0CKZGY5B6")
        return True
    else:
        print("[INCOMPLETE] Please check your .env file")
        print("\nYour .env file should look like:")
        print("  OPENAI_API_KEY=sk-your-actual-key-here")
        print("  SDXL_API_KEY=your-actual-key-here")
        print("\nMake sure:")
        print("  - No quotes around the values")
        print("  - No spaces around the = sign")
        print("  - Keys are on separate lines")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


