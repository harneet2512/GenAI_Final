"""
Quick script to set OpenAI API key in .env file.
"""

import os

# Your OpenAI key - REPLACE WITH YOUR ACTUAL KEY
OPENAI_KEY = "your_openai_api_key_here"

def update_env():
    """Update .env file with OpenAI key."""
    
    # Read existing .env
    lines = []
    sdxl_key = "your_sdxl_api_key_here"
    
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
    
    # Extract existing SDXL key if present
    for line in lines:
        if line.startswith('SDXL_API_KEY='):
            sdxl_key = line.split('=', 1)[1].strip().strip('"').strip("'")
            if sdxl_key.startswith('your_'):
                sdxl_key = "your_sdxl_api_key_here"
    
    # Write updated .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("# OpenAI API Key for DALL·E 3 and embeddings\n")
        f.write(f"OPENAI_API_KEY={OPENAI_KEY}\n\n")
        f.write("# SDXL API Key (Stability AI or compatible)\n")
        f.write(f"SDXL_API_KEY={sdxl_key}\n")
    
    print("=" * 60)
    print("[SUCCESS] OPENAI_API_KEY updated in .env file!")
    print("=" * 60)
    print(f"\nOpenAI Key: {OPENAI_KEY[:25]}...{OPENAI_KEY[-20:]}")
    print(f"SDXL Key: {sdxl_key[:20]}...{sdxl_key[-10:]}")
    print("\n[SUCCESS] Both API keys are now configured!")
    print("\nVerify with: python verify_keys.py")
    print("\nYou're ready to run the pipeline:")
    print("  python main.py --all")

if __name__ == "__main__":
    update_env()


