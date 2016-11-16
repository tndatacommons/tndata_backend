/*
 * XXX: We're faking the user interaction but hiding & displaying stuff.
 */

$(document).ready(function() {
    console.log("OK, we're ready ... ");

    $(".mdl-button").click(function () {

        // The basic idea, is that when a card's button is clicked, we:
        // 1. hide the current mdl-card
        // 2. Look up that data-next attribute on the button (which should be the ID of a card)
        // 3. Show that card.
        var next = "#" + $(this).data('next');
        $(this).parents('.mdl-card').hide();
        $(next).removeClass('hidden').hide().fadeIn();
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
                console.log("TODO: show the schedule");
                break;
            default:
                console.log("no matches");
                break;
        }
    });
});
