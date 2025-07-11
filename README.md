# AI-Powered Insurance Claim Automation

## Project Overview
This application automates the initial processing of insurance claims using AI. Users upload a hospital receipt and an insurance policy document. The system extracts, parses, and matches the data to determine claim eligibility and provides a clear explanation and estimated payout.

---

## Features
- **Document Upload:** Upload hospital receipt and insurance policy (PDF, PNG, JPG).
- **OCR & Text Extraction:** Extracts text using Tesseract OCR.
- **LLM-Assisted Parsing:** Uses Google Gemini (via LangChain) to extract structured data.
- **Intelligent Matching:** Matches receipt services to policy coverage, exclusions, deductibles, co-pays, and limits.
- **Claim Decision:** Determines eligibility, calculates payout, and provides human-readable explanations.
- **User Interface:** Simple Streamlit web app for uploads and results.

---

## Technology Stack
- **Frontend:** Streamlit
- **Backend:** Python
- **LLM:** Google Gemini API (via LangChain)
- **OCR:** pytesseract, Pillow, pdf2image
- **Containerization:** Docker

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo-url>
cd ai-insurance-claim
```

### 2. Environment Variables
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your-google-api-key-here
```

### 3. Local Development (without Docker)
#### Install Tesseract OCR
- **macOS:**
  ```bash
  brew install tesseract
  ```
- **Ubuntu/Debian:**
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils
  ```

#### Set up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Run the App
```bash
streamlit run app/app.py
```

---

### 4. Docker Deployment
#### Build the Docker Image
```bash
docker build -t ai-insurance-claim .
```
#### Run the Container
```bash
docker run --env-file .env -p 8501:8501 ai-insurance-claim
```

---

## Usage
1. Open your browser to [http://localhost:8501](http://localhost:8501)
2. Upload a hospital receipt and an insurance policy document (PDF, PNG, JPG).
3. Click **Process Claim**.
4. Review the extracted data, claim summary, breakdown, and explanations.
5. Use **New Claim** to start over.

---

## Notes & Recommendations
- **OCR Accuracy:** For best results, upload clear, high-quality scans.
- **LLM API Key:** You must have a valid Google Gemini API key.
- **Security:** This is a prototype. For production, ensure compliance with data privacy regulations (e.g., HIPAA).
- **Extensibility:** The code is modular for easy extension (e.g., cloud OCR, more advanced LLM logic).

---

## File Structure
```
ai-insurance-claim/
  app/
    app.py                # Streamlit frontend
  utils/
    ocr_processor.py      # OCR logic
    data_parser.py        # LLM parsing
    claim_processor.py    # Claim logic
  requirements.txt
  Dockerfile
  .env
  README.md
```

---

## Troubleshooting
- **Tesseract Not Found:** Ensure Tesseract is installed and in your PATH.
- **Google API Errors:** Check your API key and quota.
- **PDF Extraction Issues:** Ensure `poppler-utils` is installed for PDF support.

---

## License
MIT License 