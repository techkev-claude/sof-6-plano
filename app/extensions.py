from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
scheduler = BackgroundScheduler()
