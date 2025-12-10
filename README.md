# TTB Label Verifier

A web app that verifies alcohol beverage labels by comparing form data with text extracted from label images using OCR. Simulates the TTB label approval process.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Tesseract OCR

**Install Tesseract:**
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

### Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python3 app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```
Runs on `http://localhost:3000` (opens automatically)

## How It Works

1. User fills out form with product info (brand name, product type, alcohol %, etc.)
2. User uploads label image
3. Backend uses Tesseract OCR to extract text from image
4. Backend compares extracted text with form fields
5. Results show which fields match/mismatch

## Tech Stack

- **Frontend:** React 
- **Backend:** Flask 
- **OCR:** pytesseract 

## Approach & Decisions

### Why Tesseract OCR?
I went with Tesseract  because:
- It's free and open source
- Works offline (no API keys needed)
- Good enough for clear text on labels
- Simple to integrate

The tradeoff is accuracy 

### Matching Strategy
I made the matching somewhat forgiving because OCR isn't perfect:

- **Normalization:** Everything lowercased, extra spaces removed. "OLD TOM" matches "Old Tom"
- **Partial matching:** For multi-word fields, if 70% of words match, it counts. Handles OCR missing a word
- **Tolerance:** Alcohol content allows ±0.5% difference. OCR might read "45.2%" as "45%"
- **Flexible volume:** "750ml", "750 mL", "750ML" all match

### Why Flask?
Flask is simple and lightweight. For a single endpoint API, it's perfect. 

### Why React?
Standard choice for modern web apps. Component-based, good state management with hooks, easy to build interactive UIs.

## Known Limitations

1. **OCR accuracy:** Works best with clear, high-res images. Fancy fonts, curved text, or low contrast can cause issues.

2. **Text extraction:** OCR just extracts text - doesn't understand context. Can't tell if "45%" is alcohol content or something else, just looks for patterns.

3. **No database:** Doesn't save verification history. Each verification is independent.

4. **Single image:** Only processes one image at a time, no batch processing.

5. **Matching logic:** Partial matching might give false positives.

## Project Structure

```
backend/
  app.py              # Flask server, OCR processing, verification logic
  requirements.txt    # Python dependencies

frontend/
  src/
    App.js           # Main React component
    App.css          # Styles
  public/
    index.html       # HTML template
```

## API

**POST `/api/verify`**
- Body: multipart/form-data with image file and form fields
- Returns: JSON with verification results

**GET `/api/health`**
- Returns: `{"status": "healthy"}`

## Testing

There's a `sample_label.png` in the project root. Try it with:
- Brand Name: `Old Tom Distillery`
- Product Class: `Kentucky Straight Bourbon Whiskey`
- Alcohol Content: `45%`
- Net Contents: `750 mL`

## Troubleshooting

**OCR not reading text:**
- Image might be too blurry
- Try a clearer image with better contrast
- PNG usually works better than JPEG


**Tesseract not found:**
- Make sure Tesseract is installed and in your PATH

## What I'd Improve

If I had more time:
- Better error handling and more specific error messages
- Database to store verification history
- Batch processing for multiple labels
- Highlight extracted text regions on the image
- User authentication and sessions


## Notes

- Backend runs on port 5001 (not 5000) because macOS uses 5000 for AirPlay
- No environment variables required - everything is hardcoded for simplicity
- CORS is enabled to allow frontend (port 3000) to call backend (port 5001)
