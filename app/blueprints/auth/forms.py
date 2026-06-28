from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired(), Length(1, 80)])
    password = PasswordField("Passwort", validators=[DataRequired()])
    remember_me = BooleanField("Angemeldet bleiben")
    submit = SubmitField("Anmelden")
