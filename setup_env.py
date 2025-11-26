"""
Helper script to create .env file from template.
"""

import os
import shutil

def setup_env():
    """Create .env file from template if it doesn't exist."""
    if os.path.exists('.env'):
        print("[OK] .env file already exists")
        return
    
    if os.path.exists('.env.template'):
        shutil.copy('.env.template', '.env')
        print("[OK] Created .env file from template")
        print("  Please edit .env and add your API keys:")
        print("    - OPENAI_API_KEY")
        print("    - SDXL_API_KEY")
    else:
        # Create .env file directly
        with open('.env', 'w') as f:
            f.write("# OpenAI API Key for DALL·E 3 and embeddings\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
            f.write("# SDXL API Key (Stability AI or compatible)\n")
            f.write("SDXL_API_KEY=your_sdxl_api_key_here\n")
        print("[OK] Created .env file")
        print("  Please edit .env and add your API keys")

if __name__ == "__main__":
    setup_env()

