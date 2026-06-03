from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Regexp


# --- AUTH FORMS ---

USERNAME_REQUIRED_MESSAGE = "Username is required. 請輸入使用者名稱。"
EMAIL_REQUIRED_MESSAGE = "Email is required. 請輸入 Email。"
EMAIL_FORMAT_MESSAGE = "Please enter a valid email address. 請輸入正確的 Email 格式。"
PASSWORD_REQUIRED_MESSAGE = "Password is required. 請輸入密碼。"
PASSWORD_LENGTH_MESSAGE = "Password must be at least 8 characters. 密碼至少需要 8 個字元。"
ROLE_REQUIRED_MESSAGE = "Role is required. 請選擇身分。"

STRONG_PASSWORD_MESSAGE = (
    "Password must be at least 8 characters and include uppercase, lowercase, number, and special character. "
    "密碼至少需要 8 個字元，並且必須包含大寫英文、小寫英文、數字與特殊符號。"
)


class LoginForm(FlaskForm):
    """Login form for user authentication."""

    username = StringField(
        "Username",
        validators=[
            DataRequired(message=USERNAME_REQUIRED_MESSAGE)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message=PASSWORD_REQUIRED_MESSAGE)
        ]
    )

    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    """Registration form with strong password rules."""

    username = StringField(
        "Username",
        validators=[
            DataRequired(message=USERNAME_REQUIRED_MESSAGE)
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message=EMAIL_REQUIRED_MESSAGE),
            Email(message=EMAIL_FORMAT_MESSAGE)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message=PASSWORD_REQUIRED_MESSAGE),
            Length(min=8, message=PASSWORD_LENGTH_MESSAGE),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$",
                message=STRONG_PASSWORD_MESSAGE
            )
        ]
    )

    role = SelectField(
        "Role",
        choices=[
            ("student", "Student"),
            ("admin", "Admin")
        ],
        validators=[
            DataRequired(message=ROLE_REQUIRED_MESSAGE)
        ]
    )

    submit = SubmitField("Register")


# --- COURSE / CONTENT FORMS ---

class TitleForm(FlaskForm):
    """Base form for anything that only needs a title/name."""

    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required. 請輸入標題。")
        ]
    )

    submit = SubmitField("Submit")


class CreatePathForm(TitleForm):
    """Form for creating a learning path."""

    submit = SubmitField("Create Path")


class AddUnitForm(TitleForm):
    """Form for adding a unit."""

    submit = SubmitField("Add Unit")


class AddChapterForm(TitleForm):
    """Form for adding a chapter with unlock rules."""

    rule_type = SelectField(
        "Unlock Rule",
        choices=[
            ("none", "None"),
            ("level", "Level"),
            ("score", "Score")
        ]
    )

    threshold = IntegerField(
        "Threshold",
        default=0
    )

    submit = SubmitField("Add Chapter")


class EditUnitForm(FlaskForm):
    """Form for editing unit content."""

    content = TextAreaField(
        "Content",
        validators=[
            DataRequired(message="Content is required. 請輸入內容。")
        ]
    )

    submit = SubmitField("Save Changes")