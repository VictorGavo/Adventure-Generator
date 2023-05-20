from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField, TextAreaField, HiddenField

from wtforms.validators import DataRequired, Email, EqualTo, Length

from src.accounts.models import User

class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

class RegisterForm(FlaskForm):
    email = EmailField(
        "Email", validators=[DataRequired(), Email(message=None), Length(min=6, max=40)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=25)]
    )
    confirm = PasswordField(
        "Repeat password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    def validate(self, extra_validators=None):

        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        if self.password.data != self.confirm.data:
            self.password.errors.append("Passwords must match")
            return False
        return True
    
class SceneForm(FlaskForm):
    name = HiddenField('Name')
    focus = StringField('Focus', validators=[DataRequired()])
    vibe = StringField('Vibe', validators=[DataRequired()])
    submit_button = SubmitField()

class SceneEditForm(FlaskForm):
    box_text = TextAreaField('Boxed Text', validators=[DataRequired()])
    image_text = TextAreaField('Image Text', validators=[DataRequired()])
    submit = SubmitField('Save')

class BiomeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit_button = SubmitField()