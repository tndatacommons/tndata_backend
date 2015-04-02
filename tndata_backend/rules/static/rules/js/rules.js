var submit, allData;

$(document).ready(function() {

    function initializeConditions(key, data) {
        var selector = '.' + key + '-conditions';
        $(selector).conditionsBuilder(data);
    }

    function initializeActions(key, data) {
        var selector = '.' + key + '-actions';
        $(selector).actionsBuilder(data);
    }

    /*
     * Add class names to generated elements so they work with
     * and/or look nice in Foundation.
     */
    function updateFoundationUI() {
        $('a.add-rule, a.add-condition, a.remove, a.add')
            .addClass("button secondary tiny");
        $('a.remove').addClass("alert");
    }

    function initializeForm() {
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

            var post_data = {
                app_name: key,
                rule_name: name,
                conditions: conditions_code,
                actions: actions_code,
            };
            var csrftoken = $('input[name=csrfmiddlewaretoken]').val();

            // DO the AJAX request to create the Rule.
            $.ajax({
              type: "POST",
              url: '/rules/',
              data: post_data,
              beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
              }
            })
            .done(function(response) {
              window.location = '/rules/';
            });
        });
    }

    function buildSection(key) {
        var section = $('<form></form>').addClass("rules-section");
        section.append(
          $('<div></div>').addClass("row").append(
            $('<div></div>').addClass("large-12 small-12 columns").append(
                $('<h2></h2>').addClass("subheader").text(key),
                $('<label></label>')
                    .prop('for', key + '-name')
                    .text('Name: ')
                    .append(
                        $('<input>')
                            .prop('type', 'text')
                            .prop('name', 'name')
                            .prop('id', key + '-name')
                            .prop('placeholder', 'Give this Rule a Name')
                    )
                )
          ),
          $('<div></div>').addClass("row").append(
            $('<div></div>')
                .addClass(key + '-conditions')
                .addClass("large-12 small-12 columns")
                .text(key + '-conditions')
          ),
          $('<div></div>').addClass("row").append(
            $('<div></div>')
                .addClass(key + '-actions')
                .addClass("large-12 small-12 columns")
                .text(key + '-actions'),
            $('<hr/>'),
            $('<button></button>')
                .prop('id', key + '-submit')
                .prop('type', 'submit')
                .text("Save Rule")
                .data('key', key)
                .data('conditions', "." + key + '-conditions')  // selectors.
                .data('actions', "." + key + '-actions')
          )
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
        updateFoundationUI();
    }

    // Fire off Ajax Request to get Variable/Action data.
    $.get("/rules/data/", function(data) {
        allData = data;
        init();
    });
});
