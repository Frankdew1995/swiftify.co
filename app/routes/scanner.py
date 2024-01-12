from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session)

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user)
from app import db

from sqlalchemy.orm import joinedload

from app.aux_models import Message
from app.models import Tenant, Inventory, PO, Supplier, User

from pprint import pprint
from datetime import datetime
import json