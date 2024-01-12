var request = new XMLHttpRequest();

request.open('GET', '/api/messages/unread', true);

request.onload = function() {

  if (this.status >= 200 && this.status < 400) {
    // Success!
    var data = JSON.parse(this.response);

    var unreadSystemMsgs = data.unread_system_msgs;

    var unreadUserMsgs = data.unread_user_msgs;

    console.log(data, unreadSystemMsgs, unreadUserMsgs);


    // system alerts counter
    if (unreadSystemMsgs > 0){

      console.log("Unread system messages");

      const alertsCenter = document.querySelector("#alerts-center");

      var badgeCounter = document.createElement("span");

      badgeCounter.innerHTML = unreadSystemMsgs;

      badgeCounter.setAttribute("class", "badge badge-danger badge-counter");

      alertsCenter.appendChild(badgeCounter);


      console.log(alertsCenter);

    }


    // user messages counter
    if (unreadUserMsgs > 0){

      console.log("Unread user messages");

      const messagesCenter = document.querySelector("#messages-center");

      var messagesCounter = document.createElement("span");

      messagesCounter.innerHTML = unreadSystemMsgs;

      messagesCounter.setAttribute("class", "badge badge-danger badge-counter");

      alertsCenter.appendChild(messagesCounter);


      console.log(alertsCenter);

    }



  } else {
    // We reached our target server, but it returned an error

  }
};

request.onerror = function() {
  // There was a connection error of some sort
};

request.send();
