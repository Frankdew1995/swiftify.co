


var markReadBtns = document.querySelectorAll(".mark-read");



for (let i = 0; i < markReadBtns.length; i++) {
     markReadBtns[i].addEventListener("click", function() {

       console.log("Ok, worked");
       var button = markReadBtns[i];

       var messageId = button.dataset.messageId;

       // mark as the message as read in server
       markMessageRead(messageId=messageId);



     }

   );
 }



// function to mark message as read
 function markMessageRead(messageId){

   data = {"isRead": true, "messageId": messageId};

   const jsonData = JSON.stringify(data);

   var request = new XMLHttpRequest();

   request.open('POST', '/mark/message/read', true);

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

               // refresh without cache
               location.reload(true);

             }

       }
       };


   // Send the order data to the server via Post method
   request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
   request.send(jsonData);


 }
