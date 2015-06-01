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

});
