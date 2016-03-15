var SUB_AOIS;
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


$('#submit').on('click', function() {
    $.ajax({
        type: 'POST',
        url: '/',
        data: $('widget-form').serialize(),
        success: function(response) {
            if ('success' in response) {
                $('#widget-form').hide();
                $('#form-success').show();
            }
            else {
                $('#form-error').show();
            }
        },
        error: function(response) {
            $('#form-error').show();
        }
    })
});