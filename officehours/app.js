/*
 * XXX: We're faking the user interaction but hiding & displaying stuff.
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
    console.log("OK, we're ready ... ");

    $(".mdl-button, #main-fab").click(function () {

        // The basic idea, is that when a card's button is clicked, we:
        // 1. hide the current mdl-card
        // 2. Look up that data-next attribute on the button (which should be the ID of a card)
        // 3. Show that card.
        var next = "#" + $(this).data('next');
        if(next !== "#notimplemented") {
            //$(this).parents('.mdl-card').hide();
            $('.mdl-card').hide();
            $(next).removeClass('hidden').hide().fadeIn();
        }

        // Clear code if we go back to the add-code section
        if(next === '#add-code') {
            $('.code-input').val('');
        }

        // generate code for the share code card.
        if(next === "#share-code") {
            $('span.share-code-display').text(generateCode());
        }

        // show a toast message if applicable.
        if(TOAST_MESSAGES[next]) {
            var toast = document.querySelector('.mdl-js-snackbar');
            toast.MaterialSnackbar.showSnackbar({message: TOAST_MESSAGES[next]});
        }
    });

    // handle nav links
    $(".mdl-navigation__link").click(function() {
        console.log("clicked nav link: " + $(this).attr('href'));
        switch($(this).attr('href')) {
            case '/':
                console.log("Re-setting...");
                window.location.pathname = "/";
                break;
            case '#schedule':
                $(".mdl-card").hide();
                $("#teacher-schedule").removeClass('hidden').hide().fadeIn();
                break;
            default:
                console.log("no matches");
                break;
        }
    });
});
