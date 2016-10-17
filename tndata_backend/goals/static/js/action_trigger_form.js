/*
 * JS for the actions' Trigger form.
 *
 */

var hideAdvancedOptions = function() {
    // The chosen UI gets messed up if these fields are hiden before that
    // plugin runs. So just hide them after everything else loads.
    $(".trigger-form-advanced").hide();

};

$(document).ready(function() {

    window.setTimeout(hideAdvancedOptions, 1000);

    $("#advanced").click(function() {
        var displayStatus = $(this).data("status");
        if(displayStatus === "hidden") {
            $(this).html('<i class="fa fa-chevron-down"></i> Hide');
            $(this).data('status', 'shown');
        } else {
            $(this).html('<i class="fa fa-chevron-right"></i> Show');
            $(this).data('status', 'hidden');
        }
        $('.trigger-form-advanced').toggle();
    });

});
