$(document).ready(function() {
    $("#question_content").hide();
    $("#question_keywords").hide();
    $("#question_submit").hide();
});

function questionContinue(){
    var title = document.getElementById("id_title").value;
    if (title.length != 0){
        document.getElementById("id_title").disabled = true;
        $("#question_content").show();
        $("#question_keywords").show();
        $("#question_submit").show();
        $("#question_continue").hide();
    }
}

