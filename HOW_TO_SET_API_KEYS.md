# How to Set Your API Keys

## Quick Instructions

1. **Open the `.env` file** in the project root directory
   - It should be at: `C:\Users\Lenovo\OneDrive\Desktop\GenAI_Final\.env`

2. **Replace the placeholder values** with your actual API keys

3. **The file should look exactly like this** (with your real keys):

```
OPENAI_API_KEY=sk-proj-abc123xyz...
SDXL_API_KEY=sk-1234567890abcdef...
```

## Important Notes

- **No quotes** around the values
- **No spaces** around the `=` sign
- Each key on a **separate line**
- **Save the file** after editing

## Example

**WRONG:**
```
OPENAI_API_KEY = "sk-abc123"    ❌ (has spaces and quotes)
OPENAI_API_KEY=your_openai_api_key_here    ❌ (still placeholder)
```

**CORRECT:**
```
OPENAI_API_KEY=sk-proj-abc123xyz789    ✅
SDXL_API_KEY=sk-1234567890abcdef    ✅
```

## Verify Your Keys

After editing, run:
```bash
python verify_keys.py
```

This will tell you if your keys are properly configured.

## Get Your API Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-` or `sk-proj-`)
5. Paste it in `.env` file

### SDXL API Key (Stability AI)
1. Go to: https://platform.stability.ai/
2. Sign in or create account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key
6. Paste it in `.env` file

**Alternative:** If using a different SDXL provider (like Replicate), you may need to update `image_generation/sdxl_generator.py` with the correct API endpoint.

## Still Having Issues?

If you're having trouble:
1. Make sure the `.env` file is in the project root (same folder as `main.py`)
2. Check that there are no hidden characters or encoding issues
3. Try deleting the `.env` file and creating a new one with just:
   ```
   OPENAI_API_KEY=your-key-here
   SDXL_API_KEY=your-key-here
   ```


