from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import event
from sqlalchemy.sql import func
import uuid
from app import db, login, app


@login.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


class Role(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)


# Create User Class and inherits from UserMixin
class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))

    # backref
    role = db.relationship('Role', backref='users', lazy=True)

    #
    activated = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)
    container = db.Column(db.String(5000))
    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)
    country = db.Column(db.String(128))

    user_name = db.Column(db.String(128))

    currency = db.Column(db.String(128))

    # if never a user signed for this company. setting this value to True
    is_admin = db.Column(db.Boolean, default=False)

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    # adding activity to User
    activities = db.relationship('Activity', back_populates='sender')

    def __repr__(self):

        return f'User: {self.email} + {self.user_name}>'

    def set_password(self, password):

        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    # confirmation link is valid for 48 hours
    def generate_confirmation_token(self, expiration=3600*48):

        s = Serializer(app.config['SECRET_KEY'], expiration)

        return s.dumps({"confirm": self.id}).decode("utf-8")

    def confirm(self, token):

        s = Serializer(app.config['SECRET_KEY'])

        try:

            data = s.loads(token.encode("utf-8"))

        except Exception as e:

            print(str(e))

            return None

        if data.get('confirm') != self.id:

            return None

        self.confirmed = True

        db.session.add(self)

        return True

    def generate_reset_token(self, expiration=3600):

        s = Serializer(app.config['SECRET_KEY'], expiration)

        return s.dumps({"user_id": self.id}).decode("utf-8")

    @staticmethod
    def verify_identify_by_token(token):

        s = Serializer(app.config['SECRET_KEY'])

        try:

            user_id = s.loads(token)['user_id']

        except Exception as e:

            print(str(e))

            return None

        return User.query.get(int(user_id))


# data model for Tenants. Tenants are companies using the system.
class Tenant(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(128), nullable=False, default="")
    contact_person = db.Column(db.String(128))
    currency = db.Column(db.String(128))

    # one >>>> many relationships /// one company has many users
    users = db.relationship('User', backref='tenant', lazy='dynamic')

    inventories = db.relationship('Inventory', back_populates="tenant", lazy='dynamic')

    pos = db.relationship('PO', back_populates="tenant", lazy='dynamic')
    suppliers = db.relationship('Supplier', back_populates="tenant", lazy='dynamic')
    warehouses = db.relationship('Warehouse', back_populates="tenant", lazy='dynamic')
    shipments = db.relationship('Shipment', back_populates="tenant", lazy='dynamic')

    # adding activity to Tenant
    activities = db.relationship('Activity', back_populates='tenant', lazy="dynamic")

    # Address
    street_n_no = db.Column(db.String(120))
    zip_code = db.Column(db.String)
    city = db.Column(db.String)
    state_or_province = db.Column(db.String)
    country = db.Column(db.String)

    # Tax and Customs data
    eori_id = db.Column(db.String)
    vat_id = db.Column(db.String)

    # Communications list of emails from admin and users >> use json.loads to access as a python list
    contacts = db.Column(db.String(5000))

    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)

    # Technical data
    domain = db.Column(db.String(128), unique=True)
    salesbinder_api_key = db.Column(db.String, unique=True)
    salesbinder_subdomain = db.Column(db.String, unique=True)

    # text string use json.loads to access
    settings = db.Column(db.String(5000), default='{"settings": ""}')

    # Other Metadata
    iban = db.Column(db.String)
    swift_code = db.Column(db.String)
    bank_name = db.Column(db.String)
    bank_address = db.Column(db.String)
    tax_rate_1 = db.Column(db.Integer)
    tax_rate_2 = db.Column(db.Integer)

    # adding public facing email - Non-unique / don't apply as a filter in any cases
    public_facing_email = db.Column(db.String(120))

    # Logo path of the tenant = File Path
    logo = db.Column(db.String)

    # assign a domain name
    def assign_domain_from_email(self, email):
        self.domain = email.split("@")[1]

    def __repr__(self):

        return f'company: {self.company_name}'


'''
To achieve many-to-many relationships between the Inventory and Supplier models, you need to create an 
association table. This table will store the relationship between Inventory and Supplier. Each row in the 
table represents a relationship, that is, an Inventory can be associated with multiple Suppliers, and a Supplier 
can be associated with multiple Inventory items.

# Assuming you have inventory and supplier objects

inventory.suppliers.append(supplier)
db.session.commit()

# Get all suppliers for an inventory
suppliers = inventory.suppliers

# Get all inventories for a supplier
inventories = supplier.inventories
'''
inventory_supplier = db.Table('inventory_supplier',
    db.Column('inventory_id', db.Integer, db.ForeignKey('inventory.id'), primary_key=True),
    db.Column('supplier_id', db.Integer, db.ForeignKey('supplier.id'), primary_key=True)
)


