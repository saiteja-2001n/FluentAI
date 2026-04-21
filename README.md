# 🎙️ FluentAI — AI-Based Speech Analysis System

FluentAI is an end-to-end AI-powered platform that analyzes speech recordings and converts them into structured communication insights. It evaluates key speaking skills such as fluency, clarity, confidence, grammar, and pronunciation, and presents results through interactive dashboards and downloadable reports.

---

## 🚀 Features

* 🎧 Upload and analyze speech recordings
* 📝 Automatic speech-to-text transcription using Whisper
* 📊 Communication skill scoring (Fluency, Clarity, Confidence, Grammar, Pronunciation)
* 📈 Interactive visualizations (Radar & Pie charts)
* 📄 Auto-generated PDF reports with feedback
* 🔔 Notification system for completed analysis
* 🗂️ Session-based tracking and history

---

## 🧠 Problem Statement

Manual speech evaluation is:

* Subjective
* Time-consuming
* Not scalable

FluentAI solves this by providing **automated, consistent, and scalable speech evaluation**.

---

## 💡 Solution

FluentAI uses an AI-driven pipeline to:

1. Process audio input
2. Convert speech to text
3. Analyze communication patterns
4. Generate structured scores and insights
5. Present results visually and via reports

---

## 🏗️ System Architecture

```
Frontend (Streamlit)
        ↓
Backend (FastAPI APIs)
        ↓
Speech Pipeline (Transcription + Processing)
        ↓
Scoring Engine (Evaluation Logic)
        ↓
Database (MySQL)
        ↓
Reports & Visualization
```

---

## 🔄 Workflow

1. User uploads audio
2. Backend stores file and creates session
3. Audio is processed through speech pipeline
4. Transcription is generated
5. Scoring engine evaluates communication skills
6. Results are stored in database
7. Dashboard displays analytics
8. PDF report is generated

---

## 🧰 Tech Stack

### 🔹 Backend

* FastAPI
* SQLAlchemy (ORM)
* MySQL

### 🔹 Frontend

* Streamlit
* Plotly

### 🔹 AI / ML

* Whisper (Speech Recognition)
* Rule-based Scoring Engine

### 🔹 Others

* ReportLab (PDF generation)

---

## 📊 Scoring Parameters

* **Fluency** → Speech rate & pauses
* **Clarity** → Vocabulary & sentence structure
* **Confidence** → Consistency & filler words
* **Grammar** → Rule-based validation
* **Pronunciation** → Model confidence

---

## 📁 Project Structure

```
FluentAI/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── crud.py
│   ├── routers.py
│   ├── speech_pipeline.py
│   ├── scoring_engine.py
│   └── ...
│
├── frontend/
│   ├── app.py
│
├── requirements.txt
├── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/FluentAI.git
cd FluentAI
```

---

### 2️⃣ Setup Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

---

### 3️⃣ Setup Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 📌 API Endpoints

* `/upload` → Upload audio
* `/sessions` → Get all sessions
* `/sessions/{id}/scores` → Get scores
* `/sessions/{id}/segments` → Get transcript
* `/reports/{id}/pdf` → Download report
* `/notifications` → Get notifications

---

## ⚡ Key Highlights

* Modular architecture
* Scalable design
* Real-world AI pipeline integration
* End-to-end system (UI + Backend + AI)

---

## ⚠️ Limitations

* Heuristic-based scoring
* Performance depends on audio quality
* Limited real-time processing

---

## 🚀 Future Improvements

* LLM-based feedback generation
* Real-time speech analysis
* Multi-language support
* Enhanced ML-based scoring

---

## 👨‍💻 Author

**Sai Teja Goud**
AI/ML Enthusiast

---

## ⭐ Conclusion

FluentAI demonstrates how AI, backend engineering, and data visualization can be combined to build a scalable speech intelligence system.
