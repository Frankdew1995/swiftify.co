var addRowBtn = document.getElementById("addRowBtn");
var tableBody = document.querySelector("#form-table tbody");
var subtotalInput = document.getElementById("subtotal");
var taxAmountInput = document.getElementById("tax-amount");
var totalInput = document.getElementById("total");
var autoFillBtn = document.getElementById("autoFillBtn");
var submitBtn = document.getElementById("submitBtn");
var supplier_uuid = document.querySelector("#supplierUUID");


// Then, add an event listener for the 'change' event:
// The 'change' event triggers whenever the value of the supplier uuid dropdown changes.
// When this happens, the callback function is executed, clearing the content of the tableBody by setting its innerHTML to an empty string.
supplier_uuid.addEventListener("change", function() {
    tableBody.innerHTML = ""; // clear the table body
});




// event delegation inner the table body, With this code, any click event that
// originates from a button with the "delete-btn" class within the table body will delete the row,
// even if the row was added dynamically after the event listener was bound.
tableBody.addEventListener("click", function(event) {
    if (event.target.classList.contains("delete-btn")) {
        var rowToDelete = event.target.parentNode.parentNode; // Gets the row
        tableBody.removeChild(rowToDelete);
        updateTotals();
    }
});




// a lot of functions
addRowBtn.addEventListener("click", function() {
  var newRow = document.createElement("tr");
  var imageCell = document.createElement("td");
  var itemCell = document.createElement("td");
  var barcodeCell = document.createElement("td");
  var quantityCell = document.createElement("td");
  var purchasePriceCell = document.createElement("td");
  var taxRateCell = document.createElement("td");
  var subtotalAmountCell = document.createElement("td");
  var actionCell = document.createElement("td");
  var deleteBtn = document.createElement("button");

  imageCell.innerHTML = "<img src='' alt='' class='product-image'>";
  itemCell.innerHTML = "<input type='text' class='item-input' placeholder='Enter item'>";
  barcodeCell.innerHTML = "<input type='text' class='barcode-input' placeholder='Enter barcode'>";
  quantityCell.innerHTML = "<input type='number' class='quantity-input' placeholder='Enter quantity'>";
  purchasePriceCell.innerHTML = "<input type='number' class='purchase-price-input' placeholder='Enter purchase price'>";
  taxRateCell.innerHTML = "<input type='number' class='tax-rate-input' placeholder='Enter tax rate'>";
  subtotalAmountCell.innerHTML = "<input type='number' class='subtotal-amount-input' placeholder='Subtotal' readonly>";

  deleteBtn.innerHTML = "X";
  deleteBtn.classList.add("delete-btn");
  deleteBtn.addEventListener("click", function() {
    tableBody.removeChild(newRow);
    updateTotals();
  });

  newRow.appendChild(imageCell);
  newRow.appendChild(itemCell);
  newRow.appendChild(barcodeCell);
  newRow.appendChild(quantityCell);
  newRow.appendChild(purchasePriceCell);
  newRow.appendChild(taxRateCell);
  newRow.appendChild(subtotalAmountCell);
  newRow.appendChild(actionCell);
  actionCell.appendChild(deleteBtn);

  tableBody.appendChild(newRow);
  updateSubtotal(newRow);
  updateTotals();
});

tableBody.addEventListener("input", function(event) {
  var target = event.target;
  if (target.classList.contains("quantity-input") || target.classList.contains("purchase-price-input") || target.classList.contains("tax-rate-input")) {
    updateSubtotal(target.parentNode.parentNode);
    updateTotals();
  }
});

function updateSubtotal(row) {
  var quantity = parseInt(row.querySelector(".quantity-input").value);
  var purchasePrice = parseFloat(row.querySelector(".purchase-price-input").value);
  var taxRate = parseFloat(row.querySelector(".tax-rate-input").value);
  var subtotalAmountCell = row.querySelector(".subtotal-amount-input");

  var subtotalAmount = quantity * purchasePrice;
  subtotalAmountCell.value = subtotalAmount.toFixed(2);
}

