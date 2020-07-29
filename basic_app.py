# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

from datetime import datetime
from flask import Flask, current_app, request, redirect, render_template_string, render_template
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
import json
import var
from forex_python.converter import CurrencyRates, CurrencyCodes
c = CurrencyRates()

CURRENCIES = [
    'AUD',
    'BGN',
    'BRL',
    'CAD',
    'CHF',
    'CNY',
    'CZK',
    'DKK',
    'GBP',
    'HKD',
    'HRK',
    'HUF',
    'IDR',
    'ILS',
    'INR',
    'JPY',
    'KRW',
    'MXN',
    'MYR',
    'NOK',
    'NZD',
    'PHP',
    'PLN',
    'RON',
    'RUB',
    'SEK',
    'SGD',
    'THB',
    'TRY',
    'USD',
    'ZAR'
]

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
    USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL = True
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"
    USER_LOGIN_URL = "/login"
    USER_LOGIN_TEMPLATE = "login.html"
    USER_AFTER_LOGIN_ENDPOINT = 'enter_exposure_page'
    USER_REGISTER_URL = "/register"
    USER_REGISTER_TEMPLATE = "register.html"
    USER_AFTER_REGISTER_ENDPOINT = 'payment_page'
    USER_LOGOUT_URL = "/logout"
    USER_AFTER_LOGOUT_ENDPOINT = "user.login"

# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(__name__+'.ConfigClass')

# Initialize Flask-BabelEx
babel = Babel(app)

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

# Setup Flask DB
class TimestampMixin(object):
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

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

class UserDetail(db.Model):
    __tablename__ = 'user_detail'
    id = db.Column(db.Integer(), primary_key=True)
    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    company_name = db.Column(
        db.String(100, collation='NOCASE'), nullable=False, server_default='')
    phoneno = db.Column(
        db.String(100, collation='NOCASE'), nullable=False, server_default='')
    plan = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='free')
    # last_payment_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, unique=True)
    user = db.relationship('User')

class Report(db.Model, TimestampMixin):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    time_horizon_days = db.Column(db.Integer, nullable=False, default=7)
    confidence = db.Column(db.Integer, nullable=False, default=95)
    pairs_json = db.Column(db.String(1000), db.ForeignKey('users.id'), nullable=False, server_default='[]')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)    

def add_detail(user_id, detail):
    detail = UserDetail(
        user_id=user_id,
        first_name=detail['first_name'],
        last_name=detail['last_name'],
        company_name=detail['company_name'],
        phoneno=detail['phoneno'], 
        plan=detail['plan'],
    )
    db.session.add(detail)
    db.session.commit()

def add_report(user_id, pairs, time_horizon_days, confidence):
    report = Report(
        user_id=user_id,
        pairs_json=json.dumps(pairs),
        time_horizon_days=time_horizon_days,
        confidence=confidence,
    )
    db.session.add(report)
    db.session.commit()

def add_payment(user_email):
    user = User.query.filter_by(email=user_email).first()
    detail = UserDetail.query.get(user.id)
    detail.last_payment_at = datetime.utcnow
    db.session.add(detail)
    db.session.commit()

