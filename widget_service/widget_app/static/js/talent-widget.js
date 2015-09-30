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
