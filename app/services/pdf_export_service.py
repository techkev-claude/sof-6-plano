import structlog
from flask import render_template_string

log = structlog.get_logger()


def export_trip_pdf(trip) -> bytes:
    try:
        from weasyprint import HTML
        html = render_template_string(
            "<html><body><h1>{{ trip.title }}</h1></body></html>",
            trip=trip
        )
        return HTML(string=html).write_pdf()
    except Exception as e:
        log.error("pdf_export_error", error=str(e))
        raise
