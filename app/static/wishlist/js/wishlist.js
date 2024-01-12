
$.noConflict();

const confirmBtn = document.getElementById('requestConfirm');

console.log(confirmBtn);

confirmBtn.addEventListener("click", function(){


    alert("Great. All set. Stay tuned!")

    const order = {};

    const productDetails = [];

    const qtyItems = document.querySelectorAll(".cd-cart__select");

    const ownerEmail = document.getElementById("RequesterEmail").value.trim();

    qtyItems.forEach(function(item){

      productDetails.push({'itemId': parseInt(item.children[0].id.trim()),
                            'itemQuantity': parseInt(item.children[0].value.trim()),
                            'itemUnit': item.children[1].value.trim()});

    });


    order.details = productDetails;

    order.requester = ownerEmail;

    console.log(order);

    const data = JSON.stringify(order);

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
    request.send(data);

});
