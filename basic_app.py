# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string, render_template
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from forex_python.converter import CurrencyRates

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'jlmobile710@gmail.com'
    MAIL_PASSWORD = 'eoqldir111'
    MAIL_DEFAULT_SENDER = '"FX Risk App" <noreply@gmail.com>'

    # Flask-User settings
    # Shown in and email templates and page footers
    USER_APP_NAME = "FX Risk App"
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

def add_models(app):
    """ Add DB Models to Flask App """

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(),
                           nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'),
                          nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(
            db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(
            db.String(100, collation='NOCASE'), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey(
            'users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey(
            'roles.id', ondelete='CASCADE'))

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # Create all database tables
    db.create_all()

    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user)
        db.session.commit()

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()
    
    return app

def add_routes(app):
    """ Add Routes to Flask App """

    # The Home page is accessible to anyone
    @app.route('/admin')
    @roles_required('Admin')
    def home_page():
        return render_template('./admin/home.html')

    # The Members page is only accessible to authenticated users
    @app.route('/admin/members')
    @login_required    # Use of @login_required decorator
    def member_page():
        return render_template('./admin/members.html')

    # The Admin page requires an 'Admin' role.
    @app.route('/admin/dashboard')
    @roles_required('Admin')    # Use of @roles_required decorator
    def admin_page():
        return render_template_string("""
                {% extends "admin_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Admin Page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                    <p><a href={{ url_for('admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    @app.route('/register')
    def register_page():
        c = CurrencyRates()
        rates = list(c.get_rates('USD'))
        return render_template('./register.html', rates=rates)

    @app.route('/enter-exposure')
    def enter_exposure_page():
        c = CurrencyRates()
        rates = list(c.get_rates('USD'))
        return render_template('./exposures.html', rates=rates)

    @app.route('/report')
    def report_page():
        c = CurrencyRates()
        rates = list(c.get_rates('USD'))
        typ = request.args.get('type')
        if typ == 'heatmap':
            return render_template('./report-heatmap.html', rates=rates)
        elif typ == 'chart':
            return render_template('./report-chart.html', rates=rates)
        return render_template('./report.html', rates=rates)
    
    @app.route('/suggestion-tool')
    def suggestion_tool_page():
        number = request.args.get('number') or 1
        return render_template('./suggestion_tool.html', number=int(number))

    @app.route('/account')
    def account_page():
        c = CurrencyRates()
        rates = list(c.get_rates('USD'))
        return render_template('./account.html', rates=rates)

    @app.route('/')
    def index():
        return render_template('./splash.html')

    return app


def create_app():
    """ Flask application factory """

    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-BabelEx
    babel = Babel(app)

    # Setup Flask DB
    add_models(app)

    # Setup Flask Server Routes
    add_routes(app)

    return app

# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
