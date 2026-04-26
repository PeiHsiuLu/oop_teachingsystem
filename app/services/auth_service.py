from app.repositories.user_repository import UserRepository
from app.models.user import Student, Admin
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, username, email, password, role='student'):
        """Registers a new user (Student or Admin)."""
        # Check if user already exists
        if self.user_repo.get_by_username(username):
            raise ValueError("Username already taken.")

        # Hash the password
        hashed_pw = generate_password_hash(password).decode('utf-8')

        # Create the appropriate polymorphic object
        if role == 'admin':
            new_user = Admin(username=username, password_hash=hashed_pw)
        else:
            new_user = Student(username=username, password_hash=hashed_pw)
            


        # Save via Repository
        return self.user_repo.save(new_user)

    def login(self, username, password):
        """Authenticates a user and starts a session."""
        user = self.user_repo.get_by_username(username)
        
        if user and check_password_hash(user.password_hash, password):
            # login_user handles the session cookie
            login_user(user)
            return True
            
        return False

    def logout(self):
        """Ends the user session."""
        logout_user() # Handles deleting the session cookie
        return True

    def validate_role(self, user_id, required_role):
        """Checks if a user has the required role to access a page."""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False
            
        # Check if the object is the correct type, or check the role string
        if required_role == 'admin' and isinstance(user, Admin):
            return True
        if required_role == 'student' and isinstance(user, Student):
            return True
            
        return False