function updateTotals() {
  var rows = tableBody.querySelectorAll("tr");
  var subtotal = 0;
  var totalTaxAmount = 0;

  rows.forEach(function(row) {
    var subtotalAmount = parseFloat(row.querySelector(".subtotal-amount-input").value);
    var taxRate = parseFloat(row.querySelector(".tax-rate-input").value);

    if (!isNaN(subtotalAmount)) {
      subtotal += subtotalAmount;
    }

    if (!isNaN(taxRate)) {
      var taxAmount = (subtotalAmount * taxRate) / 100;
      totalTaxAmount += taxAmount;
    }
  });


  var total = subtotal + totalTaxAmount;

  subtotalInput.value = subtotal.toFixed(2);
  taxAmountInput.value = totalTaxAmount.toFixed(2);
  totalInput.value = total.toFixed(2);
}

autoFillBtn.addEventListener("click", async function () {
  // Get the supplier UUID and tenant ID
  var supplier_uuid = document.querySelector("#supplierUUID").value;
  var tenant_id = document.querySelector("#poSender").textContent;

  // Make a GET request to the new endpoint
  const response = await fetch(`/api/items/${tenant_id}/${supplier_uuid}`, {
      method: 'GET',
  });

  // Parse the JSON response
  const responseData = await response.json();

  if (response.ok) {
      // Clear the existing table rows
      tableBody.innerHTML = "";

      // Iterate over the items and create new table rows
      responseData.items.forEach(item => {
          addRow(item);
      });
  } else {
      console.error('Failed to fetch items:', responseData.error);
  }

  });


// add row
function addRow(item) {
  // Create a new table row and fill it with data
  var row = document.createElement("tr");

  // Fill the row with data
  row.innerHTML = `
      <td><img src="${item.img}" alt="Product Image" class="product-image"></td>
      <td><input type="text" class="item-input" value="${item.name}"></td>
      <td><input type="text" class="barcode-input" value="${item.gtin}"></td>
      <td><input type="number" class="quantity-input" value="${item.stock_quantity}"></td>
      <td><input type="number" class="purchase-price-input" value="${item.price}"></td>
      <td><input type="number" class="tax-rate-input" value="${item.vat}"></td>
      <td><input type="number" class="subtotal-amount-input" value="${item.subtotal}" readonly></td>
      <td>
          <button class="delete-btn">X</button>
      </td>
  `;

  // Append the row to the table
  tableBody.appendChild(row);

  // Update totals
  updateSubtotal(row);
  updateTotals();
}

submitBtn.addEventListener("click", function() {
  var rows = tableBody.querySelectorAll("tr");
  var purchaseOrder = [];

  rows.forEach(function(row) {
    var item = {
      image: row.querySelector(".product-image").src,
      item_name: row.querySelector(".item-input").value,
      barcode: row.querySelector(".barcode-input").value,
      quantity: parseInt(row.querySelector(".quantity-input").value),
      purchase_price: parseFloat(row.querySelector(".purchase-price-input").value),
      tax_rate: parseFloat(row.querySelector(".tax-rate-input").value),
      subtotal: parseFloat(row.querySelector(".subtotal-amount-input").value)
    };
    purchaseOrder.push(item);
  });

  var poData = {
    tenant_id: parseInt(document.querySelector("#poSender").textContent),
    supplierUUID: document.querySelector("#supplierUUID").value,
    order_date: document.querySelector("#poDate").value,
    warehouse_notes: document.querySelector("#supplierNotes").value,
    supplier_notes: document.querySelector("#warehouseNotes").value,
    warehouse_id: parseInt(document.querySelector("#warehouse").value),
    reference: document.querySelector("#internalReference").value,
    items: purchaseOrder,
    subtotal: parseFloat(subtotalInput.value),
    tax_amount: parseFloat(taxAmountInput.value),
    total: parseFloat(totalInput.value)
  };

  console.log(poData);

  async function sendPurchaseOrder(poData) {
  // Send the data to the server
  const response = await fetch('/api/purchase_order', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(poData),
  });

  if (response.ok) {
    console.log('Purchase Order successfully sent');
    window.location.href = '/users/view/pos';  // Redirects to the given page

  } else {
    console.error('Failed to send Purchase Order:', await response.json());
  }
}

// Usage:
// Assume we have PO data
sendPurchaseOrder(poData);





});
