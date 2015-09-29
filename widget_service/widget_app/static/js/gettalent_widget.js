function expandWidget() {
    $('.gettalent_container.expanding .expand').animate({
        height: 'show'
    }, 600, function () {
        // Animation complete.
    });
}

function validateEmail(email) {
    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
}

function validateInput(input) {
    var $input = $(input),
        isValid = true,
        message = "";

    if (!$input.val()) {
        isValid = false;
        message = "Enter this field!";
    }
    else if ($input.attr('type') == 'email') {
        isValid = validateEmail($input.val());
        message = "Enter valid email!";
    }

    if (isValid) {
        $input.tooltip('hide');
    }
    else {
        $input.tooltip('hide')
            .attr('data-original-title', message)
            .tooltip('fixTitle')
            .tooltip('show');
    }

    return isValid;
}

$(document).ready(function () {
    $('.gettalent_container').toggle();

    $(".gettalent_container:not(.expanding)").addClass(($(".gettalent_container").parent().width() >= 450 ? "wide" : "narrow"));

    $('.gotoFile').click(function () {
        $('#gettalent_attachment').toggle();
        $('#gettalent_upload').toggle();
    });

    $('.gettalent_container.expanding .expand').hide();
    $('.gettalent_container.expanding input[name="emailAdd"]').focus(expandWidget);

    // Show interest info input when "Other" is selected
    $("select#interestId").change(function (e) {
        var $this = $(this),
            $interestInfo = $('input#interestInfo');

        if ($this.find("option:selected").text() === "Other") {
            $this.removeClass("span6").addClass("span4");
            $interestInfo.slideDown();
        }
        else {
            $interestInfo.slideUp(400, function () {
                $this.removeClass("span4").addClass("span6");
            });
        }
    });

    // Validate inputs
    $("input.required, select.required, input#interestInfo").keyup(function (e) {
        validateInput(this);
    });

    $("form").submit(function (e) {
        var formValid = true;

        // Validate require inputs
        $("input.required, select.required").each(function (index, input) {
            if (!validateInput(input)) {
                formValid = false;
            }
        });

        // Validate interest info if visible
        if ($('#interestInfo').is(':visible')) {
            if (!validateInput($('#interestInfo'))) {
                formValid = false;
            }
        }

        // If inputs are all valid, and placeholder attribute is not supported, then blank out all inputs set to their placeholder
        if (placeholderNotSupported && formValid) {
            $("[placeholder]").each(function (e) {
                var input = $(this);
                if (input.val() == input.attr('placeholder')) {
                    input.val('');
                }
            });
        }

        if (!formValid) {
            e.preventDefault();
        }
    });

}); 