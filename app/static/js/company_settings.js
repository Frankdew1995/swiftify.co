

var saveBtn = document.getElementById("submit");


var addTaxBtn = document.getElementById("addTaxBtn");


addTaxBtn.addEventListener("click", function(event){

  const secondTaxCol = document.getElementById("tax-group-2");

  secondTaxCol.setAttribute('style', "display:inline");


});


saveBtn.addEventListener("click", function(){

  const taxRate1 = parseInt(document.getElementById("taxRate1").value);

  const taxRate2 = parseInt(document.getElementById("taxRate2").value);

  // set the tax data to local storage
  localStorage.setItem("tax1", taxRate1);

  localStorage.setItem("tax2", taxRate2)


});
