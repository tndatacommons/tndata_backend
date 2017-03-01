$(document).ready(function(){
    var title = document.getElementById("title_p").innerHTML;
    console.log("title:" + title + ":");
    if (title === ""){
        $("#question_content").hide();
        $("#question_keywords").hide();
        $("#question_submit").hide();
        $("#title_p").hide();
    }
    else{
        $("#question_title").hide();
        $("#question_continue").hide();
    }
});

function questionContinue(){
    var title = document.getElementById("id_title").value;
    if (title.length != 0){
        $("#question_title").hide();
        document.getElementById("title_p").innerHTML = title;
        $("#title_p").show();
        $("#question_content").show();
        $("#question_keywords").show();
        $("#question_submit").show();
        $("#question_continue").hide();
    }
}

