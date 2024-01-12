from app import (app, render_template,
                 url_for, redirect,
                 request, make_response,
                 send_file, jsonify,
                 flash, session)

from flask_login import (login_required, login_manager,
                         login_user, logout_user,
                         current_user)
from app import db, mongo, redis_client, documents_changelog_store

from sqlalchemy.orm import joinedload

from app.aux_models import Message
from app.models import Tenant, Inventory, PO, Supplier, User, Warehouse

from pprint import pprint
from datetime import datetime
import json
from bson.json_util import dumps
import redis
from redis.exceptions import ConnectionError


@app.route('/api/messages/unread')
@login_required
def unread_messages():

    unread_system_msgs = len(
        Message.query.filter(
            Message.isRead == False,
            Message.owner == current_user.email,
            Message.kind == "system").all()
    )

    unread_user_msgs = len(

        Message.query.filter(
            Message.isRead == False,
            Message.owner == current_user.email,
            Message.kind == "user").all()
    )

    return {"unread_system_msgs": unread_system_msgs,
            "unread_user_msgs": unread_user_msgs}


@app.route('/api/items/<string:tenant_id>/<string:supplier_uuid>', methods=['GET'])
@login_required
def get_items_by_supplier(tenant_id, supplier_uuid):

    # Ensure we got UUIDs as inputs
    try:
        tenant_id = int(tenant_id)
    except ValueError:
        return jsonify({'error': 'Invalid tenant ID'}), 400

    import uuid
    try:
        uuid.UUID(supplier_uuid)
    except ValueError:
        return jsonify({'error': 'Invalid supplier UUID'}), 400

    # Fetch the supplier from the database
    supplier = Supplier.query.filter_by(tenant_id=tenant_id, uuid=supplier_uuid).first()
    if not supplier:
        return jsonify({'error': 'No supplier found with this UUID for this tenant'}), 404

    # Fetch the items related to this supplier
    items = Inventory.query.options(joinedload('suppliers')).filter(Inventory.suppliers.any(id=supplier.id)).all()

    if items:
        item_list = [{
            'id': item.id,
            'name': item.name,
            'en_name': item.en_name,
            'brand': item.brand,
            'category': item.category,
            'en_category': item.en_category,
            'description': item.description,
            'price': item.price,
            'vat': item.vat,
            'gtin': item.gtin,
            'colli_barcode': item.colli_barcode,
            'item_code': item.item_code,
            'hs_code': item.hs_code,
            'origin': item.origin,
            'img': item.img if "https://" in item.img else
                url_for('static', filename=f"img/product_images/{item.img}"),
            'is_available': item.is_available,
            'time_created': item.time_created.isoformat(),
            'palletized_quantity': item.palletized_quantity,
            'palletized_gw': item.palletized_gw,
            'pallet_length': item.pallet_length,
            'pallet_width': item.pallet_width,
            'pallet_height': item.pallet_height,
            'pu_quantity': item.pu_quantity,
            'pu_gw': item.pu_gw,
            'pu_length': item.pu_length,
            'pu_width': item.pu_width,
            'pu_height': item.pu_height,
            'stock_quantity': item.stock_quantity,
            'stock_location': item.stock_location,
            'uuid': item.uuid
        } for item in items]

        return jsonify({'items': item_list}), 200
    else:
        return jsonify({'error': 'No items found for this supplier'}), 404


''''
FROM CLIENT
This sends a POST request to '/api/purchase_order' 
with the Purchase Order data. Make sure to replace 
'/api/purchase_order' with the 
correct endpoint that accepts the PO data on your server.
'''


