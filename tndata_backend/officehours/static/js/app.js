/*
 *
 */
$(document).ready(function() {
    // Handle Time helpers.
    $(".mdl-menu__item").click(function() {
        var val = $(this).data('val');
        var forId = $(this).data('forid');
        if(val && forId) {
            forId = "#" + forId;

            // Add .is-dirty to the parent container, so the label does the
            // right thing: https://github.com/google/material-design-lite/issues/903
            $(forId).parent().addClass("is-dirty");
            $(forId).val(val);
        }
    });

});
