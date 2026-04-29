# 🎓 AI-Powered English Learning System (英文學習系統)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![React](https://img.shields.io/badge/React-19.2-61dafb.svg)
![Flask](https://img.shields.io/badge/Flask-API-black.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg)

An interactive, AI-driven web application designed to enhance English proficiency through Spaced Repetition Systems (SRS), scenario-based AI conversations, and gamified learning. This system was developed with strict adherence to **Object-Oriented Analysis and Design (OOAD)** principles.

## 📑 Catalog (Table of Contents)
- [Project Tracking](#project-tracking)
- [System Diagrams](#system-diagrams)
  - [Use Cases](#use-cases)
  - [Activity Diagram: Report Inappropriate Content](#activity-diagram-report-inappropriate-content-workflow)
  - [Architecture Diagram: System Tech Stack & Data Flow](#architecture-diagram-system-tech-stack--data-flow)
  - [Class Diagram: Core System Architecture](#class-diagram-core-system-architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Quick Start (Local Setup)](#quick-start-local-setup)
- [Meet the Team](#meet-the-team)
- [Contact Us](#contact-us)


---

## 🚀 Project Tracking
Curious about our current development progress? 
👉 **[📌 View our latest Checkpoint here!](https://github.com/PeiHsiuLu/oop_teachingsystem/blob/main/Checkpoint.md)**

## 📊 System Diagrams

### Use Cases
We use eight use cases in the project.  

*Use case definition: Describe a whole process (or task) that the user (Actor) who cooperates with the system to attain a goal.*  
  
1. **Manage the account:**   
<img width="682" height="335" alt="image" src="https://github.com/user-attachments/assets/2783505f-4cdc-4761-82ef-93c65b65c186" />

2. **Course arrange:**  
<img width="612" height="381" alt="image" src="https://github.com/user-attachments/assets/4017029a-eb53-4625-81c2-0cb3219459bc" />

3. **Database Build and Training:**  
<img width="799" height="454" alt="image" src="https://github.com/user-attachments/assets/9ae96cb2-21b5-4bef-89ae-95f174141be6" />

4. **Course interaction:**  
<img width="800" height="501" alt="image" src="https://github.com/user-attachments/assets/71c27575-0d69-407f-ae49-fb9cbeb0cf7c" />

5. **Result Analysis:**  
<img width="799" height="471" alt="image" src="https://github.com/user-attachments/assets/662b390b-e6ea-4d03-861e-5f8a4391f0a7" />

6. **Learning by Game:**  
<img width="800" height="613" alt="image" src="https://github.com/user-attachments/assets/46b26a73-4cf4-48dd-aac7-129f2a5e8b6e" />

7. **Team up:**  
<img width="800" height="719" alt="image" src="https://github.com/user-attachments/assets/3cbeb4ea-3543-4bc4-98ed-e80c0027693e" />

8. **Report the fault:**  
<img width="701" height="548" alt="image" src="https://github.com/user-attachments/assets/ea8e1d43-8d7b-4880-93b9-837538aa388f" />
  
 
### 📊 Activity Diagram: Report Inappropriate Content Workflow
<img width="779" height="799" alt="image" src="https://github.com/user-attachments/assets/2273226e-65f4-405a-9ff7-0f1d02d129e5" />   

This diagram illustrates the end-to-end process of our content moderation system, detailing the interactions between the User, the System, and the Administrator.

#### 1. User Interaction Flow
* **Initiation:** The flow begins when a user views content on the platform.
* **Decision:** If the content is deemed acceptable, the user continues browsing normally. 
* **Action:** If the content is deemed inappropriate, the user clicks the "Report" button, selects a specific reason, enters a detailed description, and submits the report.

#### 2. System Processing
* **Storage & Notification:** Once submitted, the system autonomously stores the report data into the database (MongoDB) and sends a notification to the Administrator for review.

#### 3. Administrator Review & Resolution
The Admin reviews the flagged content and makes a decision based on validity and severity:
* **Scenario A: Report is Invalid**
  * The Admin rejects the report.
  * The system notifies the reporter that no action will be taken.
* **Scenario B: Report is Valid (Low/Moderate Severity)**
  * The Admin issues a warning to the content owner.
  * The content remains visible on the platform.
  * The system notifies both the reporter and the content owner of the decision.
* **Scenario C: Report is Valid (High Severity)**
  * The Admin removes the inappropriate content entirely.
  * The system notifies both the reporter and the content owner of the removal action.

### 📊 Architecture Diagram: System Tech Stack & Data Flow
<img width="1597" height="322" alt="image" src="https://github.com/user-attachments/assets/71cd1dcb-eb04-4d6e-ba8f-473e79c15966" />

This diagram illustrates the three-tier architecture of our English Learning System, showing how the frontend, backend, and database interact to deliver a seamless AI-driven experience.

#### 1. Frontend (React)
The client-side is built with React, focusing on a responsive and dynamic user experience:
* **React UI Components:** The visual elements the user interacts with (e.g., flashcards, chat interface).
* **State Management:** Manages the temporary data and UI state (like the current dialogue history or flashcard status) before sending it to the server.
* **API Client (Axios/Fetch):** Acts as the messenger, taking the user's actions and formatting them into requests to send to the backend.

#### 2. Communication Layer (HTTP / JSON)
* Data travels between the React frontend and the Flask backend using standard **HTTP requests**. 
* The payload is formatted as **JSON** (JavaScript Object Notation), ensuring lightweight and fast data transfer.

#### 3. Backend (Flask API)
The server-side is powered by Python and Flask, handling the core logic of the application:
* **API Routing:** Receives incoming HTTP requests and directs them to the correct internal functions.
* **Business Logic:** The brain of the system. It processes the requests (e.g., calculating SRS intervals, managing user scores).
* **AI Object / AI 老師模組 (AI Tutor Module):** A specialized component integrated into the business logic. It handles the dynamic generation of conversational dialogue and scenario-based interactions.

#### 4. Database (MongoDB)
A NoSQL database approach is used for flexible and scalable data storage:
* **PyMongo:** The Python driver used by the backend's Business Logic to seamlessly query and update the database.
* **MongoDB:** The cloud database (Atlas) that stores all persistent data.
* **BSON Documents:** Data is stored in Binary JSON (BSON) format, which perfectly maps to the nested data structures of our users, vocabulary banks, and interaction logs.

### 🧩 Class Diagram: Core System Architecture

Our system is structured using a clean Object-Oriented Analysis and Design (OOAD) approach, dividing the application into Domain Models (Entities), Business Logic (Services/Managers), and a Data Access Layer (Repositories).

#### 1. Domain Models & Entities
<img width="799" height="588" alt="image" src="https://github.com/user-attachments/assets/ef00afff-abe4-4841-839a-3f4f1f1c200c" />  

This section defines the core data structures and their relationships:
* **User Hierarchy:** `User` serves as the base class, extended by `Student` (which tracks XP, levels, and credit scores) and `Admin` (which handles system management).
* **Learning Structure:** A `LearningPath` aggregates multiple `Unit` objects. Each `Unit` is composed of `DialogueNode` objects, which power the branching conversational scenarios.
* **Vocabulary System:** The `VocabularyBank` manages a collection of `Word` objects. Each `Word` tracks critical Spaced Repetition System (SRS) data like `ease_factor`, `interval`, and `next_review_date`.
* **Social & Analytics:** `StudyGroup` aggregates `Student` members to calculate team scores. `InteractionLog` tracks detailed user behavior (time spent, correctness) for later analysis, while `Badge` handles gamified achievements.

#### 2. Business Logic Interfaces (Services & Managers)  
<img width="578" height="414" alt="image" src="https://github.com/user-attachments/assets/8980c365-0acc-43b6-9c30-0d9dcbb2834e" />

These interfaces define the core operations and algorithms of the system, keeping the business logic decoupled from the database and UI:
* **Learning Engines:** 
  * `SRSManager`: Handles the Spaced Repetition algorithms (`schedule_review`, `process_review_result`).
  * `DialogueEngine`: Manages stateful AI chat sessions.
  * `AnalyticsEngine`: Generates weakness reports and calculates learning trends.
* **System Managers:** 
  * `AuthService`: Handles login, registration, and role validation.
  * `GameManager` & `TeamManager`: Process XP events, award badges, and compute team leaderboards.
  * `ModService`: Processes reports for inappropriate content and applies sanctions.

#### 3. Data Access Layer (Repositories)
<img width="798" height="352" alt="image" src="https://github.com/user-attachments/assets/0fb75c1a-644f-41b6-b0b7-b3baad982f26" />

To maintain a clean architecture, database queries (to MongoDB) are abstracted using the Repository Pattern:
* **`BaseRepository`**: An interface defining standard CRUD (Create, Read, Update, Delete) operations (`save`, `find_by_id`, `delete_by_id`).
* **Specific Repositories:** Classes like `UserRepository`, `CourseRepository`, `VocabularyRepository`, `GroupRepository`, and `ReportRepository` inherit from `BaseRepository`. They implement specific database queries (e.g., `get_words_due_for_review` or `get_top_players`) tailored to their respective domains.

## ✨ Key Features

### 🧠 Smart Vocabulary & Analytics (單字庫建立與成效分析)
* **Spaced Repetition System (SRS):** Utilizes the Strategy Pattern to dynamically adjust review intervals based on user memory retention.
* **AI Scenario Generation:** Dynamically generates contextual example sentences.
* **Learning Analytics:** Tracks interaction logs to adjust forgetting curve models and generate weakness reports.

### 🤖 Interactive Course Play (課程互動 & 遊戲式學習)
* **AI Tutor Interface:** Branching dialogue scenarios for realistic conversational practice.
* **Gamification:** Earn XP, level up, and unlock achievements/badges upon completing tasks.
* **Team Leaderboards:** Join study groups and compete on team leaderboards.

### 🛡️ System & Account Management (管理帳號 & 內容審核)
* **Role-Based Access:** Distinct student and admin privileges.
* **Learning Paths:** Sequential unit unlocking based on user progress.
* **Content Moderation:** Built-in reporting system for inappropriate content with admin review workflows.

## 🛠️ Tech Stack
* **Frontend:** React.js (State Management, Axios/Fetch)
* **Backend:** Python / Flask (RESTful API, Business Logic)
* **Database:** MongoDB Atlas (NoSQL BSON Documents via PyMongo)

## 💻 Quick Start (Local Setup)

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/PeiHsiuLu/oop_teachingsystem.git](https://github.com/PeiHsiuLu/oop_teachingsystem.git)
   cd oop_teachingsystem
   ```
2. **Install Backend Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Application:**
   ```bash
   python run.py
   ```
## 👥 Meet the Team
* **呂沛修 (Pei-Hsiu Lu):** Vocabulary Bank Training, Course Interaction, Learning Analytics.
* **高郁城 (Yu-Cheng Kao):** Account Management, Course Scheduling.
* **蔡碩恩 (Shuo-En Tsai):** Gamified Learning, Team Formation, Content Moderation.

## 📞 Contact Us
* **呂沛修 (Pei-Hsiu Lu)'s GitHub:** [View Here!](https://github.com/PeiHsiuLu)  
* **高郁城 (Yu-Cheng Kao)'s GitHub:** [View Here!](https://github.com/leokao960811)  
* **蔡碩恩 (Shuo-En Tsai)'s GitHub:** [View Here!](https://github.com/undertaker233)
