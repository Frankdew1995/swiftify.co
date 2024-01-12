if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
 console.log("Mobile device alert!!");

 const exportBtn = document.getElementById("export");

 console.log(exportBtn);

 exportBtn.setAttribute("style", "display:none;");


}
