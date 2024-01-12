
// search button
const search = document.getElementById("search");


// list for rendering matched results
const matchList = document.getElementById("match-list");


// function for searhcing the products and filter it
const searchProducts = async searchText =>{

  const res = await fetch("/products/jsonified");

  const products = await res.json();

  // filter the products based on search text;
  let matches = products.filter(product => {

    const regex = new RegExp(`^${searchText}`, "gi");

    return product.name.match(regex) || product.gtin.match(regex)
    || product.name.includes(searchText) || product.gtin.includes(searchText);

  });


  // if the search text is empty
  if (searchText.length === 0){


    matches = [];
    matchList.innerHTML = '';


  }



console.log(matches);

renderHTML(matches);

// select all matched results
const matchResults = document.querySelectorAll(".match-result");

for (let i = 0; i < matchResults.length; i++) {

     matchResults[i].addEventListener("click", function() {

       console.log("Ok, worked");
       var result = matchResults[i];

       var name = result.children[0].children[0].children[0].textContent;

       console.log(name);

       search.value = name;


       matchList.innerHTML = '';



     }

   );
 }


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



// add the search function to the input event to search input
search.addEventListener("input", ()=> searchProducts(search.value));
