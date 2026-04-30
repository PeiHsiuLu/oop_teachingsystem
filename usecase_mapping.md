# English Learning System - Use Case to File Mapping

This document maps the system's 8 core use cases to their corresponding source code files and directories, based on the recommended OOAD structure.

---

### 1. Manage the account
*   **Purpose:** Handles user authentication, authorization, registration, and profile management.
*   **Files:**
    *   `app/utils/decorators.py`: Enforces role-based access control (e.g., Student vs. Admin).
    *   `app/models/user.py`: Defines the `User`, `Student`, and `Admin` data models.
    *   `app/services/auth_service.py`: Contains the business logic for login, registration, and profile updates.
    *   `app/routes/account_api.py`: Provides the API endpoints (e.g., /login, /register, /profile).

### 2. Course arrange
*   **Purpose:** Allows Admins to create learning paths and units, and for Students to view them.
*   **Files:**
    *   `app/models/course.py`: Defines the `LearningPath` and `Unit` data models.
    *   `app/routes/course_api.py`: Provides endpoints for creating and viewing course structures.

### 3. Database build and training
*   **Purpose:** Manages data persistence and interaction with the MongoDB database using the Repository Pattern.
*   **Files:**
    *   `app/repositories/`: This entire directory acts as the data access layer.
    *   `app/repositories/base_repository.py`: A generic repository with base CRUD operations.
    *   `app/repositories/user_repository.py`: Specific data access logic for User models.
    *   `app/models/vocabulary.py`: Defines the `Word` and `VocabularyBank` models for student vocabulary.

### 4. Course interaction
*   **Purpose:** Manages student engagement with course content, like scenario dialogues and recording logs.
*   **Files:**
    *   `app/models/course.py`: The `DialogueNode` and `InteractionLog` classes are defined here.
    *   `app/routes/interaction_api.py`: Endpoints for submitting answers and progressing through units.

### 5. Result Analysis
*   **Purpose:** Analyzes student performance and powers the Spaced Repetition System (SRS).
*   **Files:**
    *   `app/services/srs_strategy.py`: Implements the Strategy Pattern for different forgetting curve algorithms.
    *   `app/models/vocabulary.py`: The `Word` model stores `ease_factor` and `next_review_date` for the SRS.

### 6. Learning by Game
*   **Purpose:** Implements gamification features like XP, levels, and badges.
*   **Files:**
    *   `app/services/game_observer.py`: Implements the Observer Pattern to grant rewards when tasks are completed.
    *   `app/models/gamification.py`: Defines `Badge` models and tracks student `xp`, `level`, etc.

### 7. Team Up
*   **Purpose:** Allows users to create, join, and manage study groups.
*   **Files:**
    *   `app/models/team.py`: Defines the `StudyGroup` model.
    *   `app/routes/team_api.py`: Provides endpoints for team management.

### 8. Report the Fault
*   **Purpose:** Handles user reports for inappropriate content and admin moderation tools.
*   **Files:**
    *   `app/services/moderation.py`: Contains the logic for the "Safety Loop" to review reports and take action.

