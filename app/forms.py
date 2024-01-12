
from flask_wtf import FlaskForm

from app.utils import return_currencies

from flask_wtf.file import FileField, FileAllowed, FileRequired

from wtforms import (StringField, BooleanField, FloatField,
                     IntegerField, SubmitField,
                     TextAreaField, PasswordField, SelectField, SelectMultipleField,
                     DecimalField, RadioField, TimeField, DateTimeField, HiddenField)

from wtforms.validators import DataRequired, Email, EqualTo, Required, ValidationError, Length

from wtforms.fields.html5 import DateField

from flask_login import current_user, login_user


class SubscribeForm(FlaskForm):

    email = StringField(validators=[DataRequired(), Email()])

    submit = SubmitField("Tune in!")


class VendorSignUpForm(FlaskForm):

    full_name = StringField("Full Name", validators=[DataRequired()])

    company_name = StringField("Company Name", validators=[DataRequired()])

    email = StringField(validators=[DataRequired(), Email()])

    import pycountry

    countries = [(country.name, country.name) for country in pycountry.countries]

    country = SelectField("Country",
                          validators=[DataRequired()],
                          choices=countries)

    business_incorporation_doc = FileField(
                                    "Business Incorporation Certificate",
                                    validators=[DataRequired(),
                                                FileAllowed(["pdf", "jpg",
                                                            "jpeg", "png"])])

    password = PasswordField('Password',
                             validators=[DataRequired()])

    password2 = PasswordField('Confirm password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                                  message="Passwords didn't match")])

    submit = SubmitField("Sign up")


class UserSignUpForm(FlaskForm):

    full_name = StringField("Full Name", validators=[DataRequired()])

    company_name = StringField("Company Name", validators=[DataRequired()])

    email = StringField(validators=[DataRequired(), Email()])

    import pycountry

    countries = [(country.name, country.name) for country in pycountry.countries]

    country = SelectField("Country",
                          validators=[DataRequired()],
                          choices=countries)

    password = PasswordField('Password',
                             validators=[DataRequired()])

    password2 = PasswordField('Confirm password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                                  message="Passwords didn't match")])

    submit = SubmitField("Sign up")


class UserForm(FlaskForm):
    user_name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role_id = SelectField('Role')
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    tenant_id = HiddenField('Tenant')
    submit = SubmitField('Add User')
    update = SubmitField('Update User')


class SignInForm(FlaskForm):

    email = StringField(validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired()])

    remember_me = BooleanField(u'Remember me')

    submit = SubmitField("Sign in")

    sign_in_passwordless = SubmitField("Sign in Without Password")


class ResetPasswordForm(FlaskForm):

    email = StringField(validators=[DataRequired(), Email()])

    password = PasswordField('New Password', validators=[DataRequired()])

    password2 = PasswordField('Repeat New Password',
                              validators=[DataRequired(),
                                          EqualTo('password',
                                                  message="Passwords didn't match")])

    submit = SubmitField("Update password")


class ResetRequestForm(FlaskForm):

    email = StringField(validators=[DataRequired(), Email()])

    submit = SubmitField("Request reset")


class SendEmailForm(FlaskForm):

    email = StringField(validators=[DataRequired(message="Please input recipient email address"),
                                    Email(message="This seems not to be an valid email")])

    submit = SubmitField("Send")


class SettingsForm(FlaskForm):

    name = StringField("Your Name",
                       validators=[DataRequired(message="Please enter company name")])

    email = StringField(validators=[DataRequired(message="Please input your email address"),
                                    Email(message="This seems not to be an valid email")])

    company_name = StringField("Company Name",
                               validators=[DataRequired(message="Please enter company name")])

    city = StringField("City",
                       validators=[DataRequired(message="City field required!")])

    address = StringField(u"Address Line", validators=[DataRequired()])

    country = StringField("Country of registration",
                          validators=[DataRequired(message="Country of registration field required!")])

    zip_code = StringField("Postal Code",
                           validators=[DataRequired(message="Postal Code field required!")])

    state_or_province = StringField("State or Province",
                                    validators=[DataRequired(message="State or Province field required!")])

    tax_id = StringField("VAT ID. / Tax Number")

    eori = StringField("EORI ID")

    iban = StringField("IBAN or Account Number")

    swift_or_bic_no = StringField("SWIFT Code or BIC")

    bank_name = StringField("Banking Institution")

    bank_address = StringField("Address of Banking Institution")

    tax_rate1 = FloatField("Tax Rate 1 (%)")

    tax_rate2 = FloatField("Tax Rate 2 (%)")

    default_currency = SelectField("Default currency", choices=return_currencies())

    logo = FileField(u"LOGO",
                     validators=[FileAllowed(["jpg", "jpeg", "png"],
                                             message="Only jpg, jpeg and png formats are allowed.")])

    salesbinder_api_key = StringField("Your SalesBinder API Key")

    salesbinder_subdomain_name = StringField("Your SalesBinder Subdomain Name")

    submit = SubmitField("Save & update")


class SendInvoiceForm(FlaskForm):

    to = StringField("to",
                     validators=[DataRequired(message="Please input recipient email address"),
                                 Email(message="This seems not to be an valid email")])

    from_ = StringField("from",
                        validators=[DataRequired(message="Please input sender email address"),
                                    Email(message="This seems not to be an valid email")])

    invoice_id = StringField("Invoice Number", validators=[DataRequired()])

    cc = StringField("cc")

    subject = StringField("Subject", validators=[DataRequired(
            message="Subject can't be empty!")])

    message = TextAreaField("Message",
                            validators=[DataRequired(message="Please enter a message")])

    submit = SubmitField("Send")


class SendPOForm(FlaskForm):

    to = StringField("to",
                     validators=[DataRequired(message="Please input recipient email address"),
                                 Email(message="This seems not to be an valid email")])

    from_ = StringField("from",
                        validators=[DataRequired(message="Please input sender email address"),
                                    Email(message="This seems not to be an valid email")])

    po_number = StringField("PO Number", validators=[DataRequired()])

    cc = StringField("cc")

    subject = StringField("Subject", validators=[DataRequired(
            message="Subject can't be empty!")])

    message = TextAreaField("Message",
                            validators=[DataRequired(message="Please enter a message")])

    send = SubmitField("Send")

    submit = SubmitField("Save")


class AddAccountForm(FlaskForm):

    name = StringField("Company Name",
                       validators=[DataRequired(message="Please enter the company name")])

    contact_person = StringField("Contact Person",
                                 validators=[])

    email = StringField("Contact Email",
                        validators=[DataRequired(message="Please enter contact email address"), Email()])

    phone = StringField("Office Phone")

    city = StringField("City", validators=[DataRequired()])

    street_n_no = StringField(u"Address Line", validators=[DataRequired()])

    import pycountry

    countries = [(country.name, country.name) for country in pycountry.countries]

    country = SelectField("Country",
                          validators=[DataRequired()],
                          choices=countries)

    zip_code = StringField("Postal Code", validators=[DataRequired()])

    state_or_province = StringField("State or Province")

    vat_id = StringField("VAT ID. / Tax Number")

    tax_rate = FloatField("Tax Rate(%)")

    tax_rate_1 = FloatField("Tax Rate #1 (%)")

    tax_rate_2 = FloatField("Tax Rate #2 (%)")

    # add some data fields for logistics and warehouse

    warehouse_address = StringField(u"Warehouse Address")
    same_as_company_address = BooleanField(u'Same as the company address', default=True)
    warehouse_start_hours = TimeField("Warehouse opening from")
    warehouse_end_hours = TimeField("Warehouse closing at")

    submit = SubmitField("Save & Add")
    update = SubmitField("Save & Update")


class AddProductForm(FlaskForm):

    name = StringField("Product Name *", validators=[DataRequired()])
    gtin = StringField("Item Barcode *", validators=[DataRequired()])
    colli_barcode = StringField("Colli Barcode")

    desc = TextAreaField("Description")

    stock_quantity = IntegerField("Quantity in stock *", validators=[DataRequired()])

    purchase_price = FloatField("Purchase Price *", validators=[DataRequired()])

    # SKU Data
    volume = FloatField("Volume (ml)")
    net_weight = FloatField("Net Weight (g)")
    length = FloatField("Length (cm)")
    width = FloatField("Width (cm)")
    height = FloatField("Height (cm)")

    # PU data
    pu = IntegerField("Packing units")
    pu_gw = FloatField("packing unit Gross Weight(kg)")
    pu_length = FloatField("packing unit length(cm)")
    pu_width = FloatField("packing unit width(cm)")
    pu_height = FloatField("packing unit height(cm)")

    # Palletization Data
    palletized_quantity = IntegerField("Quantity per pallet *", validators=[DataRequired()])
    palletized_gw = FloatField("Gross Weight per pallet(kg) *", validators=[DataRequired()])
    pallet_length = FloatField("Length per pallet(cm) *", validators=[DataRequired()])
    pallet_width = FloatField("Width per pallet(cm)n *", validators=[DataRequired()])
    pallet_height = FloatField("Height per pallet(cm) *", validators=[DataRequired()])

    ingredients = TextAreaField("Ingredients")
    manufacturer = StringField("Manufacturer")
    hs_codes = StringField("HS Code(s)")
    tax_rate = FloatField("Tax Rate (%)")

    import pycountry

    countries = [(country.name, country.name) for country in pycountry.countries]

    country = SelectField("Country of origin",
                          validators=[DataRequired()],
                          choices=countries,
                          )

    image = FileField("Upload Product Image",
                      validators=[FileAllowed(["jpg", "jpeg", "png"],
                                              message="Only jpg, jpeg and png formats are allowed.")])

    submit = SubmitField("Add")


# form for adding a warehouse location
class AddWarehouseForm(FlaskForm):

    warehouse_name = StringField("Warehouse Name", validators=[DataRequired()])

    address = StringField("Address", validators=[DataRequired()])

    city = StringField("City", validators=[DataRequired()])

    state = StringField("State")

    zipcode = StringField("Postal Code", validators=[DataRequired()])

    notes = TextAreaField("Notes")

    operating_hours = StringField("Warehouse Operating Hours")

    warehouse_start_hours = TimeField("Warehouse opening from")
    warehouse_end_hours = TimeField("Warehouse closing at")

    import pycountry

    warehouse_manager = StringField("Manager", validators=[DataRequired()])

    email = StringField("Email", validators=[Email(), DataRequired()])

    countries = [(country.name, country.name) for country in pycountry.countries]

    country = SelectField("Country",
                          validators=[DataRequired()],
                          choices=countries)

    submit = SubmitField("Save Warehouse")


# Form used to reject the quote from server side
class RejectQuoteForm(FlaskForm):

    submit = SubmitField("Confirm & Break the heart")


class AddFreightForm(FlaskForm):

    shipper_name = StringField("Company Name",
                               validators=[DataRequired(message="Please enter company name")])

    shipper_contact_person = StringField("Contact Person",
                                 validators=[DataRequired(message="Please enter a contact person")])

    shipper_email = StringField("Contact Email",
                        validators=[DataRequired(message="Please enter customer contact email address"), Email()])

    shipper_phone = StringField("Contact Phone")

    shipper_city = StringField("City")

    shipper_address = StringField(u"Address Line")

    import pycountry

    countries = [(country.name, country.name) for country in pycountry.countries]

    shipper_country = SelectField("Country",
                          validators=[DataRequired()],
                          choices=countries)

    zip_code = StringField("Postal Code")

    state_or_province = StringField("State or Province")

    submit = SubmitField("Save & Add")


class CreatePOForm(FlaskForm):
    items = SelectField('Items', choices=[])  # choices will be populated dynamically
    supplier = SelectField('Supplier', choices=[])  # choices will be populated dynamically
    valid_until = DateTimeField('Valid Until', validators=[DataRequired()])
    lead_time = IntegerField('Lead Time', validators=[DataRequired()])
    supplier_notes = TextAreaField('Supplier Notes', validators=[Length(max=2000)])
    warehouse_notes = TextAreaField('Warehouse Notes', validators=[Length(max=2000)])
    expected = DateTimeField('Expected Delivery Date', validators=[DataRequired()])
    subtotal = FloatField('Subtotal', validators=[DataRequired()])
    discount = FloatField('Discount')
    shipping_charges = FloatField('Shipping Charges', validators=[DataRequired()])
    total = FloatField('Total', validators=[DataRequired()])
    warehouse = SelectField('Receiving Warehouse', choices=[])  # choices will be populated dynamically
    submit = SubmitField('Create Purchase Order')


class FileUploadForm(FlaskForm):
    file = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Upload File')

