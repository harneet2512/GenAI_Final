"""
Quick setup checker - verifies what's needed to run the pipeline.
"""

import os
import sys

def check_setup():
    """Check if setup is complete."""
    print("=" * 60)
    print("Setup Checker")
    print("=" * 60)
    
    issues = []
    
    # Check Python version
    print(f"\n[1] Python version: {sys.version.split()[0]}")
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
        print("   [WARNING] Python version may be too old")
    else:
        print("   [OK] Python version is compatible")
    
    # Check .env file
    print("\n[2] Checking .env file...")
    if os.path.exists('.env'):
        print("   [OK] .env file exists")
        with open('.env', 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY=your_' in content or 'OPENAI_API_KEY=' not in content:
                issues.append("OPENAI_API_KEY not configured in .env")
                print("   [WARNING] OPENAI_API_KEY needs to be set")
            else:
                print("   [OK] OPENAI_API_KEY found")
            
            if 'SDXL_API_KEY=your_' in content or 'SDXL_API_KEY=' not in content:
                issues.append("SDXL_API_KEY not configured in .env")
                print("   [WARNING] SDXL_API_KEY needs to be set")
            else:
                print("   [OK] SDXL_API_KEY found")
    else:
        issues.append(".env file missing - run 'python setup_env.py'")
        print("   [ERROR] .env file not found")
        print("   Run: python setup_env.py")
    
    # Check dependencies
    print("\n[3] Checking dependencies...")
    required = {
        'openai': 'OpenAI API',
        'faiss': 'FAISS vector DB',
        'langgraph': 'LangGraph',
        'sentence_transformers': 'Sentence Transformers (CLIP)',
        'bs4': 'BeautifulSoup',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'tiktoken': 'TikToken',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, name in required.items():
        try:
            if module == 'bs4':
                import bs4
            elif module == 'PIL':
                import PIL
            elif module == 'dotenv':
                import dotenv
            else:
                __import__(module)
            print(f"   [OK] {name}")
        except ImportError:
            missing.append(name)
            print(f"   [ERROR] {name} not installed")
    
    if missing:
        issues.append(f"Missing dependencies: {', '.join(missing)}")
        print(f"\n   Install with: pip install -r requirements.txt")
    
    # Check directory structure
    print("\n[4] Checking directory structure...")
    required_dirs = [
        'data/raw', 'data/processed',
        'scrapers', 'rag_pipeline', 'analysis',
        'image_generation', 'agent_workflow', 'report'
    ]
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   [OK] {dir_path}/")
        else:
            issues.append(f"Directory missing: {dir_path}")
            print(f"   [ERROR] {dir_path}/ not found")
    
    # Summary
    print("\n" + "=" * 60)
    if issues:
        print("SETUP INCOMPLETE - Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\nSee SETUP_CHECKLIST.md for detailed instructions.")
        return False
    else:
        print("SETUP COMPLETE - Ready to run!")
        print("\nNext step: python main.py --all")
        return True

if __name__ == "__main__":
    check_setup()