class CustomUserManager(UserManager):
    def login_view(self):
        """Prepare and process the login form."""

        # Authenticate username/email and login authenticated users.

        safe_next_url =  self._get_safe_next_url('next', self.USER_AFTER_LOGIN_ENDPOINT)

        # Immediately redirect already logged in users
        if self.call_or_get(current_user.is_authenticated) and self.USER_AUTO_LOGIN_AT_LOGIN:
            return redirect(safe_next_url)

        # Initialize form
        login_form = self.LoginFormClass(request.form)

        if request.method != 'POST':
            return render_template('login.html')
        
        # Retrieve User
        user = None
        if self.USER_ENABLE_EMAIL:
            # Find user by email (with form.email)
            user, _ = self.db_manager.get_user_and_user_email_by_email(
                login_form.email.data)
        if user:
            safe_next_url = self.make_safe_url(login_form.next.data)
            return self._do_login_user(user, safe_next_url, True)
        

    def register_view(self):
        safe_reg_next = self._get_safe_next_url('reg_next', self.USER_AFTER_REGISTER_ENDPOINT)

        # Immediately redirect already logged in users
        if self.call_or_get(current_user.is_authenticated) and self.USER_AUTO_LOGIN_AT_LOGIN:
            return redirect(safe_reg_next)

        # Initialize form
        register_form = self.RegisterFormClass(request.form)
        page_number = request.args.get('p') or 1

        if request.method == 'POST':
            user = self.db_manager.add_user()
            register_form.populate_obj(user)
            user_email = self.db_manager.add_user_email(
                user=user, is_primary=True)
            register_form.populate_obj(user_email)
            user.password = self.hash_password(user.password)

            self.db_manager.save_user_and_user_email(user, user_email)
            self.db_manager.commit()
            add_detail(user.id, {
                'first_name': request.form.getlist('first_name').pop(),
                'last_name': request.form.getlist('last_name').pop(),
                'company_name': request.form.getlist('company_name').pop(),
                'phoneno': request.form.getlist('phoneno').pop(), 
                'plan': request.form.getlist('plan').pop(),
            })

            return self._do_login_user(user, safe_reg_next, False)

        return render_template('register.html', currencies=CURRENCIES)

# Setup Flask-User and specify the User data-model
user_manager = CustomUserManager(app, db, User)

# Create all database tables
db.create_all()

