# CHECKPOINT: English Learning System (OOAD Project)

This document outlines the current state of development for the English Learning System, focusing on the backend architecture and server-rendered UI for three primary use cases: Vocabulary Bank & Training, Course Interaction, and Analytics.
It also serves as a log for file functions and recent modifications.

## 1. File Directory & Functions

This section details the purpose of each file within the current project structure.

### Core Application
-   `run.py`: The main entry point for the Flask application. It imports the app factory and runs the development server.
-   `config.py`: Contains application configuration, primarily the connection URI for the MongoDB Atlas database.
-   `app/__init__.py`: The application factory (`create_app`). It initializes the Flask app, connects to the database, registers all blueprints (routes), and sets up Flask-Login.

### `app/models/` - Data Schema Layer
Defines the BSON document structures for MongoDB using `mongoengine`.
-   `user.py`: Defines the `User`, `Admin`, and `Student` models using polymorphic inheritance.
-   `vocabulary.py`: Defines the `Word` (with SM-2 SRS logic) and `VocabularyBank` schemas for student vocabulary management (UC3).
-   `course.py`: Defines schemas for `LearningPath`, `Chapter`, and `Unit`.
-   `dialogue.py`: Defines the `DialogueNode` and `DialogueOption` schemas for building interactive conversation trees.
-   `analytics.py`: Defines the `InteractionLog` schema for recording user behavior, correctness, and time spent (UC4_2).
-   `team.py`: Defines the `StudyGroup` schema for students to create and join teams (UC7).

### `app/repositories/` - Data Access Layer
Abstracts database interactions, separating business logic from data persistence logic.
-   `base_repository.py`: An abstract base class providing a common interface for all repositories (e.g., `save`, `find_by_id`).
-   `user_repository.py`: Handles database operations for `User` documents.
-   `course_repository.py`: Handles database operations for `LearningPath` and `Chapter` documents.
-   `vocabulary_repository.py`: Uses MongoDB Aggregation pipelines to efficiently query words due for review.

### `app/services/` - Business Logic Layer
Contains the core business logic and orchestrates operations between different components.
-   `auth_service.py`: Manages user registration, login, logout, and role validation.
-   `course_service.py`: Manages the creation of learning paths and their components.
-   `vocabulary_service.py`: Handles dynamic sentence generation and atomic database updates for SRS reviews (UC3).
-   `srs_manager.py`: Analyzes `InteractionLogs` to generate weakness reports and review strategies (UC5).
-   `dialogue_engine.py`: Handles stateful traversal of dialogue nodes and saves interaction logs upon completion (UC4).
-   `team_service.py`: Handles the logic for creating teams and checking membership restrictions (UC7).
-   `game_observer.py`: Implements the **Observer Pattern** to automatically grant XP to students when tasks are completed (UC6).

### `app/routes/` - Presentation & API Layer
Contains Flask Blueprints that define the application's URLs (routes) and connect them to backend logic. This layer also includes the UI templates and components.
-   `main.py`: Defines the route for the main home page (`/`).
-   `auth.py`: Defines routes for user authentication (`/register`, `/login`, `/logout`).
-   `course.py`: Defines routes for course management.
-   `vocabulary_api.py`: Exposes endpoints for seeding data and submitting SRS reviews.
-   `dialogue_api.py`: Exposes endpoints to start scenarios and make dialogue choices.
-   `analytics_api.py`: Exposes endpoints to fetch weakness reports.
-   `team_api.py`: Exposes endpoints to create and join study groups.

#### HTML Templates (Server-Rendered UI)
-   `base.html`: Main layout featuring navigation links.
-   `student_dashboard.html`: Unified dashboard displaying Gamification stats, Vocabulary Review, Course Interaction, and Result Analysis.
-   `student_course.html`: Dedicated view for Learning Paths and Chapters.
-   `student_dialogue.html`: Interactive chat UI for scenario practice.
-   `student_analytics.html`: UI for displaying the weakness report and review strategy.
-   `student_teams.html`: UI for viewing, joining, and creating study groups.

### `app/utils/` - Utilities
-   `decorators.py`: Custom decorators for route protection (`@role_required`) and browser caching prevention (`@no_cache`).

---

## 2. Component Cooperation (System Flow)

This section describes the end-to-end data flow for key use cases.

### Flow 1: Student Vocabulary Review (SRS)
This flow demonstrates the **Vocabulary Bank & Training** and **Analytics** use cases working together.

1.  **Request:** A logged-in student clicks "Start Review" on the home page (`index.html`), sending a `GET` request to `/srs/review/next`.
2.  **Routing:** The request is handled by `get_next_review_word` in `app/routes/srs.py`.
3.  **Business Logic (SRS):** The route calls `srs_manager.get_words_for_review()`. The `SRSManager` (`srs_service.py`) queries the database via the `WordRepository` to find words that are due for review.
4.  **Data Access:** The `WordRepository` (`word_repository.py`) executes a `find` query on the `review_items` collection in MongoDB.
5.  **Response (Render):** The route receives the word data and renders the `review_card.html` template, passing the word information to it.
6.  **User Interaction:** The student views the flashcard, reveals the answer, and clicks a performance button ("Forgot", "Hard", "Easy"). This submits an HTML form via a `POST` request to `/srs/review`.
7.  **Business Logic (Update & Analytics):**
    *   The `submit_review` route in `srs.py` is triggered.
    *   It calls `srs_manager.process_review_result()`. The `SRSManager` delegates the complex calculation to its configured strategy (`SuperMemo2Strategy`), which computes the new `due_date`, `interval`, and `ease_factor`. The result is saved to the `review_items` collection.
    *   The route then calls `analytics_engine.log_event()`. The `AnalyticsEngine` (`analytics_service.py`) creates a new `InteractionLog` document and saves it to the `interaction_logs` collection.
