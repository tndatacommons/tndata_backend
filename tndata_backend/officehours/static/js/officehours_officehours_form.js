/*
 * Hide the days textfield and use JS to populate it based on selected
 * checkbox options.
 */
var _checkboxEditing = {};

$(document).ready(function() {
    //$("#div_id_days").hide(); // Hide the days textfield

    /*************************************
    // Pre-select any necessary days.
    var selectedDays = $("#id_days").val();
    if(selectedDays.length) {
        selectedDays.split(",").forEach(function(item, index, array) {
            console.log(item, index, array);
            var checkId = "office-hours-day-" + item.toLowerCase();
            $("#" + checkId).prop("checked", "checked");
            $("label[for=" + checkId + "]").addClass("is-checked");
        });
    }

    // Handle any additional selections.
    // Unbind this, then re-bind to make sure we don't end up with duplicates.
    // SEE: http://stackoverflow.com/a/22311843/182778
    $("input.mdl-checkbox__input").off("change").on("change", function(evt) {
        evt.stopPropagation();
        evt.preventDefault();

        var inputId = $(this).prop('id');

        var days = $("#id_days").val();
        days = days.length ? days.split(",") : [];

        var elt = $(this);
        var isSelected = elt.is(":checked");
        var selectedDay = elt.data('day');
        var selectedDayIndex = days.indexOf(selectedDay);

        if(isSelected && selectedDayIndex === -1) {
            // Add the day if it's not already in the list.
            days.push(selectedDay);
        } else if(selectedDayIndex >= 0) {
            // Remove the day if it IS in the list
            days.splice(selectedDayIndex, 1);
        }

        var daysString = days.join(",");
        $("#id_days").val(daysString);
        console.log("Selected Days: ", days, daysString);
    });
    *************************************/

    // Handle Time input helpers.
    $("button.helper").click(function(e) {
        e.preventDefault();
        console.log("Helper button clicked: " + $(this).prop('id'));
    });

    $("li.mdl-menu__item").click(function(e) {
        e.preventDefault();
        console.log("li.mdl-menu__item clicked: " + $(this).data('val'));
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
