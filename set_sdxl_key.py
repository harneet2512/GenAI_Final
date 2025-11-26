"""
Quick script to set SDXL API key in .env file.
"""

import os

# Your SDXL key - REPLACE WITH YOUR ACTUAL KEY
SDXL_KEY = "your_sdxl_api_key_here"

def update_env():
    """Update .env file with SDXL key."""
    
    # Read existing .env
    lines = []
    openai_key = "your_openai_api_key_here"
    
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            try:
                with open('.env', 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            except:
                pass
    
    # Extract existing OpenAI key if present
    for line in lines:
        if line.startswith('OPENAI_API_KEY='):
            openai_key = line.split('=', 1)[1].strip().strip('"').strip("'")
            if openai_key.startswith('your_'):
                openai_key = "your_openai_api_key_here"
    
    # Write updated .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("# OpenAI API Key for DALL·E 3 and embeddings\n")
        f.write(f"OPENAI_API_KEY={openai_key}\n\n")
        f.write("# SDXL API Key (Stability AI or compatible)\n")
        f.write(f"SDXL_API_KEY={SDXL_KEY}\n")
    
    print("=" * 60)
    print("[SUCCESS] SDXL_API_KEY updated in .env file!")
    print("=" * 60)
    print(f"\nSDXL Key: {SDXL_KEY[:20]}...{SDXL_KEY[-10:]}")
    
    if openai_key.startswith('your_'):
        print("\n[IMPORTANT] You still need to add your OPENAI_API_KEY!")
        print("Edit .env file and replace 'your_openai_api_key_here' with your actual key.")
        print("\nGet your OpenAI key from: https://platform.openai.com/api-keys")
    else:
        print(f"\nOpenAI Key: {openai_key[:20]}...{openai_key[-10:]}")
    
    print("\nVerify with: python verify_keys.py")

if __name__ == "__main__":
    update_env()


