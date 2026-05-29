from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

# --- AUTH FORMS ---

class LoginForm(FlaskForm):
    """The base for authentication."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(LoginForm):
    """Extends Login by adding email and role."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')])
    submit = SubmitField('Register') # Overrides the label

# --- COURSE/CONTENT FORMS ---

class TitleForm(FlaskForm):
    """Base form for anything that just needs a title/name."""
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CreatePathForm(TitleForm):
    """Uses the title field as the 'Path Name'."""
    submit = SubmitField('Create Path')

class AddUnitForm(TitleForm):
    """Exactly the same as TitleForm, just a different button label."""
    submit = SubmitField('Add Unit')

class AddChapterForm(TitleForm):
    """Extends TitleForm by adding rules."""
    rule_type = SelectField('Unlock Rule', choices=[
        ('none', 'None'), ('level', 'Level'), ('score', 'Score')
    ])
    threshold = IntegerField('Threshold', default=0)
    submit = SubmitField('Add Chapter')

class EditUnitForm(FlaskForm):
    """Unique enough to stay separate, or could inherit from TitleForm if you edit titles too."""
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Changes')