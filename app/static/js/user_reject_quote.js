

//
const quoteId = parseInt(document.getElementById("quoteId").textContent.trim());

const rejectBtn = document.getElementById("confirmReject");

const rejectedQuotesURL = "/user/quotes/view/rejected";


rejectBtn.addEventListener("click", function(){

  const data = {"quoteId": quoteId, "isRejected": true};

  // stringify the data
  const jsonData = JSON.stringify(data);


  // Init a http request Post
  var request = new XMLHttpRequest();
  request.open('POST', '/user/reject/quote', true);

  request.onload = function() {
        if (this.status >= 200 && this.status < 400) {

            // Success!
            var resp = JSON.parse(this.response);

            console.log(resp);

            // if the a new quote successdully created in database and action is send
            if (resp.success){

            console.log("Rejected!!");


            // redirct user to rejected quotes page
            window.location = rejectedQuotesURL;

            }


            // if error, log the error messages
            if (resp.error){

                alert(resp.error);
                // refresh without cache
                location.reload(true);

            } else {

              // redirct user to rejected quotes page
              window.location = rejectedQuotesURL;


            }

      }
      };

      // Send the quote data to the server via Post method
      request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      request.send(jsonData);




});
