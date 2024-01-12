
const reqId = parseInt(document.getElementById("reqId").textContent.trim());

const quoteId = parseInt(document.getElementById("quoteId").textContent.trim());

const vendor = document.getElementById("vendor").textContent.trim()

const rows = document.querySelectorAll(".info-row");

const updateBtns = document.querySelectorAll(".update-quote-btn");

const saveBtn = document.getElementById("save");

const sendBtn = document.getElementById("send");


// view quote button in modal alert
const viewQuoteBtn = document.getElementById("viewQuote");


// get the referrer
var referrer = document.referrer;

const alertContent = document.getElementById("alertContent");

const alertTitle = document.getElementById("vendorSaveAlertLabel");


console.log(alertTitle, alertContent);



updateBtns.forEach(function(button){

  // click to ajax call to send the quote data to the server
  button.addEventListener("click", function(){

     // get the action save or send
    const action = button.id;

    var actionType = action.toString();

    // if the action type is "send", reset the title and text content for the modal alert
    if (actionType === "send") {

      alertContent.textContent = `Bravo! You've sent this quote to the buyer`;

      // alert title label
      alertTitle.textContent ="Quote sent to the buyer!";

      // set the button new  button text
      viewQuoteBtn.textContent = "View this quote";

      // reset the view quote url routing to this complete quote view using JS Template Literal
      viewQuoteBtn.href = `/vendor/view/ready/quote/${quoteId}`;

    }

    const validUntil = document.getElementById("Expiry").value;

    const leadTime = document.getElementById("leadTime").value;

    const data = {};

    data.action = action;

    data.reqId = reqId;

    data.quoteId = quoteId;

    data.validUntil = validUntil;

    data.leadTime = parseInt(leadTime);

    data.vendor = vendor;

    const details = [];

    rows.forEach(function(row) {

      const itemId = row.children[0].textContent.trim();
      const itemName = row.children[1].textContent.trim();
      const brand = row.children[2].textContent.trim();
      const gtin = row.children[3].textContent.trim();
      const qty = row.children[4].textContent.trim();
      const unit = row.children[5].textContent.trim();
      const price = row.children[6].children[0].value.trim();
      const deliverableQty = row.children[7].children[0].value.trim();

      console.log(itemId, itemName, brand, gtin, qty, unit, price, deliverableQty, action);

      details.push({

        "itemId": itemId,
        "itemName": itemName,
        "brand": brand,
        "gtin": gtin,
        "qty": parseInt(qty),
        "unit": unit,
        "price": parseFloat(price),
        "deliverableQty": parseInt(deliverableQty)

      });

      data.details = details;



    });

    // stringify the data
    const jsonData = JSON.stringify(data);

    console.log(jsonData);

    // Init a http request Post
    var request = new XMLHttpRequest();
    request.open('POST', '/vendor/quote/update', true);

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


  });


});
