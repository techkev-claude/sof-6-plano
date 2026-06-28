from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class TripForm(FlaskForm):
    title = StringField("Titel", validators=[DataRequired(), Length(1, 200)])
    destination = StringField("Reiseziel", validators=[Optional(), Length(max=200)])
    description = TextAreaField("Beschreibung", validators=[Optional()])
    start_date = DateField("Startdatum", validators=[DataRequired()])
    end_date = DateField("Enddatum", validators=[DataRequired()])
    currency = SelectField(
        "Währung",
        choices=[("EUR", "EUR"), ("USD", "USD"), ("GBP", "GBP"), ("CHF", "CHF"), ("JPY", "JPY")],
        default="EUR",
    )
    budget_total = DecimalField("Gesamtbudget", validators=[Optional()], places=2)
    submit = SubmitField("Speichern")


class TripLegForm(FlaskForm):
    title = StringField("Titel", validators=[DataRequired(), Length(1, 200)])
    start_date = DateField("Startdatum", validators=[DataRequired()])
    end_date = DateField("Enddatum", validators=[DataRequired()])
    transport_mode = SelectField(
        "Fortbewegungsmittel",
        choices=[
            ("transit", "ÖPNV"),
            ("driving", "Auto"),
            ("walking", "Fuß"),
            ("cycling", "Fahrrad"),
            ("flight", "Flug"),
        ],
    )
    notes = TextAreaField("Notizen", validators=[Optional()])
    color = StringField("Farbe", default="#6366f1")
    submit = SubmitField("Speichern")


class AddMemberForm(FlaskForm):
    username_or_email = StringField("Benutzername oder E-Mail", validators=[DataRequired()])
    permission = SelectField(
        "Berechtigung",
        choices=[("viewer", "Leser"), ("editor", "Bearbeiter")],
    )
    submit = SubmitField("Hinzufügen")