@app.route('/api/purchase_order', methods=['POST'])
@login_required
def handle_purchase_order():
    # Get the JSON data from the request
    data = request.get_json()

    # Checking if data is not None
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Create a new PO object / make sure that tenant_id is assigned before the PO object is instantiated
    tenant_id = data.get('tenant_id')
    if tenant_id is None:
        return jsonify({"error": "Tenant ID is required"}), 400

    po = PO(tenant_id=tenant_id)

    # Set the attributes of the PO object based on the received data
    po.buyer = current_user.user_name
    po.supplier_notes = data.get('supplier_notes', '')
    po.warehouse_notes = data.get('warehouse_notes', '')
    po.subtotal = data.get('subtotal', 0)  # Set the subtotal attribute
    po.total = data.get('total', 0)  # Set the total attribute
    po.tax_amount = data.get("tax_amount", 0)
    po.reference = data.get("reference", "No reference specified")

    # Set the warehouse_id attributes
    warehouse_id = data.get('warehouse_id')
    if warehouse_id is not None:
        po.warehouse_id = warehouse_id

    po.status = "Not Sent"

    supplier_uuid = data.get("supplierUUID")
    if not supplier_uuid:
        return jsonify({"error": "Supplier UUID is required"}), 400

    supplier = Supplier.query.filter_by(tenant_id=tenant_id, uuid=supplier_uuid).first()
    if supplier is None:
        return jsonify({"error": "Supplier not found"}), 404

    po.supplier_id = supplier.id

    # Dumps items data as JSON string
    items = data.get("items")
    if items is not None:
        po.items = json.dumps(items)

    # Query for an existing Inventory object or create a new one if none exists.
    for item in items or []:
        inventory = Inventory.query.filter_by(tenant_id=tenant_id,
                                              gtin=item.get('barcode')).first()
        if inventory is None:
            inventory = Inventory(tenant_id=tenant_id)
            inventory.gtin = item.get('barcode', "")
            inventory.name = item.get('item_name', "")
            inventory.price = item.get("purchase_price", 0)
            inventory.suppliers.append(supplier)
            inventory.vat = item.get("tax_rate", 0)

            db.session.add(inventory)

    db.session.add(po)

    db.session.commit()

    # Return a message indicating success
    flash(f"new PO {po.po_number} has been created!", category="success")

    return jsonify({'message': 'Purchase Order created successfully', 'po_number': po.po_number})


@app.route('/api/purchase_order/update', methods=['POST'])
@login_required
def update_purchase_order():
    # Get the JSON data from the request
    data = request.get_json()

    # Checking if data is not None
    if not data:
        return jsonify({"error": "No data entered by the user"}), 400

    # Query for the PO with the given UUID
    po_uuid = data.get('poUUID')
    if po_uuid is None:
        return jsonify({"error": "PO UUID is required"}), 400

    po = PO.query.filter_by(uuid=po_uuid).first()

    # before an update / modification
    previous_items = json.loads(po.items)

    # Make sure that tenant_id is assigned before the PO object is updated
    tenant_id = data.get('tenant_id')
    if tenant_id is None:
        return jsonify({"error": "Tenant ID is required"}), 400

    # Set the attributes of the PO object based on the received data
    po.buyer = current_user.user_name
    po.supplier_notes = data.get('supplier_notes', '')
    po.warehouse_notes = data.get('warehouse_notes', '')
    po.subtotal = data.get('subtotal', 0)  # Set the subtotal attribute
    po.total = data.get('total', 0)  # Set the total attribute
    po.tax_amount = data.get("tax_amount", 0)
    po.reference = data.get("reference", "No reference specified")

    # Set the warehouse_id attributes
    warehouse_id = data.get('warehouse_id')
    if warehouse_id is not None:
        po.warehouse_id = warehouse_id

    po.status = "Modified by user"

    supplier_uuid = data.get("supplierUUID")
    if not supplier_uuid:
        return jsonify({"error": "Supplier UUID is required"}), 400

    supplier = Supplier.query.filter_by(tenant_id=tenant_id, uuid=supplier_uuid).first()
    if supplier is None:
        return jsonify({"error": "Supplier not found"}), 404

    po.supplier_id = supplier.id

    # Dumps items data as JSON string - the new items of this PO
    items = data.get("items")
    current_items = []
    if items is not None:
        po.items = json.dumps(items)
        current_items = items

    # Query for an existing Inventory object or create a new one if none exists.
    for item in items or []:
        # if this tenant has so such item associated with this supplier, creating a new one
        inventory = Inventory.query.filter_by(tenant_id=tenant_id,
                                              gtin=item.get('barcode')).first()
        if inventory is None:
            inventory = Inventory(tenant_id=tenant_id)
            inventory.gtin = item.get('barcode', "")
            inventory.name = item.get('item_name', "")
            inventory.price = item.get("purchase_price", 0)
            inventory.vat = item.get("tax_rate", 0)

            db.session.add(inventory)

    try:
        db.session.commit()

        # write the change log into redis server
        po_log = {
            "previous_items": previous_items,
            "current_items": current_items,
            "timestamp": datetime.utcnow().isoformat(),
            "modified_by": current_user.user_name,
            "tenant_id": tenant_id
            }
        # error handling for redis connection if failed
        try:
            # Add the change log to the Redis list
            documents_changelog_store.lpush(po.uuid, json.dumps(po_log))

        except redis.exceptions.RedisError as e:
            print(f'Error while writing to Redis: {str(e)}')

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"error": "PO failed to update. Please retry"}), 404

    # Return a message indicating success
    flash(f"PO {po.po_number} has been updated!", category="success")

    return jsonify({'message': 'Purchase Order updated successfully', 'po_number': po.po_number})


