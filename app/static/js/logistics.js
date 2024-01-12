
var logiOptions = document.querySelectorAll(".logi-options")


// add event listner click  to set the current transport mode
logiOptions.forEach(function(button){

  button.addEventListener("click", function(){

    var selectedMode = button.dataset.logiMode.toString();

    const transportMode = document.getElementById("transport-mode");

    // reset the current logistics mode;
    transportMode.textContent = selectedMode;

  })
})



var customsCheckbox = document.getElementById("customs")

// hide or unhide the additional customs fields
customsCheckbox.addEventListener("click", function(){


  const customsFields = document.getElementById("customs-fields")

  customsFields.setAttribute("style", "display:inline")

})



// function for adding new cargo
function addAirCargo(){

  const divisionTableRowAir = document.getElementById("divisionTableRowAir");

  var tableRow = document.createElement('tr');

  tableRow.setAttribute("class", "odd info-row-air");

  tableRow.role = "row";

  tableRow.class = "odd info-row-air";


  // td1 cargo qty
  var qtyInputAir = document.querySelector('.quantity-air');

  var td1 = qtyInputAir.cloneNode(true);

  td1.children[0].value = "";


  // td2 for cargo length
  var lengthAir = document.querySelector('.length-air');

  var td2 = lengthAir.cloneNode(true);
  td2.children[0].value = "";


  // td3 for cargo width
  var widthAir = document.querySelector('.width-air');

  var td3 = widthAir.cloneNode(true);
  td3.children[0].value = "";


  // td4 cargo height
  var heightAir = document.querySelector(".height-air");

  var td4 = heightAir.cloneNode(true);

  td4.children[0].value = ""


  // td5 for cargo volume in cbm
  var volumeAir = document.querySelector(".volume-air");
  var td5 = volumeAir.cloneNode(true);
  td5.children[0].value = "";


  // td6 for cargo weight
  var weightAir = document.querySelector(".weight-air");
  var td6 = weightAir.cloneNode(true);
  td6.children[0].value = "";


  // td7 for cargo desc
  var cargoDescAir = document.querySelector(".cargo-desc-air");
  var td7 = cargoDescAir.cloneNode(true);
  td7.children[0].value = "";


  // table row insert all children input tds
  tableRow.appendChild(td1);

  tableRow.appendChild(td2);

  tableRow.appendChild(td3);

  tableRow.appendChild(td4);

  tableRow.appendChild(td5);

  tableRow.appendChild(td6);

  tableRow.appendChild(td7);

  // finnally insert the element before the division table row

  divisionTableRowAir.parentNode.insertBefore(tableRow, divisionTableRowAir);

  // fetch again all info-input air fields
  var infoInputAirBtns = document.querySelectorAll(".info-input-air");


  // implement auto-saving here
  infoInputAirBtns.forEach(function(element){

    element.addEventListener("input", cacheAirCargoData);
    // element.addEventListener("input", autoSavingMsg)

})

}



// add more cargo
var addNewCargo = document.getElementById("addNewAirCargo")

// click to trigger the function
addNewCargo.addEventListener("click", addAirCargo)


// function for calculating cargo volume
function calculateAirCargoVoumeWeight(){

  const rows = document.querySelectorAll(".info-row-air");

  const data = [];

  rows.forEach(function(row){


    const object1 = {};

    const cargoQty = parseInt(row.children[0].children[0].value.trim());

    const lengthAir = parseFloat(row.children[1].children[0].value.trim());

    const widthAir = parseFloat(row.children[2].children[0].value.trim());

    const heightAir = parseFloat(row.children[3].children[0].value.trim());


    // calc the total volume for this batch of cargo
    const cargoVolume = parseFloat(((lengthAir * widthAir * heightAir) / 1000000) * cargoQty);


    // calculate the volume for current batch of cargo and set the volume to it
    row.children[4].children[0].value = parseFloat(cargoVolume).toFixed(2);


    // cargo piece weight multiply the qty of cargo
    const cargoWeight = parseFloat(row.children[5].children[0].value.trim()) * cargoQty;


    // get the cargo description
    const cargoDesc = row.children[6].children[0].value.trim();

    object1.qty = cargoQty;

    object1.length = lengthAir;

    object1.width = widthAir;

    object1.height = heightAir;

    object1.weight = cargoWeight.toFixed(2);

    object1.totalVolume = parseFloat(cargoVolume).toFixed(2);

    object1.cargoDesc = cargoDesc;

    // append the data object into data object array
    data.push(object1);


  });


  // hoding different weights
  var weights = [];

  // holding different volumes
  var volumes = [];


  // create an array of weights and volumes
  data.forEach(function(obj){


    weights.push(parseFloat(obj.weight));

    volumes.push(parseFloat(obj.totalVolume));

  });


  // reduce function to get the accumualted subtotals
  function reducer(accumulator, currentValue){

    return accumulator + currentValue;

  };


  var totalWeight = weights.reduce(reducer);

  var totalVolume = volumes.reduce(reducer);

  const reqSender = document.getElementById("currentUser").textContent;

  const origin = document.getElementById("origin-air").value.trim();

  const dest = document.getElementById("destination-air").value.trim();

  // set up an invoice object
  var freightReq = {};

  freightReq.reqSender = reqSender;

  freightReq.cargo = data;

  freightReq.totalWeight = totalWeight;

  freightReq.totalVolume = totalVolume;

  freightReq.mode = document.getElementById("transport-mode").textContent;

  freightReq.origin = origin;

  freightReq.dest = dest;

  console.log("This is not from cache");

  console.log(freightReq);x

  return freightReq;


};



// store the cargo information in local storage. Ajax call clears this cache
function cacheAirCargoData(){

  var currentAirCargo = calculateAirCargoVoumeWeight();

  localStorage.setItem("currentAirCargo", JSON.stringify(currentAirCargo));

  const airCargoData = localStorage.getItem("currentAirCargo");

  console.log("this is from cache");

  console.log(airCargoData);

  // set the data to hidden air data
  const hiddenAirCargoData = document.getElementById("hidden-air-cargo-data");

  hiddenAirCargoData.value = airCargoData;

}


// all air cargo input fields
var infoInputAirBtns = document.querySelectorAll(".info-input-air");


// implement auto-saving here via local storage
infoInputAirBtns.forEach(function(element){

  element.addEventListener("input", cacheAirCargoData)

})



// assign function event to search button
var search = document.getElementById("search");
