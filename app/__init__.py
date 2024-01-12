from flask import (Flask, render_template,
                   url_for, redirect,
                   make_response, send_file,
                   jsonify, flash,
                   session, request, abort)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from config import Config, ProductionConfig, is_prod
from flask_caching import Cache
from flask_pymongo import PyMongo
from pathlib import Path
from flask_redis import FlaskRedis
from flask_babel import Babel

import redis
import os

app = Flask(__name__)

# Configure from a Python object
if is_prod:

    app.config.from_object(ProductionConfig)

else:

    app.config.from_object(Config)

db = SQLAlchemy(app)

# this setting is unique when using a SQLite DB
migrate = Migrate(app, db, render_as_batch=True)

login = LoginManager(app)


cache = Cache(app)

mongo = PyMongo(app)

# init babel in flask app obj
babel = Babel(app)

# redis client init
redis_client = FlaskRedis(app, decode_responses=True)

# Set the Login View to protect a view
login.login_view = "sign_in"

# establish a redis connection to record the change log of a Document: PO, Invoice or SalesOrder or a Shipment
try:
    documents_changelog_store = redis.Redis(
        host='redis-10088.c269.eu-west-1-3.ec2.cloud.redislabs.com',
        port=10088,
        password='xxxxxx')

    # Test the connection
    documents_changelog_store.ping()

except ConnectionError:
    print('Failed to connect to Redis')
    documents_changelog_store = None

from app import models

from app.routes import (users, common, suppliers, super_user,
                        api, scanner, user_manager,
                        purchase_orders, activity_flows, warehouses,
                        shipments, inventories, messenger, auxillary)