# Create 'member@example.com' user with no roles
if not User.query.filter(User.email == 'member@example.com').first():
    user = User(
        email='member@example.com',
        email_confirmed_at=datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    db.session.add(user)
    db.session.commit()
    add_detail(user.id, {
        'first_name': 'Member',
        'last_name': 'Member',
        'company_name': 'Sample Company Inc.',
        'phoneno': '9090909090',
        'plan': 'free',
    })

# Create 'admin@example.com' user with 'Admin' and 'Agent' roles
if not User.query.filter(User.email == 'admin@example.com').first():
    user = User(
        email='admin@example.com',
        email_confirmed_at=datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    user.roles.append(Role(name='Admin'))
    user.roles.append(Role(name='Agent'))
    db.session.add(user)
    db.session.commit()
    db.session.flush()
    add_detail(user.id, {
        'first_name': 'Admin',
        'last_name': 'Admin',
        'company_name': 'Sample Company Inc.',
        'phoneno': '9090909090',
        'plan': 'free',
    })

def get_raw_pairs(form, files, report_id):
    if report_id and Report.query.get(report_id):
        report = Report.query.get(report_id)
        return (
            json.loads(report.pairs_json),
            report.time_horizon_days,
            report.confidence,
        )
    
    if 'exposures_csv' not in files:
        return []
    
    file = files['exposures_csv']
    rows = [ line.decode("utf-8").split(',') for line in file.read().splitlines() ]
    file.close()

    n = int(form.getlist('time_horizon').pop())
    confidence = float(form.getlist('confidence').pop())
    
    if len(rows) > 0:
        return (
            [
                [
                    r[0].strip(),
                    r[1].strip(),
                    int(r[2].strip()),
                ] for r in rows
            ],
            n,
            confidence,
        )
    else:
        return (
            list(map(
                lambda x: [x[0].strip(), x[1].strip(), int(x[2].strip())],
                zip(
                    form.getlist('short[]'),
                    form.getlist('long[]'),
                    form.getlist('amount[]'),
                )
            )),
            n,
            confidence,
        )
    

def handle_report(form, files, report_id, user_id):
    raw_pairs, n, confidence = get_raw_pairs(form, files, report_id)
    print(raw_pairs)
    pairs = list(filter(lambda x: x[0] in CURRENCIES and x[1] in CURRENCIES, raw_pairs))

    if not report_id:
        add_report(user_id, pairs, n, confidence)

    results = list(zip(
        list(map(lambda p: f"{p[0]}-{p[1]}", pairs)),
        list(map(lambda p: p[1], pairs)),
        list(map(lambda p: f"{p[2]:,}", pairs)),
        list(map(
            lambda x: f"{round(abs(x), 3):,}", var.get_n_day_individual_vars(
                pairs, n, confidence)
        )),
        list(map(
            lambda x: f"{round(x, 3):,}", var.get_n_day_component_vars(
                pairs, n, confidence)
        )),
        list(map(
            lambda x: f"{round(x*100/var.get_portfolio_var(pairs, n, confidence), 1):,}%",
            var.get_n_day_component_vars(pairs, n, confidence)
        )),
    )) + [(
        "Total",
        "-",
        f"{round(sum([p[2] for p in pairs]), 3):,}",
        f"{round(abs(sum(var.get_n_day_individual_vars(pairs, n, confidence))), 3):,}",
        f"{round(var.get_portfolio_var(pairs, n, confidence), 3):,}",
        "100%",
    )]
    benefit_abs = round((
        abs(sum(var.get_n_day_individual_vars(pairs, n, confidence))) - var.get_portfolio_var(pairs, 7, confidence)),
        3
    )
    benefit_percent = round((
        abs(sum(var.get_n_day_individual_vars(pairs, n, confidence))) - var.get_portfolio_var(pairs, 7, confidence)),
        3
    )

    return {
        'results': results,
        'benefit_abs': f"{benefit_abs:,}",
        'benefit_percent': f"{benefit_percent:,}",
        'confidence': format(confidence*100, '.0f')+"%",
        'currencies': CURRENCIES,
    }

def handle_suggestions(report_id, scenario_id):
    report = Report.query.get(report_id)
    pairs, n, confidence = json.loads(
        report.pairs_json), report.time_horizon_days, report.confidence
    current_var = f"{round(var.get_portfolio_var(pairs, n, confidence), 3):,}"

    component_vars = var.get_n_day_component_vars(pairs, n, confidence)
    sorted_component_vars = sorted(enumerate(component_vars), key=lambda x: x[1], reverse=True)
    
    scenarios = []
    var_reductions = []
    if len(pairs) >= 1:
        scenarios.append([
            [
                pairs[i][1],
                pairs[i][0],
                pairs[i][2] if i == sorted_component_vars[0][0] else 0,
                f"{n} Days",
            ]
            for i in range(len(pairs))
        ])
        var_reductions.append(sorted_component_vars[0][1])
    if len(pairs) >= 2:
        scenarios.append([
            [
                pairs[i][1],
                pairs[i][0],
                sum([
                    pairs[i][2]*1 if i == sorted_component_vars[1][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[0][0] else 0,
                ]),
                f"{n} Days",
            ]
            for i in range(len(pairs))
        ])
        var_reductions.append(sum([
            sorted_component_vars[1][1]*1,
            sorted_component_vars[0][1]*0.5,
        ]))
    if len(pairs) >= 3:
        scenarios.append([
            [
                pairs[i][1],
                pairs[i][0],
                sum([
                    pairs[i][2] * 1 if i == sorted_component_vars[2][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[1][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[0][0] else 0,
                ]),
                f"{n} Days",
            ]
            for i in range(len(pairs))
        ])
        var_reductions.append(sum([
            sorted_component_vars[2][1]*1,
            sorted_component_vars[1][1]*0.5,
            sorted_component_vars[0][1]*0.5,
        ]))
    if len(pairs) >= 4:
        scenarios.append([
            [
                pairs[i][1],
                pairs[i][0],
                sum([
                    pairs[i][2] * 1 if i == sorted_component_vars[3][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[2][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[1][0] else 0,
                    pairs[i][2] * 0.5 if i == sorted_component_vars[0][0] else 0,
                ]),
                f"{n} Days",
            ]
            for i in range(len(pairs))
        ])
        var_reductions.append(sum([
            sorted_component_vars[3][1] * 1,
            sorted_component_vars[2][1] * 0.5,
            sorted_component_vars[1][1] * 0.5,
            sorted_component_vars[0][1] * 0.5,
        ]))
    var_reductions = [f"{round(x, 3):,}" for x in var_reductions]
    diffs = [f"{round(float(current_var)-float(v), 3):,}" for v in var_reductions]

    return {
        'report_id': report_id,
        'scenario': int(scenario_id),
        'scenarios': scenarios,
        'total_scenarios': len(scenarios),
        'current_var': current_var,
        'var_reductions': var_reductions,
        'diffs': diffs,
    }

def add_routes():
    """ Add Routes to Flask App """

    # The Home page is accessible to anyone
    @app.route('/admin')
    @roles_required(['Admin', 'Agent'])
    def home_page():
        return render_template('./admin/home.html')

    # The Members page is only accessible to authenticated users
    @app.route('/admin/members')
    @roles_required(['Admin', 'Agent'])   # Use of @login_required decorator
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
        return render_template('./register.html')
    
    @app.route('/payment')
    # @login_required
    def payment_page():
        PP_CLIENT_ID = "AQnE3_uZrT1Vf56AluXZIR1ir4gUYWAMmxquNRnRzGSVukHeGPzUvu5WsW4FtdYhqrHO06IQkKTr8zOh"
        user = User.query.filter_by(email=current_user.email).first()
        detail = UserDetail.query.filter_by(user_id=user.id).first()
        plan, last_payment_at = detail.plan, detail.last_payment_at
        plan_id = ''
        if plan == 'free':
            return redirect('/enter-exposure')
        if plan == 'premium':
            plan_id = 'P-6WL802942Y8719627L4PXXFY'
        elif plan == 'business':
            plan_id = 'P-306056489A234290WL4PXXLI'
        return render_template('./payment.html', plan_id=plan_id, PP_CLIENT_ID=PP_CLIENT_ID)
    
    @app.route('/payment-complete')
    def payment_complete_page():
        add_payment(current_user.email)
        return redirect('/enter-exposure')

    @app.route('/enter-exposure')
    def enter_exposure_page():
        return render_template('./exposures.html', currencies=CURRENCIES)

    @app.route('/report', methods=['GET', 'POST'])
    @login_required
    def report_page():
        user = User.query.filter_by(email=current_user.email).first()
        if request.method == 'POST':
            return render_template(
                './report.html',
                **handle_report(request.form, request.files, None, user.id),
            )
        report = Report.query.get_or_404(request.args.get('id'))
        return render_template(
            './report.html',
            **handle_report(request.form, request.files, report.id, user.id),
        )

    @app.route('/suggestion-tool')
    def suggestion_tool_page():
        user = User.query.filter_by(email=current_user.email).first()
        reports = Report.query.filter_by(user_id=user.id).all()
        report_id = request.args.get('report_id') or reports.pop().id
        scenario = request.args.get('scenario') or 1

        return render_template(
            './suggestion_tool.html', 
            **handle_suggestions(report_id, scenario),
        )

    @app.route('/account')
    @login_required
    def account_page():
        user = User.query.filter_by(email=current_user.email).first()
        detail = UserDetail.query.filter_by(user_id=user.id).first()
        reports = Report.query.filter_by(user_id=user.id).all()
        for i in range(len(reports)):
            reports[i].created = reports[i].created.strftime("%A, %d-%b-%Y %H:%M:%S GMT%z")
        return render_template(
            './account.html',
            email=current_user.email,
            first_name=detail.first_name,
            last_name=detail.last_name,
            company_name=detail.company_name,
            plan=detail.plan,
            reports=reports,
        )

    @app.route('/contact')
    def contact_page():        
        return render_template(
            './contact.html'            
        )

    @app.route('/')
    def index():
        return render_template('./splash.html')

# Start development web server
if __name__ == '__main__':
    # Setup Flask Server Routes
    add_routes()
    app.run(host='0.0.0.0', port=5000, debug=True)
