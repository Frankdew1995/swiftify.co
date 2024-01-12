console.log("Ok");


const sendSelfBtn = document.getElementById("emailSelf");


const sendNonSelf = document.getElementById("emailNonSelf");

// add an event listener to this
sendSelfBtn.addEventListener("click", function(){

  const emailInput = document.getElementById("email");

  // set the recipient email as user thyself email
  emailInput.value = document.getElementById("senderEmail").textContent.trim();

  console.log(emailInput.value);


});


// add an event listener to this
sendNonSelf.addEventListener("click", function(){

  const emailInput = document.getElementById("email");

  // set the recipient email as user thyself email
  emailInput.value = "";

  console.log(emailInput.value);


});
