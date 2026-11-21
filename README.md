# HAKIM

HAKIM is a multilingual medical and scientific research assistant with language support for Arabic, Hebrew, English, French, German, and Spanish.

## Features currently implemented
- Europe PMC literature search
- Open-access filtering
- 5, 10, or 20 result options
- Titles, authors, journals, years, abstracts, DOI, and PMID links
- Health endpoint at `/api/health`

## Safety
HAKIM is not a medical device. It does not provide diagnosis or treatment recommendations. Clinical decisions require licensed professional review.

## Run locally
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Render
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
