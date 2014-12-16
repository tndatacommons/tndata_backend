var conditions, actions, submit, allData;

$(document).ready(function() {

    function initializeConditions(data) {
        console.log("initializeConditions");
        conditions.conditionsBuilder(data)
    }

    function initializeActions(data) {
        console.log("initializeActions");
        actions.actionsBuilder(data);
    }

    // Just Captures the submit event and displays data instead.
    function initializeForm() {
        console.log("initializeForm");

        $("#submit").click(function(e) {
            e.preventDefault();
            var conditions_code = JSON.stringify(conditions.conditionsBuilder("data"));
            var actions_code = JSON.stringify(actions.actionsBuilder("data"));

            $("#conditions-code").text(conditions_code);
            $("#actions-code").text(actions_code);
            $("#results").show();

            console.log("CONDITIONS", conditions_code);
            console.log("ACTIONS", actions_code);
        });
    }

    function init() {
        conditions = $("#conditions");
        actions = $("#actions");

        initializeConditions(allData);
        initializeActions(allData);
        initializeForm();
    }

    // Fire off Ajax Request to get Variable/Action data.
    $.get("/diary/rules/data/", function(data) {
        allData = data;
        console.log("received rules data", data);
        init();
    });

});