# add a table to track a tenant's max item code / inventory code from Inventory table
class TenantITEMNumbers(db.Model):
    __tablename__ = 'tenant_item_numbers'
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), primary_key=True)
    last_item_number = db.Column(db.Integer, default=0)


# Inventory
class Inventory(db.Model):

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)

    name = db.Column(db.String(500), unique=False, nullable=False)

    en_name = db.Column(db.String(500))

    brand = db.Column(db.String(100), default="")

    category = db.Column(db.String(100), default="")

    en_category = db.Column(db.String(100), default="")

    description = db.Column(db.String(1000))

    price = db.Column(db.Float(2))

    vat = db.Column(db.Float(2))

    gtin = db.Column(db.String(200))

    colli_barcode = db.Column(db.String(200))

    #  unique at the tenant level but not globally,
    item_code = db.Column(db.String(200), default="")

    hs_code = db.Column(db.String(200))

    origin = db.Column(db.String(200))

    img = db.Column(db.String(1000), default='')

    is_available = db.Column(db.Boolean, default=True)

    time_created = db.Column(db.Date, default=datetime.utcnow)

    '''
    packing data, gross weight, volume and packing unit
    '''
    palletized_quantity = db.Column(db.Integer)
    palletized_gw = db.Column(db.Integer)
    pallet_length = db.Column(db.Float)
    pallet_width = db.Column(db.Float)
    pallet_height = db.Column(db.Float)

    pu_quantity = db.Column(db.Integer)
    pu_gw = db.Column(db.Float)
    pu_length = db.Column(db.Float)
    pu_width = db.Column(db.Float)
    pu_height = db.Column(db.Float)

    '''
    Relations
    '''
    ###

    stock_quantity = db.Column(db.Integer)

    stock_location = db.Column(db.String(1000))

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    tenant = db.relationship('Tenant', back_populates="inventories")

    suppliers = db.relationship('Supplier', secondary=inventory_supplier, backref=db.backref('inventories', lazy='dynamic'))

    # Adding a universal unique id to query and identify an Inventory Item
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))

    def __repr__(self):

        return f"Product: {self.name}, {self.gtin}"

    # set the item number
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_item_code()

    def set_item_code(self):
        item_tracker = TenantITEMNumbers.query.get(self.tenant_id)
        if item_tracker is None:
            item_tracker = TenantITEMNumbers(tenant_id=self.tenant_id, last_item_number=1)
            db.session.add(item_tracker)
        else:
            item_tracker.last_item_number += 1
        self.item_code = item_tracker.last_item_number
        db.session.commit()


# supplier
class Supplier(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    # Define your fields here
    name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(128))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)

    # Address
    street_n_no = db.Column(db.String(120))
    zip_code = db.Column(db.String)
    city = db.Column(db.String)
    state_or_province = db.Column(db.String)
    country = db.Column(db.String)

    # add a time created
    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)

    # taxation and vat rate when creating a PO
    tax_rate_1 = db.Column(db.Integer)
    tax_rate_2 = db.Column(db.Integer)
    vat_id = db.Column(db.String)

    # warehouse and logistics
    warehouse_address = db.Column(db.String)
    warehouse_start_hours = db.Column(db.Time)
    warehouse_end_hours = db.Column(db.Time)

    # Adding a universal unique id to query and identify a Supplier
    uuid = db.Column(db.String(36))

    '''
    Adding a account number. The account number must be unique 
    at the tenant level but not globally, and it should increment from 5000
    '''
    account_number = db.Column(db.String(64))

    notes = db.Column(db.String(500))

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))  # Assuming your Tenant table's name is 'tenant'
    tenant = db.relationship('Tenant', back_populates="suppliers")
    pos = db.relationship('PO', backref='supplier', lazy=True)

    # adding activity to Supplier
    activities = db.relationship('Activity', back_populates='supplier')

    # method to create a warehouse address
    def set_warehouse_address(self):

        warehouse_address = " ".join([self.street_n_no, self.zip_code, self.city, self.state_or_province, self.country])
        self.warehouse_address = warehouse_address

    # Remember to call db.session.commit() to  commit the method result
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = str(uuid.uuid4())

    def __repr__(self):
        return f'Supplier: {self.name}'

    '''
    implement the auth mechanism for supplier. 
    The web token is valid for a month time. 
    Generally a life span for a PO cycle
    '''
    def generate_supplier_token(self, expiration=720*3600):
        s = Serializer(app.config['SECRET_KEY'], expiration)
        return s.dumps({"supplier_id": self.id}).decode("utf-8")

    @staticmethod
    def verify_supplier_by_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            supplier_id = s.loads(token)['supplier_id']
        except Exception as e:
            print(str(e))
            return None
        return Supplier.query.get(int(supplier_id))


