
var infoRows = document.querySelectorAll(".info-row");

var itemsQty = infoRows.length;

var actionBtns = document.getElementById("actionBtns");

var cartOwner = document.getElementById("cartOwner").textContent.trim();


const reqBtn = document.getElementById("send");



console.log(actionBtns);
if (itemsQty === 0 ) {


  // set the action buttons hidden.
  console.log("No items available");



};




// aggregate the data for the whole cart data
function aggregateCartData(){

  const rows = document.querySelectorAll(".info-row");

  const data = [];

  console.log(rows);


  rows.forEach(function(row){

      const object1 = {};

      const itemId = row.children[0].textContent.trim();

      const itemQty = row.children[4].children[0].value.trim();

      object1.itemId = parseInt(itemId);
      object1.itemQty = parseInt(itemQty);

      data.push(object1)

  })

  console.log(data);


  return data;



};




// function using AJAX Call sending data to backend to email vendors
function sendRequest(){


  const reqData = {"details": aggregateCartData(), "requester": cartOwner};

  const jsonData = JSON.stringify(reqData);

  var request = new XMLHttpRequest();
  request.open('POST', '/users/requests/listen', true);

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
              window.location = '/';
            }

      }
      };


  // Send the order data to the server via Post method
  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(jsonData);




};



reqBtn.addEventListener("click", sendRequest);
