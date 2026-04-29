# CHECKPOINT: English Learning System (OOAD Project)

This document outlines the current state of development for the English Learning System, focusing on the backend architecture and server-rendered UI for three primary use cases: Vocabulary Bank & Training, Course Interaction, and Analytics.

## 1. File Directory & Functions

This section details the purpose of each file within the current project structure.

### Core Application
-   `run.py`: The main entry point for the Flask application. It imports the app factory and runs the development server.
-   `config.py`: Contains application configuration, primarily the connection URI for the MongoDB Atlas database.
-   `app/__init__.py`: The application factory (`create_app`). It initializes the Flask app, connects to the database, registers all blueprints (routes), and sets up Flask-Login.

### `app/models/` - Data Schema Layer
Defines the BSON document structures for MongoDB using `mongoengine`.
-   `user.py`: Defines the `User`, `Admin`, and `Student` models using polymorphic inheritance.
-   `word.py`: Defines the core vocabulary schemas: `Word` (the vocabulary itself), `SentenceGeneratingRule`, and `ReviewItem` (tracks a student's SRS progress for a word).
-   `course.py`: Defines schemas for `LearningPath`, `Chapter`, and `Unit`.
-   `dialogue.py`: Defines the `DialogueNode` and `DialogueOption` schemas for building interactive conversation trees.
-   `analytics.py`: Defines the `InteractionLog` schema for recording user events for later analysis.

### `app/repositories/` - Data Access Layer
Abstracts database interactions, separating business logic from data persistence logic.
-   `base_repository.py`: An abstract base class providing a common interface for all repositories (e.g., `save`, `find_by_id`).
-   `user_repository.py`: Handles database operations for `User` documents.
-   `course_repository.py`: Handles database operations for `LearningPath` and `Chapter` documents.
-   `word_repository.py`: Handles database operations for `Word` and `ReviewItem` documents.
-   `sentence_rule_repository.py`: Handles database operations for `SentenceGeneratingRule` documents.

### `app/services/` - Business Logic Layer
Contains the core business logic and orchestrates operations between different components.
-   `auth_service.py`: Manages user registration, login, logout, and role validation.
-   `course_serivce.py`: Manages the creation of learning paths and their components.
-   `word_service.py`: Provides methods for administrators to manage the vocabulary (`Word`) and sentence generation rules.
-   `srs_service.py`: Implements the Spaced Repetition System. It contains the `SRSManager` and the `SuperMemo2Strategy`, demonstrating the **Strategy Pattern**.
-   `dialogue_service.py`: The `DialogueEngine` for navigating scenario-based conversations defined by `DialogueNode`s.
-   `analytics_service.py`: The `AnalyticsEngine` for logging user interactions and generating reports from those logs.

### `app/routes/` - Presentation & API Layer
Contains Flask Blueprints that define the application's URLs (routes) and connect them to backend logic. This layer also includes the UI templates and components.
-   `main.py`: Defines the route for the main home page (`/`).
-   `auth.py`: Defines routes for user authentication (`/register`, `/login`, `/logout`).
-   `course.py`: Defines routes for course management.
-   `word.py`: Defines routes for vocabulary management. This includes a server-rendered page for admins (`/admin/words/manage`) and several JSON API endpoints for programmatic access.
-   `srs.py`: Defines the student-facing routes for vocabulary review (`/review/next`, `/review`), which render the flashcard interface.

#### HTML Templates (Server-Rendered UI)
-   `base.html`: The main Jinja2 template providing the site-wide layout, navigation bar, and styling.
-   `index.html`: The home page template, which dynamically shows different options based on user role.
-   `login.html` / `register.html`: User authentication forms.
-   `admin_words.html`: A dashboard for administrators to add new words and view the existing vocabulary.
-   `review_card.html`: The student-facing flashcard interface for SRS vocabulary review.

#### React Components (For a Decoupled Frontend)
*Note: These files are part of the original frontend architecture plan but are not currently integrated with the server-rendered Flask application.*
-   `SRSFlashcard.js`: A React component designed to fetch data from the SRS JSON API and render a flashcard UI.
-   `AITutor.js`: A React component designed to create a chat interface for the `DialogueEngine`.

### `app/models/test_srs_service.py`
*Note: This file is currently misplaced in the `models` directory. It should be in a dedicated `tests/` folder.*
-   `test_srs_service.py`: Contains unit tests for the `SuperMemo2Strategy` using `pytest` and `mongomock` to ensure the SRS algorithm's calculations are correct in isolation.

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

-   **Decorator Pattern:** Used to add cross-cutting concerns like authentication and authorization.
    -   **File:** `app/routes/word.py`
    -   **Implementation:** The `@admin_required` decorator wraps route functions, adding a role-checking layer before the route's primary logic is executed. This keeps the authorization logic separate from the route's main responsibility.

---

## 4. New and Modified Files

The following files have been created or modified during this development checkpoint.

### New Files
- `app/models/analytics.py`
- `app/models/dialogue.py`
- `app/models/test_srs_service.py`
- `app/repositories/sentence_rule_repository.py`
- `app/repositories/word_repository.py`
- `app/routes/AITutor.js`
- `app/routes/SRSFlashcard.js`
- `app/routes/admin_words.html`
- `app/routes/base.html`
- `app/routes/index.html`
- `app/routes/login.html`
- `app/routes/main.py`
- `app/routes/register.html`
- `app/routes/review_card.html`
- `app/services/analytics_service.py`
- `app/services/dialogue_service.py`
- `app/services/srs_service.py`
- `app/services/word_service.py`

### Modified Files
- `app/__init__.py`
- `app/models/user.py`
- `app/models/word.py`
- `app/routes/auth.py`
- `app/routes/course.py`
- `app/routes/srs.py`
- `app/routes/word.py`