/*  https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_collapsible_symbol  */

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.maxHeight){
        content.style.maxHeight = null;
    } else {
        content.style.maxHeight = content.scrollHeight + "px";
    } 
    });
}

/* POP UP CHAT WINDOW */
/* https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_popup_chat */

function openForm() {
    document.getElementById("myForm").style.display = "block";
}
  
function closeForm() {
    document.getElementById("myForm").style.display = "none";
}