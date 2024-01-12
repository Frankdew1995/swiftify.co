console.log("Ok");



// get the tax rate from local storage

let infoInputBtns = document.querySelectorAll(".info-input");



// this function sets the tax options
function setTaxRateOptions(){

  var tax1 = localStorage.getItem('tax1');

  var tax2 = localStorage.getItem('tax2');

  console.log(tax1, tax2);

  const taxRate1 = document.getElementById("taxRate1");

  taxRate1.value = parseInt(tax1) / 100;
  taxRate1.textContent = tax1.toString() + "%";

  const taxRate2 = document.getElementById("taxRate2");


  taxRate1.value = parseInt(tax2) / 100;
  taxRate1.textContent = tax2.toString() + "%";

  console.log(taxRate1, taxRate2);


};


setTaxRateOptions();



// add a new method to date object
Date.prototype.addDays = function(days){
  this.setDate(this.getDate() + parseInt(days));
  return this;
}


// set the cur date and due date accordingly
function setDateAndDueDate(){


  var date = new Date();

  var year = date.getFullYear().toString();

  // month counts start from 0
  var month = (date.getMonth() + 1).toString().padStart(2, '0');

  var curD = date.getDate().toString().padStart(2, '0');

  const curDate  = document.getElementById("invoiceDate");

  curDate.value = year + "-" + month + "-" + curD;


};

setDateAndDueDate();


// set the due date
function setDueDate(event){


  const curDate  = document.getElementById("invoiceDate").value;

  var date = new Date(curDate);

  // calculates the due date from the input terms by listening to input event
  var dueDate = date.addDays(event.target.value);

  console.log(dueDate);

  var dueYear = dueDate.getFullYear().toString();

  // month counts start from 0
  var dueMonth = (dueDate.getMonth() + 1).toString().padStart(2, '0');

  var dueD = dueDate.getDate().toString().padStart(2, '0');

  console.log(dueD);

  const invoiceDueDate = document.getElementById("dueDate");

  invoiceDueDate.value = dueYear + "-" + dueMonth + "-" + dueD;


};



const inputTerms = document.getElementById("terms");

const curDate  = document.getElementById("invoiceDate");

inputTerms.addEventListener("input", setDueDate);

inputTerms.addEventListener("change", setDueDate);


curDate.addEventListener("input", setDueDate);

curDate.addEventListener("change", setDueDate);



// function for adding new rows by listening new event
// function for adding new rows by listening new event
function addNewTableRow(){

  const divisionTableRow = document.getElementById("divisionTableRow");

  var tableRow = document.createElement('tr');

  tableRow.setAttribute("class", "info-row");

  tableRow.role = "row";

  tableRow.class = "odd info-row";


  // td1
  var itemDesc = document.querySelector('.itemDescription');

  var td1 = itemDesc.cloneNode(true);

  td1.children[0].value = "";

  // td2 for gtin/ean/upc input
  var gtinInput = document.querySelector('.gtinInput');

  var td2 = gtinInput.cloneNode(true);
  td2.children[0].value = "";


  // td3 for item quantity input
  var qty = document.querySelector('.qtyInput');

  var td3 = qty.cloneNode(true);
  td3.children[0].value = "";




  // td4 price input -
  var priceInput = document.querySelector(".priceInput");

  var td4 = priceInput.cloneNode(true);
  td4.children[0].value = ""


  // td5
  var taxDropdown = document.querySelector(".taxSelection");
  var td5 = taxDropdown.cloneNode(true);
  td5.children[0].value = 0;


  // td6
  var td6 = document.createElement('td');


  // table row insert all children input tds
  tableRow.appendChild(td1);

  tableRow.appendChild(td2);

  tableRow.appendChild(td3);

  tableRow.appendChild(td4);

  tableRow.appendChild(td5);

  tableRow.appendChild(td6);

  // finnally insert the element before the division table row
  divisionTableRow.parentNode.insertBefore(tableRow, divisionTableRow);


  // fetch again all info-input fields
  let infoInputBtns = document.querySelectorAll(".info-input");

  // implement auto-saving here
  infoInputBtns.forEach(function(element){

    element.addEventListener("input", createInvoice)
    element.addEventListener("input", autoSavingMsg)


  })


  console.log(infoInputBtns);


};


const addNewLineBtn = document.getElementById("addNewLine");

// when clicked, add a new row
addNewLineBtn.addEventListener("click", addNewTableRow);



