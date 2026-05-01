# 🎓 Audio NLP: Generative AI-Powered Learning Platform

## 📌 Overview

Audio NLP is an AI-powered Learning Management System (LMS) that transforms spoken lectures into structured educational content. It automates the process of generating lecture notes and quizzes from audio recordings, reducing manual effort for educators and enhancing student learning experience.

This system is based on advanced **Generative AI + NLP + Speech Recognition** technologies.

---

## 🚀 Key Features

### 👨‍🏫 Teacher Panel

* 🎙️ Record multiple audio lectures per session
* 🧠 Generate structured notes using AI
* 📝 Automatically generate MCQ-based quizzes using NLP
* ✏️ Edit notes and quizzes manually
* 📊 View student performance analytics
* 📅 Schedule quizzes with deadlines

### 🎓 Student Panel

* 📄 Access AI-generated lecture notes
* 🧪 Attempt quizzes with time limits
* ⏱️ Auto-submission after deadline
* 📊 View performance reports
* 🔔 Receive real-time notifications

---

## ⚙️ System Architecture

### 🔄 Core Pipelines

#### 1. Audio Processing Pipeline

Audio Input → Chunking → Transcription → Storage

#### 2. Notes Generation Pipeline

Transcript → AI Summarization → Structured Notes → Export

#### 3. Quiz Generation Pipeline

Notes → NLP Processing → MCQ Generation → Scheduling

---

## 🌍 Multi-Language Support

* Supports **multi-language audio input** (Urdu, French, English, etc.)
* Powered by Whisper for robust transcription across languages
* All generated **notes are standardized in English** for consistency
* Enables cross-language learning and accessibility

---

## 📂 File Handling & Storage System

The system includes a **production-level file handling mechanism** designed for scalability, reliability, and incremental processing.

### 🔹 Incremental Audio Storage

* Each lecture can have **multiple recordings**
* Files follow a structured naming convention:

  * `course_section_lecture_recordingNumber`
* Prevents overwriting and maintains sequence integrity

### 🔹 Audio Chunking

* Large audio files are split into **~20MB chunks**
* Ensures efficient processing with Whisper
* Improves performance and avoids memory issues

### 🔹 Queue-Based Processing

* Separate processing queues:

  * 🎙️ Recording Queue
  * 🧠 Notes Queue
  * 📝 Quiz Queue
* Background workers process tasks **incrementally (FIFO)**

### 🔹 Transcript Handling

* Each chunk is transcribed independently
* Transcripts are **incrementally merged**
* Final combined transcript used for summarization

### 🔹 Notes File Management

* Notes are stored in:

  * 📄 DOCX (editable)
  * 📑 PDF (read-only)
* Teachers can download, edit, and re-upload
* System automatically **syncs and updates versions**

### 🔹 Data Integrity

* Incremental processing ensures **no data loss**
* Versioning avoids overwrite conflicts
* Database sync maintains consistency

---

## 🧠 Tech Stack

### 🔧 Backend

* FastAPI 

### 🤖 AI & NLP

* OpenAI GPT (Summarization & Quiz Generation)
* Whisper AI (Speech-to-Text)
* spaCy (Text Processing)

### 🗄️ Database

* MySQL

### 🔔 Notifications

* Email-based alerts system

---


## ▶️ Usage

1. Login as Teacher
2. Create Course
3. Upload / Record Audio Lecture
4. Generate Notes
5. Generate Quiz
6. Schedule Quiz

Students can:

* View notes
* Attempt quizzes
* Track performance

---

## 📊 Results (From Research)

* ⏱️ 70% reduction in manual workload
* 📝 87.5% relevance in generated notes
* 🎯 80% accuracy in quiz content

---

## 💡 Why This Project Matters

* Automates educational content creation
* Improves student engagement
* Scalable for large institutions
* Real-world AI application (NLP + Generative AI)

---

## 🔮 Future Improvements

* Real-time lecture transcription
* AI-based performance prediction
* Mobile application (Flutter / React Native)
* Advanced multi-language output support


