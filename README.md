# 🎓 AI-Powered English Learning System (英文學習系統)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![React](https://img.shields.io/badge/React-19.2-61dafb.svg)
![Flask](https://img.shields.io/badge/Flask-API-black.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg)

An interactive, AI-driven web application designed to enhance English proficiency through Spaced Repetition Systems (SRS), scenario-based AI conversations, and gamified learning. This system was developed with strict adherence to **Object-Oriented Analysis and Design (OOAD)** principles.

## 🚀 Project Tracking
Curious about our current development progress? 
👉 **[📌 View our latest Checkpoint here!](https://github.com/PeiHsiuLu/oop_teachingsystem/blob/main/Checkpoint.md)**

## 📊 System Diagrams

### Use Cases
We use eight use cases in the project.  
*Use case definition: Desribe a whole process (or task) that the user (Actor) who cooperates with the system to attain a goal.*  
  
* Manage the account:   
<img width="682" height="335" alt="image" src="https://github.com/user-attachments/assets/2783505f-4cdc-4761-82ef-93c65b65c186" />
  
* Course arrange:  
<img width="612" height="381" alt="image" src="https://github.com/user-attachments/assets/4017029a-eb53-4625-81c2-0cb3219459bc" />
  
* Database Build and Training:  
<img width="799" height="454" alt="image" src="https://github.com/user-attachments/assets/9ae96cb2-21b5-4bef-89ae-95f174141be6" />
  
* Couse interaction:  
<img width="800" height="501" alt="image" src="https://github.com/user-attachments/assets/71c27575-0d69-407f-ae49-fb9cbeb0cf7c" />
  
* Result Analysis:  
<img width="799" height="471" alt="image" src="https://github.com/user-attachments/assets/662b390b-e6ea-4d03-861e-5f8a4391f0a7" />
  
* Learning by Game:
<img width="800" height="613" alt="image" src="https://github.com/user-attachments/assets/46b26a73-4cf4-48dd-aac7-129f2a5e8b6e" />
  
* Team up:
<img width="800" height="719" alt="image" src="https://github.com/user-attachments/assets/3cbeb4ea-3543-4bc4-98ed-e80c0027693e" />
  
* Report the fault:
<img width="701" height="548" alt="image" src="https://github.com/user-attachments/assets/ea8e1d43-8d7b-4880-93b9-837538aa388f" />
  
  
### Activity Diagram
*(Replace the path below with your actual image file path)*
![Activity Diagram](./images/activity_diagram.png)

### Architecture Diagram
*(Replace the path below with your actual image file path)*
![Architecture Diagram](./images/architecture_diagram.png)

### Class Diagram
*(Replace the path below with your actual image file path)*
![Class Diagram](./images/class_diagram.png)

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
2. Install Backend Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Application:
   ```bash
   python run.py
   ```
## 👥 Meet the Team
* **呂沛修 (Pei-Hsiu Lu):** Vocabulary Bank Training, Course Interaction, Learning Analytics.
* **高郁城 (Yu-Cheng Kao):** Account Management, Course Scheduling.
* **蔡碩恩 (Shuo-En Tsai):** Gamified Learning, Team Formation, Content Moderation.

## 📞 Contact us:
* **呂沛修 (Pei-Hsiu Lu)'s GitHub:** [View Here!](https://github.com/PeiHsiuLu)  
* **高郁城 (Yu-Cheng Kao)'s GitHub:** [View Here!](https://github.com/leokao960811)  
* **蔡碩恩 (Shuo-En Tsai)'s GitHub:** [View Here!](https://github.com/undertaker233)