@app.route('/api/po/emails', methods=['POST', "GET"])
@login_required
def get_stakeholder_emails():
    data = request.get_json()

    # # Check if UUID is present in request data
    # if 'po_uuid' not in data:
    #     return jsonify({'error': 'PO UUID missing'}), 400

    # # Get the PO from the database
    # po = PO.query.filter_by(uuid=data['po_uuid']).first()

    po = PO.query.filter_by(uuid='0a12bd5c-e496-4179-80bc-d2ef602aaa1f').first()

    # Check if the PO exists
    if not po:
        return jsonify({'error': 'PO not found'}), 404

    # Fetch the supplier, warehouse and users related to the PO
    supplier = Supplier.query.get(po.supplier_id)
    warehouse = po.warehouse

    users = User.query.filter_by(tenant_id=po.tenant_id).all()

    # Extract emails and return
    emails = [user.email for user in users]
    if supplier:
        emails.append(supplier.email)
    if warehouse:
        emails.append(warehouse.email)

    return jsonify({'emails': emails}), 200


@app.route('/ping', methods=['GET'])
def ping():
    try:
        # The is master command is cheap and does not require auth.
        mongo.cx.admin.command('ismaster')
        return dumps({'message': 'Pinged your deployment. You successfully connected to MongoDB!'}), 200
    except Exception as e:
        return dumps({'error': str(e)}), 500


@app.route('/ping/redis/set/status/mapping')
@login_required
def redis_set_status_mapping():

    status_icons = {

        'draft': {"icon": 'fas fa-file-alt', 'animation': ""},

        'bug': {"icon": '<i class="fa-solid fa-bug fa-xl" style="color: #de4917;"></i>"',
                'animation': "animate__animated animate__pulse animate__infinite"},

        'pending_approval': 'fas fa-clock',
        'approved': 'fas fa-check-circle',
        'in_progress': 'fas fa-cogs',
        'shipped': 'fas fa-truck',
        'delivered': 'fas fa-check-square',
        'cancelled': 'fas fa-times-circle'
    }

    for status, icon in status_icons.items():
        redis_client.set(status, icon)

    return {"status": "ok"}, 200


# config super admin access
@app.route('/ping/redis/store/access')
@login_required
def redis_store_access():

    value = redis_client.get('key')
    return {"status": "ok"}, 200
