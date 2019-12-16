function LoadMain() {
    var checkError = "{{errorvalue}}";
    if(checkError=="Error: Invalid UserID or Password"){
        document.getElementById("login-form").action ="";
    }else{
        document.getElementById("login-form").action ="login/";
    }

}

function clearmsg(){
    document.getElementById("errorvalue").innerHTML = ''; 
}