'''
In this code, each time a supplier is created, it queries for the maximum account number that 
exists for the tenant and uses that to calculate the new account number. Note that this solution 
could also potentially have race condition issues if multiple suppliers are being added for the same 
tenant concurrently. If that's a concern, you'd need to look into SQLAlchemy's locking mechanisms as 
mentioned in the previous response. Please remember to handle the conversion from string to 
int properly, as the account number is stored as a string but manipulated as an int.
'''


def calculate_account_number(mapper, connection, target):
    # Query for the maximum account number for this tenant
    max_account_number = db.session.query(func.max(Supplier.account_number)).filter_by(tenant_id=target.tenant_id).scalar()
    if max_account_number is None:
        # This is the first supplier for this tenant
        target.account_number = str(5000)
    else:
        # Increment the maximum account number by 1
        target.account_number = str(int(max_account_number) + 1)


# associate the listener function with `before_insert` event
event.listen(Supplier, 'before_insert', calculate_account_number)


'''
Logistics
'''


class TransportMode(Enum):
    AIR = "Air"
    SEA = "Sea"
    RAIL = "Rail"
    MULTIMODE = "Multi-mode"


class ShipmentStatus(Enum):
    STARTED = "Started"
    CANCELLED = "Cancelled"
    ONGOING = "Ongoing"
    ACTIONS_REQUIRED = "Actions Required"
    COMPLETE = "Complete"


shipment_po_association = db.Table('shipment_po_association',
    db.Column('shipment_id', db.Integer, db.ForeignKey('shipment.id'), primary_key=True),
    db.Column('po_id', db.Integer, db.ForeignKey('po.id'), primary_key=True)
)


class Shipment(db.Model):

    __tablename__ = 'shipment'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float)
    status = db.Column(SQLEnum(ShipmentStatus), default=ShipmentStatus.STARTED)
    mode = db.Column(SQLEnum(TransportMode))
    shipment_number = db.Column(db.String(50))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    tenant = db.relationship('Tenant', back_populates="shipments")

    pos = db.relationship('PO', secondary=shipment_po_association, back_populates="shipments", lazy="subquery")

    activities = db.relationship('Activity', back_populates='shipment')


# Create Warehouse Class
class Warehouse(db.Model):

    id = db.Column(db.Integer, primary_key=True, default=0)

    email = db.Column(db.String(120), unique=True)

    # warehouse name
    warehouse_name = db.Column(db.String(128))

    # manager's name
    warehouse_manager = db.Column(db.String(128))

    email_domain = db.Column(db.String(50))

    address = db.Column(db.String(128))

    city = db.Column(db.String(128))

    state = db.Column(db.String(128))

    zipcode = db.Column(db.String(128))

    country = db.Column(db.String(128))

    timeCreated = db.Column(db.Date, default=datetime.utcnow)

    operating_hours = db.Column(db.String(50))

    notes = db.Column(db.Text)

    # relationships
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    tenant = db.relationship('Tenant', back_populates="warehouses")

    pos = db.relationship('PO', backref='warehouse', lazy=True)

    activities = db.relationship('Activity', back_populates='warehouse')

    @property
    def warehouse_email_domain(self):
        return self.email.split('@')[1]

    def __repr__(self):
        return f'<Warehouse {self.email}, {self.warehouse_name}, {self.warehouse_manager}>'


'''''''''''''''''''''''''''''''''''''''''''''''
Documents
'''''''''''''''''''''''''''''''''''''''''''''''

'''
A better way to handle this issue might be to maintain a 
separate table for tracking the last issued PO number for each tenant
'''


class TenantPONumbers(db.Model):
    __tablename__ = 'tenant_po_numbers'
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), primary_key=True)
    last_po_number = db.Column(db.Integer, default=0)