8.  **Redirect:** The user is redirected back to `/srs/review/next` to get the next card, completing the loop.

### Flow 2: Admin Word Management
This flow demonstrates the **Vocabulary Bank & Training** (management side) use case.

1.  **Request:** A logged-in admin clicks "Manage Words" on the home page, sending a `GET` request to `/word/admin/words/manage`.
2.  **Routing:** The request is handled by `manage_words` in `app/routes/word.py`, which is protected by the `@admin_required` decorator.
3.  **Business Logic:** The route calls `word_service.get_all_words()` (`word_service.py`).
4.  **Data Access:** The service calls the `WordRepository` to fetch all documents from the `words` collection in MongoDB.
5.  **Response (Render):** The route renders the `admin_words.html` template, passing the list of existing words to be displayed in a table.
6.  **User Interaction:** The admin fills out the "Add New Word" form and clicks "Submit". This sends a `POST` request to the same URL (`/word/admin/words/manage`).
7.  **Business Logic (Create):** The `manage_words` route now handles the `POST` request. It calls `word_service.add_word()`, which creates a new `Word` object and saves it to the database via the `WordRepository`.
8.  **Redirect:** The user is redirected back to the `manage_words` page, where the new word now appears in the table.

---

## 3. Design Patterns Applied

The project adheres to several key Object-Oriented Analysis and Design (OOAD) principles.

-   **Strategy Pattern:** This is the cornerstone of the Spaced Repetition System.
    -   **File:** `app/services/srs_service.py`
    -   **Implementation:** The `SRSManager` (Context) is configured with an object that conforms to the `SRSAlgorithmStrategy` interface. `SuperMemo2Strategy` is a concrete implementation. This design allows the SRS algorithm to be changed (e.g., to a new `SM-5` strategy) without modifying the `SRSManager` or the routes that use it.

-   **Repository Pattern:** Used to decouple the business logic from the data persistence mechanism.
    -   **Files:** All files in `app/repositories/`.
    -   **Implementation:** Services (e.g., `SRSManager`, `WordService`) do not interact with `mongoengine` or the database directly. They communicate exclusively through repository methods (e.g., `word_repo.get_review_item()`). This makes the code easier to test and allows the database technology to be swapped with minimal changes to the business logic.

-   **Factory Pattern (Application Factory):** Used to create and configure the Flask application instance.
    -   **File:** `app/__init__.py`
    -   **Implementation:** The `create_app()` function encapsulates the entire setup process, making the application more modular and easier to test or deploy in different configurations.

-   **Observer Pattern:** Used to trigger secondary actions without tightly coupling systems.
    -   **File:** `app/services/game_observer.py`
    -   **Implementation:** `GamificationObserver` listens for events (like completing a dialogue or vocabulary review) from the `DialogueEngine` and `VocabularyService` to automatically award XP to the student, separating learning logic from game logic.

---

## 4. Detailed Modifications Log

The following outlines how key files were recently modified to achieve the current system state.

### `app/__init__.py`
- **Modification:** Added `register_blueprint` statements for `vocabulary_bp`, `dialogue_bp`, `analytics_bp`, and `team_bp`.
- **Reason:** Required to make the new APIs accessible to the Flask application.

### `app/routes/course.py`
- **Modification:** Updated the root `/` route to automatically redirect logged-in students to `/student/dashboard`. Separated the dashboard route from the course listing route (`/student/courses`). Applied the `@no_cache` decorator to the dashboard.
- **Reason:** Improves UX by providing a dedicated dashboard home screen, and prevents browser caching issues during development.

### `app/utils/decorators.py`
- **Modification:** Added a `@no_cache` decorator. Updated `@role_required` to evaluate roles using `.lower()`.
- **Reason:** Ensures that API checks for roles are case-insensitive (matching the User model), and provides a utility to force browsers to fetch fresh UI data.

### `app/services/vocabulary_service.py`
- **Modification:** Refactored `process_review` to use MongoEngine's `update_one(set__...)` atomic operation. Added `GamificationObserver.on_task_completed()`.
- **Reason:** Greatly improves database write performance by avoiding full document loads, and seamlessly integrates Use Case 6 (Gamification).

### `app/services/dialogue_engine.py`
- **Modification:** Implemented actual Node traversal logic in `start_session` and `handle_user_choice`. Added `InteractionLog.save()` and `GamificationObserver` to `finalize_session`. Added `create_node`.
- **Reason:** Transforms the service from an empty interface into a functional engine that powers Use Case 4 and connects it to Gamification (UC6).

### `app/templates/base.html`
- **Modification:** Updated the navigation bar to include separate links for "Dashboard", "Courses", and "Teams".
- **Reason:** Allows the student to navigate freely between the newly separated views.