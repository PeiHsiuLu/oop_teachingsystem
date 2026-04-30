from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, Length # Add Email here

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()]) # New field
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CreatePathForm(FlaskForm):
    name = StringField('Path Name', validators=[DataRequired()])
    submit = SubmitField('Create Path')

class AddChapterForm(FlaskForm):
    title = StringField('Chapter Title', validators=[DataRequired()])
    rule_type = SelectField('Unlock Rule', choices=[('none', 'None'), ('level', 'Level'), ('score', 'Score')])
    threshold = IntegerField('Threshold')
    submit = SubmitField('Add Chapter')

class AddUnitForm(FlaskForm):
    title = StringField('Unit Title', validators=[DataRequired()])
    submit = SubmitField('Add Unit')