// calculate the invoice amount - used for dynamically calculating the invoice metrics.
function calculateInvoice(){

  const rows = document.querySelectorAll(".info-row");

  const data = [];

  rows.forEach(function(row){

    const object1 = {};

    const itemName = row.children[0].children[0].value.trim();

    const gtin = row.children[1].children[0].value.trim()

    const quantity = parseInt(row.children[2].children[0].value);

    const unitPrice = parseFloat(row.children[3].children[0].value);

    var decimalTaxRate = parseFloat(row.children[4].children[0].value);

    const taxRate = (parseFloat(row.children[4].children[0].value) * 100).toFixed(0).toString() + "%";

    object1.name = itemName;

    object1.gtin = gtin;

    object1.quantity = quantity;

    object1.price = unitPrice;

    object1.taxRate = taxRate;

    object1.taxAmount = parseFloat((decimalTaxRate * unitPrice * quantity).toFixed(2))

    object1.subtotal = parseFloat(((1 + decimalTaxRate) * unitPrice * quantity).toFixed(2));

    object1.netTotal = parseFloat((unitPrice * quantity).toFixed(2));

    // set the sub-amount in a row as the subtotal
    row.children[5].textContent = object1.subtotal;

    // append the data object into data object array
    data.push(object1);


  });


  var netTotals = [];

  var taxTotals = [];

  var totals = [];

  // create an array of subtotals
  data.forEach(function(obj){


    netTotals.push(obj.netTotal)

    taxTotals.push(obj.taxAmount)

    totals.push(obj.subtotal)



  });



  // reduce function to get the accumualted subtotals
  function reducer(accumulator, currentValue){

    return accumulator + currentValue;

  };

  var netTotalAmount = netTotals.reduce(reducer).toFixed(2);

  var totalTaxAmount = taxTotals.reduce(reducer).toFixed(2);

  var beforeShippingTotal = totals.reduce(reducer).toFixed(2);

  const finalSubTotal = document.getElementById("subtotal");

  const finalTaxTotal = document.getElementById("taxAmount");

  finalSubTotal.value = netTotalAmount;

  finalTaxTotal.value = totalTaxAmount;

  // get the shipping charges entered by the user
  const shippingCharges = parseFloat(document.getElementById("shippingCharges").value).toFixed(2);

  const discount = parseFloat(document.getElementById("discount").value).toFixed(2);

  const finalTotal = document.querySelector("#total");


  if (isNaN(shippingCharges)){

    // calculate the final sum
    finalTotal.value = parseFloat(0 + parseFloat(beforeShippingTotal) - discount).toFixed(2);

  } else {

    // calculate the final sum
    finalTotal.value = parseFloat(parseFloat(shippingCharges) + parseFloat(beforeShippingTotal) - discount).toFixed(2);


  }


  const customer = document.getElementById("customer").value.trim();

  const dated = document.getElementById("invoiceDate").value;

  const dueDate = document.getElementById("dueDate").value;

  const invoiceNum = document.getElementById("invoiceNum").value;

  const invoiceSender = document.getElementById("invoiceSender").textContent;

  const customerNotes = document.getElementById("customerNotes").value;

  const terms = document.getElementById("terms").value;

  // set up an invoice object
  var invoice = {};

  invoice.customer = customer;
  invoice.dated = dated;
  invoice.dueDate = dueDate;
  invoice.data = data;
  invoice.shippingCharges = shippingCharges;
  invoice.discount = discount;
  invoice.subtotal = netTotalAmount;
  invoice.finalTotal = finalTotal.value;
  invoice.invoiceId = invoiceNum;
  invoice.invoiceSender = invoiceSender;
  invoice.status = "Draft";
  invoice.customerNotes = customerNotes;
  invoice.terms = terms;

  return invoice;


};



// Finally create the invoice and send it to the server via ajax
function createInvoice(){


  const invoice = calculateInvoice();

  console.log(invoice);

  const jsonData = JSON.stringify(invoice);

  // Init a http request Post
  var request = new XMLHttpRequest();
  request.open('POST', '/user/create/invoice', true);

  request.onload = function() {

        if (this.status >= 200 && this.status < 400) {

            // Success!
            var resp = JSON.parse(this.response);
            console.log(resp);

            // if error, log the error messages
            if (resp.error){

                alert(resp.error);
                // refresh without cache
                location.reload(true);

            } else {

              // redirct handling + javascript template literals > alacarte index page
              // window.location = referrer.toString();
            }

      }
      };

  // Send the quote data to the server via Post method
  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(jsonData);

  return request;
};




// select all price update buttons
const updatePriceBtns = document.querySelectorAll(".update-price-btn");

updatePriceBtns.forEach(function(button){

  button.addEventListener("click", createInvoice);

})



// implement auto-saving here
infoInputBtns.forEach(function(element){

  element.addEventListener("input", createInvoice)

  element.addEventListener("input", autoSavingMsg)


})


// select save and send button

const sendInvoiceBtn = document.getElementById("send");

sendInvoiceBtn.addEventListener("click", createInvoice);
sendInvoiceBtn.addEventListener("click", autoSavingMsg);

// set the form invoice_id equals to invoiceNum
sendInvoiceBtn.addEventListener("click", function(){

  const invoiceNum = document.getElementById("invoiceNum").value;

  const formInvoiceId = document.getElementById("invoice_id");

  formInvoiceId.value = invoiceNum;

});




// helper funtion for sleeping..
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// function for displaying auto saving messages
async function autoSavingMsg(){

  const autoSavingMsg = document.getElementById("auto-saving-msg");

  autoSavingMsg.setAttribute("style", "display:block");

  await sleep(4000);

  autoSavingMsg.setAttribute("style", "display:none");


}
