/*
 * See the utils.widgets.TextareaWithMarkdownHelperWidget.
 *
 * This bit of code is only useful if that widget is specified with a
 * `warning_limit` paramter, in which case it'll warn about text reaching
 * that limit.
 */

$(document).ready(function() {
    $('span.md-text-length').each(function() {
        // Wrapper span for the character count. There's an inner
        // <span class="count"></span> element for the character count value.
        var span = $(this);
        var fieldId = "#" + span.data('for');  // ID of the textarea
        var textarea = $(fieldId); // the textarea element.
        var limit = span.data('limit');  // the predifined character limit

        // Set the initial count.
        var count = textarea.val() ? textarea.val().length : 0;

        // Update it as we type in the textarea.
        textarea.keyup(function(e) {
            count = $(this).val() ? $(this).val().length : 0;
            span.find('.count').text(count);

            // If we're over the defined limit, add a warning class.
            if(count >= limit) {
                span.addClass('warning');
            } else {
                span.removeClass('warning');
            }
        });
    });
});
