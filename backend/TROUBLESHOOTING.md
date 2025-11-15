# Troubleshooting Guide

## Common Errors and Solutions

### 1. OpenAI API Quota Exceeded (Error 429)

**Error Message:**
```
Error code: 429 - You exceeded your current quota
```

**Solution:**
1. Check your OpenAI account billing: https://platform.openai.com/account/billing
2. Add payment method if needed
3. Upgrade your plan if you've hit usage limits
4. Check your usage dashboard: https://platform.openai.com/usage

**Temporary Workaround:**
- Use a different OpenAI API key with available quota
- Wait for your quota to reset (usually monthly)

### 2. Missing OpenAI API Key

**Error Message:**
```
ValidationError: OPENAI_API_KEY is required
```

**Solution:**
1. Create a `.env` file in the `backend` directory
2. Add: `OPENAI_API_KEY=your_actual_key_here`
3. Get your API key from: https://platform.openai.com/api-keys

### 3. Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'langchain_chroma'`

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Python Version Compatibility

**Error:** Build errors with pandas, tiktoken, or pydantic-core

**Solution:**
- Use Python 3.11 or 3.12 (recommended)
- Python 3.13 has compatibility issues with some packages

```bash
# Install Python 3.11
brew install python@3.11

# Create new venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. PDF Upload Fails

**Possible Causes:**
- Invalid PDF file format
- File too large
- OpenAI API quota exceeded
- Missing dependencies

**Solution:**
- Check the error message in the API response
- Verify PDF file is valid
- Check OpenAI API quota
- Ensure all dependencies are installed

### 6. Vector Store Initialization Fails

**Error:** ChromaDB initialization errors

**Solution:**
- Ensure `chroma_db` directory has write permissions
- Check disk space
- Try deleting `chroma_db` directory and reinitializing

```bash
cd backend
rm -rf chroma_db
# Restart server
```

## Getting Help

1. Check the error message in the API response (now includes full traceback)
2. Review this troubleshooting guide
3. Check OpenAI API status: https://status.openai.com/
4. Review logs in the terminal where uvicorn is running

