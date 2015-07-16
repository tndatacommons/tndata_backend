/*
 * Auto-populate the `Notification text` field with the Action's title,
 * but only if the notification text field is empty.
 *
 */
$(document).ready(function() {
    var title_field = $("#id_title");
    var notification_field = $("#id_notification_text");
    var original_title = title_field.val();

    // If we've loaded the page, and there's a title but not notification.
    if(notification_field.val() === "" && original_title !== "") {
        notification_field.val(original_title);
        console.log("Setting notification to: " + original_title);
    }

    // See if we should change the notification.
    title_field.change(function() {
        if(notification_field.val() === "") {
            // if we're setting the title field for the first time,
            // copy it's value into the notification field.
            notification_field.val(title_field.val());
            console.log("Setting notification to: " + title_field.val());
        } else if(notification_field.val() === original_title) {
            // if we're changing the title AND it originally matched the
            // notification field.
            notification_field.val(title_field.val());
            console.log("Setting notification to: " + title_field.val());
        }
    });


    // Function to toggle the selected Behavior's details.
    var toggle_behavior_details = function(selector) {
        $("#behavior-info").show();
        $(".behaviors").hide(); // hide all other behaviors.
        $(selector).show(); // show the selected one.
        $("#behavior-info h2").text($("#id_behavior option:selected").text());
    };

    // We we select a Behavior, display some of it's info.
    $("#id_behavior").change(function() {
        var selected_id = "#behavior-" + $(this).val();
        toggle_behavior_details(selected_id);
    });

    // Show any pre-selected behaviors.
    var selected_id = $("#id_behavior").val();
    if(selected_id) {
        selected_id = "#behavior-" + selected_id;
        toggle_behavior_details(selected_id);
    }

});
