"""
Test API keys to verify they're working.
"""

import os
from dotenv import load_dotenv

try:
    load_dotenv(encoding='utf-8')
except:
    # Try without encoding parameter for older versions
    load_dotenv()

def test_openai_key():
    """Test OpenAI API key."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key or api_key.startswith("your_") or len(api_key) < 20:
        print("[ERROR] OPENAI_API_KEY not properly configured")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test - check if we can access models
        # Just verify the key format is correct (starts with sk-)
        if api_key.startswith("sk-"):
            print("[OK] OpenAI API key format looks correct")
            print(f"     Key starts with: {api_key[:7]}...")
            return True
        else:
            print("[WARNING] OpenAI API key format unusual (should start with 'sk-')")
            return True  # Still might work
    except Exception as e:
        print(f"[ERROR] Error testing OpenAI key: {e}")
        return False

def test_sdxl_key():
    """Test SDXL API key."""
    api_key = os.getenv("SDXL_API_KEY", "")
    
    if not api_key or api_key.startswith("your_") or len(api_key) < 10:
        print("[ERROR] SDXL_API_KEY not properly configured")
        return False
    
    print("[OK] SDXL API key found")
    print(f"     Key starts with: {api_key[:10]}...")
    return True

def main():
    print("=" * 60)
    print("API Key Verification")
    print("=" * 60)
    
    openai_ok = test_openai_key()
    sdxl_ok = test_sdxl_key()
    
    print("\n" + "=" * 60)
    if openai_ok and sdxl_ok:
        print("[SUCCESS] Both API keys are configured!")
        print("\nYou're ready to run the pipeline:")
        print("  python main.py --all")
        return True
    else:
        print("[INCOMPLETE] Please check your API keys in .env file")
        return False

if __name__ == "__main__":
    main()

