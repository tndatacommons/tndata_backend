$(document).ready(function() {

    /* Note: This is an undocumented api that lets you change only the
     * order of an Action. Then endpoint is at:
     *
     *  /api/actions/<id>/order/
     *
     * and accepts data like: {sequence_order: 5}
     */
    $("select.action-update").change(function(e) {
        var select_element = $(this);
        var url = "/api/actions/" + select_element.data('actionid') + "/order/";
        var payload = {
            'sequence_order': select_element.val(),
            'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val(),
        };

        $.post(url, payload, function(data) {
            select_element.addClass("success");
            setTimeout(function() {select_element.removeClass("success");}, 1500);
        }).fail(function(data) {
            select_element.addClass("error");
            setTimeout(function() {select_element.removeClass("error");}, 1500);
        });
    });


    /* Note: This is an undocumented api that lets you change only the
     * order of a Goal. Then endpoint is at:
     *
     *  /api/goals/<id>/order/
     *
     * and accepts data like: {sequence_order: 5}
     */
    $("select.goal-update").change(function(e) {
        var select_element = $(this);
        var url = "/api/goals/" + select_element.data('goalid') + "/order/";
        var payload = {
            'sequence_order': select_element.val(),
            'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val(),
        };

        $.post(url, payload, function(data) {
            select_element.addClass("success");
            setTimeout(function() {select_element.removeClass("success");}, 1500);
        }).fail(function(data) {
            select_element.addClass("error");
            setTimeout(function() {select_element.removeClass("error");}, 1500);
        });
    });
});
