var submit, allData;

$(document).ready(function() {

    function initializeConditions(key, data) {
        console.log("initializeConditions", data);
        var selector = '.' + key + '-conditions';
        $(selector).conditionsBuilder(data)
    }

    function initializeActions(key, data) {
        console.log("initializeActions");
        var selector = '.' + key + '-actions';
        $(selector).actionsBuilder(data);
    }

    // Just Captures the submit event and displays data instead.
    function initializeForm() {
        console.log("initializeForm");
        $("button[type=submit]").click(function(e) {
            e.preventDefault();
            var key = $(this).data('key');
            var name = $("#" + key + "-name").val();
            // Get selectors for the conditions and actions;
            var conditions = $(this).data("conditions");
            var actions = $(this).data("actions");
            var conditions_code = JSON.stringify(
                $(conditions).conditionsBuilder("data")
            );
            var actions_code = JSON.stringify(
                $(actions).actionsBuilder("data")
            );

            $("#conditions-code").text(conditions_code);
            $("#actions-code").text(actions_code);
            $("#results").show();
            console.log("CONDITIONS", conditions_code);
            console.log("ACTIONS", actions_code);
            console.log("NAME: ", name);
        });
    }

    function buildSection(key) {
        var section = $('<form></form>').addClass("rules-section");
        section.append(
            $('<h2></h2>').text(key),
            $('<label></label>').prop('for', key + '-name').text('Name'),
            $('<input>').prop('type', 'name').prop('id', key + '-name'),
            $('<div></div>')
                .addClass(key + '-conditions')
                .text(key + '-conditions'),
            $('<div></div>')
                .addClass(key + '-actions')
                .text(key + '-actions'),
            $('<button></button>')
                .prop('id', key + '-submit')
                .prop('type', 'submit')
                .text("Save Rule")
                .data('key', key)
                .data('conditions', "." + key + '-conditions')  // selectors.
                .data('actions', "." + key + '-actions')
        );
        $('#rules-container').append(section);
    }

    function init() {
        // NOTE: allData = { app_name: [conditions...], ... }
        var keys = Object.keys(allData);
        for(i=0; i < keys.length; i++) {
            buildSection(keys[i]);
        }
        for(i=0; i < keys.length; i++) {
            data = allData[keys[i]];
            for(j=0; j < data.length; j++) {
                initializeConditions(keys[i], data[j]);
                initializeActions(keys[i], data[j]);
            }
        }
        initializeForm();
    }

    // Fire off Ajax Request to get Variable/Action data.
    $.get("/rules/data/", function(data) {
        allData = data;
        console.log("received rules data", data);
        init();
    });

});
