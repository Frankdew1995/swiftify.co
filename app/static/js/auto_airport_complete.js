

// search button
const searchAirportOrigin = document.getElementById("origin-air");

const airportSearchResults = document.getElementById("airport-origin-match-list")


console.log(searchAirportOrigin);


searchAirportOrigin.addEventListener("input", fetchAirport);



function fetchAirport(e){


  // initialize the apc library

  var apcm = new apc('multi', {key : 'a489432269', limit: 7});

	// handle successful response
	apcm.onSuccess = function (data) {


      var airports = data.airports;

	    console.log(airports);


	};

	// handle response error
	apcm.onError = function (data) {
	    console.log(data.message);
	};

	// makes the request to get the airport data
	apcm.request(e.target.value);



}





// render match results in renderHTML
function renderHTML(matches){


  if (matches.length > 0 ){


    const html = matches.map( match =>

      `
      <div class="card match-result">

        <div class="card-body">
          <p class="card-text">
            <span>${match.name}</span>.
            <span>${match.gtin}</span>.
            <span>${match.brand}</span>.
          </p>
          </div>

      </div>
      `


  ).join('');


  matchList.innerHTML = html;


  }

};
