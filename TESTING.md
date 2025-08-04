# Integration Testing Guide for case_in.py

This guide provides comprehensive instructions for running integration tests for the case_in.py Firebase function using real Gemini API calls and Firebase emulators.

## Overview

The test suite validates the complete data ingestion pipeline:
- PDF processing with real Gemini API calls
- Firestore integration with emulators
- Data extraction accuracy for trademark cases
- Vector search preparation with embeddings

## Prerequisites

1. **Python 3.8+** installed
2. **Firebase CLI** installed globally
3. **Gemini API Key** from Google AI Studio
4. **Test PDF files** in `data/case_pdfs/`

## Setup Instructions

### 1. Install Dependencies

```bash
cd functions
pip install -r requirements.txt
```

### 2. Configure Environment

Create `functions/.env` file:
```bash
cp functions/.env.test functions/.env
```

Edit `functions/.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Start Firebase Emulators

From the project root:
```bash
firebase emulators:start --only firestore,storage,auth
```

Or use the automated test runner:
```bash
cd functions
python test_runner.py
```

## Test Structure

### Test Files
- `functions/test_case_in.py` - Main integration test suite
- `functions/test_runner.py` - Automated test runner with emulator management
- `functions/.env.test` - Test environment template

### Test Cases

1. **PDF Processing Tests**
   - `test_extract_case_reference_from_filename()` - Validates filename parsing
   - `test_extract_full_text_from_pdf()` - Tests PDF text extraction
   - `test_create_heading_aware_chunks()` - Validates chunking strategy

2. **AI Integration Tests**
   - `test_extract_structured_data_real_gemini()` - Tests Gemini API calls
   - `test_generate_embeddings()` - Validates embedding generation

3. **Firestore Integration**
   - `test_firestore_integration()` - Tests Firestore storage
   - `test_complete_pipeline()` - End-to-end integration

4. **Data Validation**
   - Individual case validation for each PDF

## Running Tests

### Method 1: Using Test Runner (Recommended)
```bash
cd functions
python test_runner.py
```

### Method 2: Manual with Running Emulators
```bash
# Terminal 1: Start emulators
firebase emulators:start --only firestore,storage,auth

# Terminal 2: Run tests
cd functions
python -m pytest test_case_in.py -v
```

### Method 3: Specific Test Cases
```bash
# Run only PDF processing tests
python -m pytest test_case_in.py::TestCaseInIntegration::test_extract_full_text_from_pdf -v

# Run only integration tests
python -m pytest test_case_in.py::TestIntegration -v
```

## Test Data

The test suite uses these PDF files:
- `data/case_pdfs/Barking Brains LTD.pdf` - O/0060/24
- `data/case_pdfs/Bug Off.pdf` - O/0950/24
- `data/case_pdfs/CM Games.pdf` - O/0958/24
- `data/case_pdfs/DREAM RITE.pdf` - O/0702/24
- `data/case_pdfs/JOLLY PECKISH.pdf` - O/0703/24

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google AI Studio API key | Required |
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator host | localhost:8080 |
| `FIREBASE_AUTH_EMULATOR_HOST` | Auth emulator host | localhost:9099 |
| `FIREBASE_STORAGE_EMULATOR_HOST` | Storage emulator host | localhost:9199 |

## Emulator Configuration

The Firebase emulators are configured in `firebase.json`:
- **Firestore**: localhost:8080
- **Storage**: localhost:9199
- **Auth**: localhost:9099
- **UI**: localhost:4000

## Test Output

Tests produce:
- **Console logs** with detailed progress information
- **Firestore emulator data** in `.firestore_export`
- **Storage emulator data** in `.storage_export`
- **Coverage reports** (when using pytest-cov)

## Validation Criteria

Each test validates:

1. **PDF Processing**
   - Text extraction accuracy
   - Case reference identification
   - Chunking strategy effectiveness

2. **AI Extraction**
   - Structured data completeness
   - Field accuracy validation
   - Embedding generation

3. **Firestore Storage**
   - Document structure
   - Chunk organization
   - Embedding storage

## Troubleshooting

### Common Issues

1. **Emulator Connection Issues**
   ```bash
   # Check if emulators are running
   netstat -an | grep :8080
   ```

2. **Gemini API Key Issues**
   ```bash
   # Verify API key
   echo $GEMINI_API_KEY
   ```

3. **PDF File Not Found**
   ```bash
   # Check test data
   ls -la data/case_pdfs/
   ```

### Debug Mode

Enable debug logging:
```bash
python -m pytest test_case_in.py -v --log-cli-level=DEBUG
```

## CI/CD Integration

For automated testing in CI/CD:

```yaml
# Example GitHub Actions workflow
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install Firebase CLI
        run: npm install -g firebase-tools
      
      - name: Install dependencies
        run: |
          cd functions
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          cd functions
          python test_runner.py
```

## Performance Notes

- **Test Duration**: ~2-5 minutes per PDF (depending on size)
- **API Rate Limits**: 60 requests/minute for Gemini API
- **Emulator Performance**: Suitable for development, not production load
- **Memory Usage**: ~500MB-1GB during testing

## Security Considerations

- **API Keys**: Never commit actual API keys
- **Test Data**: Use anonymized/synthetic data when possible
- **Emulator Data**: Reset between test runs
- **Network**: Tests use local emulators, no external network calls except Gemini API