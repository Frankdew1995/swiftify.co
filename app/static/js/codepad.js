var addRowBtn = document.getElementById("addRowBtn");
var tableBody = document.querySelector("#form-table tbody");
var subtotalInput = document.getElementById("subtotal");
var taxAmountInput = document.getElementById("tax-amount");
var totalInput = document.getElementById("total");
var autoFillBtn = document.getElementById("autoFillBtn");
var submitBtn = document.getElementById("submitBtn");
var supplierUUID = document.getElementById("supplierUUID");

// Clear the table body when the supplier UUID changes
supplierUUID.addEventListener("change", function() {
    tableBody.innerHTML = "";
});

// Event delegation for deleting rows
tableBody.addEventListener("click", function(event) {
    if (event.target.classList.contains("delete-btn")) {
        var rowToDelete = event.target.parentNode.parentNode;
        tableBody.removeChild(rowToDelete);
        updateTotals();
    }
});

// Add a new row
addRowBtn.addEventListener("click", function() {
    var newRow = document.createElement("tr");
    newRow.innerHTML = `
        <td><img src="" alt="" class="product-image"></td>
        <td><input type="text" class="item-input" placeholder="Enter item"></td>
        <td><input type="text" class="barcode-input" placeholder="Enter barcode"></td>
        <td><input type="number" class="quantity-input" placeholder="Enter quantity"></td>
        <td><input type="number" class="purchase-price-input" placeholder="Enter purchase price"></td>
        <td><input type="number" class="tax-rate-input" placeholder="Enter tax rate"></td>
        <td><input type="number" class="subtotal-amount-input" placeholder="Subtotal" readonly></td>
        <td><button class="delete-btn">X</button></td>
    `;

    tableBody.appendChild(newRow);
    updateTotals();
});

// Update the subtotal and totals when input values change
tableBody.addEventListener("input", function(event) {
    var target = event.target;
    if (target.classList.contains("quantity-input") || target.classList.contains("purchase-price-input") || target.classList.contains("tax-rate-input")) {
        updateSubtotal(target.parentNode.parentNode);
        updateTotals();
    }
});

// Function to update the subtotal for a row
function updateSubtotal(row) {
    var quantity = parseInt(row.querySelector(".quantity-input").value);
    var purchasePrice = parseFloat(row.querySelector(".purchase-price-input").value);
    var taxRate = parseFloat(row.querySelector(".tax-rate-input").value);
    var subtotalAmountCell = row.querySelector(".subtotal-amount-input");

    var subtotalAmount = quantity * purchasePrice;
    subtotalAmountCell.value = subtotalAmount.toFixed(2);
}

// Function to update the subtotal, tax amount, and total
function updateTotals() {
    var rows = tableBody.querySelectorAll("tr");
    var subtotal = 0;
    var taxAmount = 0;
    var total = 0;

    rows.forEach(function(row) {
        var subtotalAmount = parseFloat(row.querySelector(".subtotal-amount-input").value);
        var taxRate = parseFloat(row.querySelector(".tax-rate-input").value);

        if (!isNaN(subtotalAmount)) {
            subtotal += subtotalAmount;
            if (!isNaN(taxRate)) {
                var tax = (subtotalAmount * taxRate) / 100;
                taxAmount += tax;
            }
        }
    });

    total = subtotal + taxAmount;

    subtotalInput.value = subtotal.toFixed(2);
    taxAmountInput.value = taxAmount.toFixed(2);
    totalInput.value = total.toFixed(2);
}

// Auto-fill button click event handler
autoFillBtn.addEventListener("click", async function() {
    var supplierUUIDValue = supplierUUID.value;
    var tenantID = document.getElementById("poSender").textContent;

    try {
        var response = await fetch(`/api/items/${tenantID}/${supplierUUIDValue}`);
        var data = await response.json();

        if (response.ok) {
            tableBody.innerHTML = ""; // Clear the table body

            data.items.forEach(function(item) {
                addRow(item); // Add a new row for each item
            });
        } else {
            console.error("Failed to fetch items:", data.error);
        }
    } catch (error) {
        console.error("Failed to fetch items:", error);
    }
});

// Submit button click event handler
submitBtn.addEventListener("click", function() {
    var rows = tableBody.querySelectorAll("tr");
    var items = [];

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

        items.push(item);
    });

    var formData = new FormData();
    formData.append("supplier_notes", document.querySelector("#supplierNotes").value);
    formData.append("warehouse_notes", document.querySelector("#warehouseNotes").value);
    formData.append("items", JSON.stringify(items));

    fetch(`/po/update/${poID}`, {
        method: "POST",
        body: formData
    })
        .then(function(response) {
            if (response.ok) {
                console.log("Purchase Order updated successfully");
                window.location.href = "/users/view/pos"; // Redirect to the PO list page
            } else {
                console.error("Failed to update Purchase Order:", response.status);
            }
        })
        .catch(function(error) {
            console.error("Failed to update Purchase Order:", error);
        });
});
