from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class SetupStep1Form(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired(), Length(3, 80)])
    email = StringField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired(), Length(8)])
    password_confirm = PasswordField(
        "Passwort bestätigen", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Weiter")


class SetupStep2Form(FlaskForm):
    ai_provider = SelectField(
        "Standard KI-Provider",
        choices=[("anthropic", "Anthropic (Claude)"), ("openai", "OpenAI (GPT)")],
        default="anthropic",
    )
    anthropic_api_key = StringField("Anthropic API Key", validators=[Optional()])
    openai_api_key = StringField("OpenAI API Key", validators=[Optional()])
    owm_api_key = StringField("OpenWeatherMap API Key", validators=[Optional()])
    google_maps_api_key = StringField("Google Maps API Key", validators=[Optional()])
    submit = SubmitField("Weiter")


class SetupStep3Form(FlaskForm):
    smtp_host = StringField("SMTP Host", validators=[Optional()])
    smtp_port = IntegerField("SMTP Port", validators=[Optional(), NumberRange(1, 65535)], default=587)
    smtp_user = StringField("SMTP Benutzername", validators=[Optional()])
    smtp_password = PasswordField("SMTP Passwort", validators=[Optional()])
    smtp_from = StringField("Absender E-Mail", validators=[Optional()])
    smtp_tls = BooleanField("TLS verwenden", default=True)
    submit = SubmitField("Weiter")


class SetupStep4Form(FlaskForm):
    default_timezone = StringField("Standard-Zeitzone", default="UTC")
    default_currency = StringField("Standard-Währung", default="EUR")
    default_locale = SelectField(
        "Sprache",
        choices=[("de", "Deutsch"), ("en", "English")],
        default="de",
    )
    default_transport_mode = SelectField(
        "Standard Fortbewegungsmittel",
        choices=[("transit", "ÖPNV"), ("driving", "Auto"), ("walking", "Fuß"), ("cycling", "Fahrrad")],
        default="transit",
    )
    planner_snap_minutes = SelectField(
        "Planer Raster (Minuten)",
        choices=[("5", "5"), ("10", "10"), ("15", "15"), ("30", "30")],
        default="15",
    )
    offline_map_zoom_min = IntegerField(
        "Offline-Karten Min-Zoom", validators=[NumberRange(1, 20)], default=12
    )
    offline_map_zoom_max = IntegerField(
        "Offline-Karten Max-Zoom", validators=[NumberRange(1, 20)], default=17
    )
    submit = SubmitField("Setup abschließen")