class PO(db.Model):

    __tablename__ = 'po'
    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.Column(db.String())
    container = db.Column(db.String(300))
    isReady = db.Column(db.Boolean, default=False)
    isDeclined = db.Column(db.Boolean(), default=False)
    isAccepted = db.Column(db.Boolean(), default=False)
    isExpired = db.Column(db.Boolean(), default=False)
    buyer = db.Column(db.String(1500))
    lastEdited = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.Date)
    req_id = db.Column(db.Integer)
    quote_id = db.Column(db.Integer)
    lead_time = db.Column(db.Integer)
    po_number = db.Column(db.Integer)
    supplier_po_number = db.Column(db.String(1500))
    reference = db.Column(db.String(1500))

    supplier_notes = db.Column(db.String(2000))
    warehouse_notes = db.Column(db.String(2000))

    status = db.Column(db.String(120))

    expected = db.Column(db.Date)

    # numeric data
    subtotal = db.Column(db.Float)
    discount = db.Column(db.Float)
    shipping_charges = db.Column(db.Float)
    total = db.Column(db.Float)
    tax_amount = db.Column(db.Float)

    '''
    relationships
    '''
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    tenant = db.relationship('Tenant', back_populates="pos")
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    # receiving warehouse
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))

    shipments = db.relationship('Shipment', secondary=shipment_po_association, back_populates="pos", lazy="subquery")

    activities = db.relationship('Activity', back_populates='po')

    # Adding a universal unique id to query and identify an Inventory Item
    uuid = db.Column(db.String(36))

    # create the UUID for the item and set the PO number
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = str(uuid.uuid4())
        if self.tenant_id is not None:  # Add a check here to prevent an error
            self.set_po_number()
        else:
            print("Warning: tenant_id is None.")

    def set_po_number(self):
        po_tracker = TenantPONumbers.query.get(self.tenant_id)
        if po_tracker is None:
            po_tracker = TenantPONumbers(tenant_id=self.tenant_id, last_po_number=1)
            db.session.add(po_tracker)
        else:
            po_tracker.last_po_number += 1
        self.po_number = po_tracker.last_po_number
        db.session.commit()


class Activity(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))

    # Related entities
    po_id = db.Column(db.Integer, db.ForeignKey('po.id'))
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    text = db.Column(db.String(5000))

    type = db.Column(db.String(50))  # new 'type' field

    # Relationship declarations
    sender = db.relationship('User', back_populates='activities')
    tenant = db.relationship('Tenant', back_populates='activities')
    warehouse = db.relationship('Warehouse', back_populates='activities')  # New warehouse relationship
    po = db.relationship('PO', back_populates='activities')
    shipment = db.relationship('Shipment', back_populates='activities')
    supplier = db.relationship('Supplier', back_populates='activities')


class Request(db.Model):

    id = db.Column(db.Integer, primary_key=True, index=True)
    timeCreated = db.Column(db.Date, default=datetime.utcnow)
    isReady = db.Column(db.Boolean, default=False)
    items = db.Column(db.String(1500))
    container = db.Column(db.String(300))
    isDeclined = db.Column(db.Boolean, default=False)
    isPending = db.Column(db.Boolean, default=False)
    isDone = db.Column(db.Boolean, default=False)
    isAccepted = db.Column(db.Boolean, default=False)
    requester = db.Column(db.String(1500))
    owner = db.Column(db.String(1500))


class Quote(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    timeCreated = db.Column(db.Date, default=datetime.utcnow)
    items = db.Column(db.String(1500))
    container = db.Column(db.String(300))
    isReady = db.Column(db.Boolean, default=False)
    isDeclined = db.Column(db.Boolean(), default=False)

    # user accepts and converts to mark this as "accepted"

    isAccepted = db.Column(db.Boolean(), default=False)
    isExpired = db.Column(db.Boolean(), default=False)
    buyer = db.Column(db.String(1500))
    vendor = db.Column(db.String(1500))
    lastEdited = db.Column(db.Date, default=datetime.utcnow)
    valid_until = db.Column(db.Date)
    req_id = db.Column(db.Integer)
    lead_time = db.Column(db.Integer)

    def is_expired(self):

        today = datetime.today().date()

        if today > self.valid_until:

            # set the isExpired to True
            self.isExpired = True
            db.session.commit()

            return True

        else:

            return False



