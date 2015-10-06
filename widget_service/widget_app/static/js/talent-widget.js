var SUB_AOIS;
var status = 'form'
$('#form-success').hide();
$('#form-error').hide();

function isEmailValid(email) {
    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return email && re.test(email);
}

function markInputInvalid($input) {
    console.log("marking input invalid: " + $input.attr('id'));
    if (! $input.siblings('.tooltip').length) {
        $input.tooltip('show');
    }
    $input.closest(".control-group").removeClass('success').addClass('error');
}

function markInputValid($input) {
    console.log("marking input valid: " + $input.attr('id'));
    $input.tooltip('hide');

    $input.closest(".control-group").removeClass('error').addClass('success');
}

//function getInterestsJSON() {
//    var interests;
//    var request = $.ajax({
//        url: "/widgetV1/interests/1", // TODO hardcode change interests url
//        type: "GET",
//        dataType: "json"
//    });
//    request.done(function(interests) {
//        if (interests.primary_interests.length == 0) {
//            console.log('Assuming DEMO mode');
//            interests = getDemoInterests();
//        }
//        SUB_AOIS = interests.secondary_interests;
//        renderInterests(interests);
//    });
//}


function getDemoInterests(){
    return {
        primary_interests: [
            {id: 1, description: 'foo', parent_id: null},
            {id: 2, description: 'bar', parent_id: null},
            {id: 3, description: 'baz', parent_id: null},
        ],
        secondary_interests: [
            {id: 4, description: 'oof', parent_id: 1},
            {id: 5, description: 'rab', parent_id: 2},
            {id: 6, description: 'zab', parent_id: 3},
        ]
    }
}


function renderInterests(interests) {
    var option;
    var interestSelector = document.getElementById("interestSelect");
    for (var i=0; i < interests.primary_interests.length; i++) {
        option = document.createElement("option");
        option.label = interests.primary_interests[i].description;
        option.value = interests.primary_interests[i].id;
        option.text = interests.primary_interests[i].description;
        interestSelector.add(option);
    }
}
