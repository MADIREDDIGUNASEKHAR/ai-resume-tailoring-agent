# AI Resume Tailoring Agent

An automated pipeline that reads job postings, tailors a candidate's resume for each role using **Groq LLM (Llama3-70B)**, saves individual DOCX files, and dispatches one application email per job.

---

## Why Option 2?

I chose Option 2 because it directly aligns with a real problem I have personally faced while applying for jobs. For every job description, I had to manually edit and tailor my resume before applying, which was time-consuming and repetitive.

Around two months ago, I started building an open-source project called **NextRoundAI** to automate this exact process. Since this assignment closely matches that idea, I decided to go with Option 2 as it reflects both my interest and prior hands-on experience.

---

## Why Groq?

* ⚡ Extremely fast (~2–3 seconds per request)
* 🆓 Generous free tier
* 🧠 High-quality outputs using Llama3 models
* 🔌 Simple OpenAI-style API integration

---

## Project Structure

```
resume-tailoring-agent/
├── main.py                    ← Entry point & orchestration
├── config/
│   └── settings.py            ← Environment variable loader & validator
├── services/
│   ├── parser_service.py      ← Read Excel + JSON, merge into Job objects
│   ├── document_service.py    ← Read/write DOCX resumes
│   ├── llm_service.py         ← Groq API calls with prompt engineering
│   └── email_service.py       ← Gmail SMTP with MIME attachment
├── models/
│   └── job_model.py           ← Job dataclass
├── utils/
│   ├── logger.py              ← Rotating file + console logging
│   └── helpers.py             ← retry decorator, filesystem helpers
├── data/
│   ├── option2_job_links.xlsx
│   ├── option2_jobs.json
│   └── candidate_resume.docx
├── output/
│   └── resumes/
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## Architecture Overview

The project follows a clean modular pipeline:

```
Excel + JSON → Merge Jobs
        ↓
Resume DOCX → Extract Text
        ↓
Groq LLM → Tailored Resume
        ↓
Save DOCX
        ↓
Send Email
```

Each module has a single responsibility, making the system scalable and easy to maintain.

---

## Setup

### 1. Clone / unzip the project

```bash
cd resume-tailoring-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable         | Description                   |
| ---------------- | ----------------------------- |
| `GROQ_API_KEY`   | From https://console.groq.com |
| `EMAIL_USER`     | Your Gmail                    |
| `EMAIL_PASSWORD` | Gmail App Password            |

👉 Generate App Password: https://myaccount.google.com/apppasswords

| Variable       | Value          |
| -------------- | -------------- |
| SMTP_SERVER    | smtp.gmail.com |
| SMTP_PORT      | 587            |
| RECEIVER_EMAIL | Receiver email |
| SENDER_NAME    | Your name      |

⚠️ Gmail requires **App Password**, not normal password.

---

### 5. Add input files

* `option2_job_links.xlsx`
* `option2_jobs.json`
* `candidate_resume.docx`

---

### 6. Run

```bash
python main.py
```

---

## How It Works

```
main.py
  │
  ├─ parse_jobs()
  ├─ read_resume()
  │
  └─ for each Job:
       ├─ tailor_resume()  ← Groq
       ├─ save_resume()
       └─ send_email()
```

---

## Uniqueness Guarantee

Each resume is different because:

* Job-specific keyword extraction
* Prompt engineering with role context
* Reordering skills and experience
* Context-aware rewriting

---

## Error Handling

* Each job runs independently
* Failures don’t stop pipeline
* Retry logic for API & email
* Detailed logging

---

## Output

* 📄 Resumes → `output/resumes/`
* 📝 Logs → console output

---

## Known Issues & Fixes

### ❌ Permission Denied (DOCX)

Cause: File open in Word
Fix: Close file or overwrite/delete before saving

### ❌ Email Authentication Error

Cause: Gmail security
Fix: Use App Password

---

## Assumptions

* Excel & JSON IDs match
* Resume is in DOCX format
* Gmail App Password configured
* Internet access for Groq API

---

## Possible Improvements

| Area          | Improvement             |
| ------------- | ----------------------- |
| Output format | Add PDF support         |
| Parallelism   | Multi-thread processing |
| UI            | Streamlit dashboard     |
| Storage       | Upload to cloud         |
| Testing       | Add unit tests          |
| File handling | Auto-overwrite files    |

---

## Final Overview

“This system automates resume tailoring using a modular pipeline. It combines structured job data with LLM-based content generation using Groq for fast and reliable inference. Each resume is uniquely optimized for ATS by adapting skills, summaries, and experience to match job descriptions.”
