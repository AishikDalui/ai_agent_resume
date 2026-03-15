## Data Analyst Portfolio with AI Chat

This project is a **data analyst portfolio website** with a built-in **"Chat with me"** feature.

- **Frontend**: Static HTML/CSS/JavaScript
- **Backend**: FastAPI (Python)
- **LLM**: Google Gemini API (answers questions based on a PDF, e.g. your resume or case study)
- **Storage**: User `name`, `email`, and `phone` are logged to a Google Sheet

### Features

- **Portfolio site** with sections for About, Skills, Projects, and Contact.
- **Chat with me flow**:
  1. User clicks the **Chat with me** button.
  2. User submits **name, email, and phone number**.
  3. Backend generates and "sends" a one-time password (OTP) (email/SMS sending is stubbed for now).
  4. User enters OTP to verify.
  5. On success, backend:
     - Persists user details to **Google Sheets**.
     - Returns a short-lived **access token** used to access the chat API.
  6. User accesses a **chat screen** where messages are answered by **Google Gemini** using the configured PDF as context.

### Tech Stack

- **Backend**
  - FastAPI
  - Uvicorn (for local dev)
  - Pydantic
  - `python-dotenv` for environment variables
  - Google Gemini client (`google-generativeai`)
  - Google Sheets API client (`gspread` or `google-api-python-client`)

- **Frontend**
  - Pure HTML/CSS/JavaScript (no build step required)
  - Fetch-based API calls to the FastAPI backend

### Project Structure

```text
ai_agent_resume/
  backend/
    main.py
    auth.py
    chat.py
    config.py
    google_sheets.py
    pdf_loader.py
    models.py
    requirements.txt
  frontend/
    index.html
    styles.css
    app.js
  .env.example
  README.md
```

### Environment Variables

Copy `.env.example` to `.env` in the project root and fill in the values:

- `GEMINI_API_KEY`: Your Google Gemini API key.
- `PDF_PATH`: Absolute or relative path to the PDF used as context (e.g. your resume).
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to the Google service account JSON file for Sheets access.
- `GOOGLE_SHEETS_SPREADSHEET_ID`: ID of the Google Sheet where user info should be stored.
- `JWT_SECRET_KEY`: Secret key for signing JWT tokens.
- `JWT_ALGORITHM`: Algorithm for JWT, e.g. `HS256`.

### Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will run on `http://127.0.0.1:8000` by default.

### Running Background Jobs

Delayed resume emails, booking confirmation emails, and auto-calls are queued through Celery.
Start Redis first, then run a Celery worker:

```bash
cd backend
celery -A celery_app.celery_app worker --loglevel=info
```

By default Celery expects Redis at `redis://127.0.0.1:6379/0`. Override with
`CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env` if needed.

### Running the Frontend

For local development you can:

- Open `frontend/index.html` directly in the browser, or
- Serve `frontend/` via a simple static server (e.g. `python -m http.server 8080` from the `frontend` folder).

Make sure the frontend JavaScript points to the correct backend URL (by default `http://127.0.0.1:8000`).


### Docker Deployment

The project can now run with Docker Compose using four services:

- `frontend`: Next.js app on port `3000`
- `backend`: FastAPI app on port `8000`
- `redis`: broker/backend for Celery
- `worker`: Celery worker for resume emails and voice-call jobs

Start everything with:

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/health`

Notes:

- SQLite data is persisted through the mounted `backend/data/` folder.
- The worker uses `--concurrency=1`, which fits a small VPS well.
- Keep your production `.env` values updated before deployment, especially `PUBLIC_BACKEND_URL`.

### Notes

- OTP sending is implemented as a **stub** (it logs the OTP on the backend). To go to production, integrate a real email or SMS provider.
- Google Sheets access requires you to configure a **service account** and share the sheet with that account.
- Gemini-based answers are grounded in the PDF you provide. Replace the sample PDF path with your own resume, portfolio, or case study.
