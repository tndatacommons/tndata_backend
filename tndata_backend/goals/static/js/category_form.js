/*
 * JS for the category form. This:
 *
 * - auto-hides the consent_summary/consent_more fields
 * - adds a click listener to the packaged_content field that, when
 *   checked displays the above.
 *
 */

var _show_consent = function() {
    $("#id_consent_summary").parent().parent().parent().show();
    $("#id_consent_more").parent().parent().parent().show();
};

var _hide_consent = function() {
    $("#id_consent_summary").parent().parent().parent().hide();
    $("#id_consent_more").parent().parent().parent().hide();
};

$(document).ready(function() {

    var packaged = $("#id_packaged_content");
    if(packaged.is(":checked")) {
        _show_consent();
    } else {
        _hide_consent();
    }

    // Auto-show/hide the consent fields when packed is checked/unchecked.
    packaged.change(function() {
        if($(this).is(":checked")) {
            _show_consent();
        } else {
            _hide_consent();
        }
    });
});
