"""
Helper script to update .env file with API keys.
"""

import os
import re

def update_env_file(openai_key=None, sdxl_key=None):
    """Update .env file with provided keys."""
    
    # Read existing .env if it exists
    env_content = []
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        except:
            try:
                with open('.env', 'r', encoding='latin-1') as f:
                    env_content = f.readlines()
            except:
                env_content = []
    
    # Parse existing content
    env_dict = {}
    for line in env_content:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env_dict[key] = value
    
    # Update with provided keys
    if openai_key:
        # Clean the key (remove any trailing characters like |)
        openai_key = openai_key.strip().rstrip('|').strip()
        env_dict['OPENAI_API_KEY'] = openai_key
        print(f"[OK] Updated OPENAI_API_KEY: {openai_key[:15]}...")
    
    if sdxl_key:
        # Clean the key (remove any trailing characters like |)
        sdxl_key = sdxl_key.strip().rstrip('|').strip()
        env_dict['SDXL_API_KEY'] = sdxl_key
        print(f"[OK] Updated SDXL_API_KEY: {sdxl_key[:15]}...")
    
    # Write back to .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("# OpenAI API Key for DALL·E 3 and embeddings\n")
        f.write(f"OPENAI_API_KEY={env_dict.get('OPENAI_API_KEY', 'your_openai_api_key_here')}\n\n")
        f.write("# SDXL API Key (Stability AI or compatible)\n")
        f.write(f"SDXL_API_KEY={env_dict.get('SDXL_API_KEY', 'your_sdxl_api_key_here')}\n")
    
    print("\n[SUCCESS] .env file updated!")
    print("Now verify with: python verify_keys.py")

if __name__ == "__main__":
    print("=" * 60)
    print("Update .env File with API Keys")
    print("=" * 60)
    print("\nThis script will help you update your .env file.")
    print("You can either:")
    print("  1. Provide keys as command line arguments")
    print("  2. Edit the .env file manually")
    print("\nFor now, I'll show you what needs to be in the file.\n")
    
    # Check if keys provided via command line
    import sys
    if len(sys.argv) > 1:
        openai_key = sys.argv[1] if len(sys.argv) > 1 else None
        sdxl_key = sys.argv[2] if len(sys.argv) > 2 else None
        update_env_file(openai_key, sdxl_key)
    else:
        print("To update via script, run:")
        print("  python update_env_keys.py <OPENAI_KEY> <SDXL_KEY>")
        print("\nOr manually edit .env file with:")
        print("  OPENAI_API_KEY=sk-your-key-here")
        print("  SDXL_API_KEY=sk-your-key-here")


