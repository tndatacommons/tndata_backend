/*
 * XXX: We're faking the user interaction but hiding & displaying stuff.
 *
 */


var generateCode = function(length) {
    length = length ? length : 4;
    var items = 'ABCDEFGHIJKLMNOPQRSTUVXYZ01234567890';
    var result = '';
    for(var i=0; i < length; i++) {
        result += items[Math.floor(Math.random()*items.length)];
    }
    console.log("Generated Code: " + result);
    return result;
};


// Toast messages to be shown AFTER tapping a button. The key/ID is the html
// ID attribute for the element that gets displayed.
var TOAST_MESSAGES = {
    '#notimplemented': "Sorry, we haven've built this yet.",
    '#add-code': 'Add a class code to populate your schedule.',  // add-code -> student-schedule
    '#teacher-info': 'Add your contact info to get started', // select-role -> teacher-info
    '#office-hours': 'Great! Now, list your office hours.', // teacher-info -> office-hours
    '#add-course': 'Perfect! Add your course info, next.', // office-hours -> add-course
    '#share-code': 'Done! Share this code with your students.', // add-course -> share-code
    '#student-schedule': 'Your class has been added to your schedule.'
};

$(document).ready(function() {
    $(".card-cta, #main-fab").click(function () {
        // The basic idea, is that when a card's button is clicked, we:
        // 1. Hide all the other cards...
        // 2. Look up that data-next attribute on the button (which should be the ID of a card)
        // 3. Show that card.
        var next = "#" + $(this).data('next');
        if(next !== "#notimplemented") {
            //$(this).parents('.mdl-card').hide();
            $('.mdl-card').hide();
            $(next).removeClass('hidden').hide().fadeIn();
        }

        // Clear input fields if we go back to them.
        if(next === '#add-code' || next === '#office-hours' || next === '#add-course') {
            $('.code-input, input[type=text]').val('');
            $('input[type=checkbox]').prop('checked', false);
            $('label.is-checked').removeClass('is-checked');
            $('.is-dirty').removeClass('is-dirty');
        }

        // generate code for the share code card.
        if(next === "#share-code") {
            $('span.share-code-display').text(generateCode());
        }

        // if we're viewnig the student schedule, also show the fab
        if(next === "#student-schedule") {
            $('#main-fab').removeClass('hidden').hide().fadeIn();
        } else {
            $('#main-fab').addClass('hidden');
        }

        // show a toast message if applicable.
        if(TOAST_MESSAGES[next]) {
            var toast = document.querySelector('.mdl-js-snackbar');
            toast.MaterialSnackbar.showSnackbar({message: TOAST_MESSAGES[next]});
        }
    });

    // Auto-advance the Code inputs.
    $(".code-input").keyup(function() {
        var next = {
            'code-1': 'code-2',
            'code-2': 'code-3',
            'code-3': 'code-4',
        };
        var transition = next[$(this).prop('id')];
        if(transition) {
            transition = "#" + transition;
            $(transition).focus();
        } else {
            $('.code-input').blur();
        }
    });

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

    // handle nav links
    $(".mdl-navigation__link").click(function() {
        switch($(this).attr('href')) {
            case '/':
                window.location.pathname = "/";
                break;
            case '#schedule':
                $(".mdl-card").hide();
                $("#teacher-schedule").removeClass('hidden').hide().fadeIn();
                break;
            case '#student-schedule':
                $(".mdl-card").hide();
                $("#student-schedule").removeClass('hidden').hide().fadeIn();
                break;
            default:
                break;
        }
    });
});
