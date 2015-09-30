var _gaq = _gaq || [];
var universitiesList = [];

_gaq.push(['_setAccount', 'UA-33209718-1']);
_gaq.push(['_trackPageview']);

var placeholderNotSupported = false;

(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();

$(document).ready(function() {
    // $('input[type=text][placeholder], input[type=email][placeholder]').simplePlaceholder();

    if (! Modernizr.input.placeholder) {
        placeholderNotSupported = true;
        $('[placeholder]').focus(function() {
            var input = $(this);
            if (input.val() == input.attr('placeholder')) {
                input.val('');
                input.removeClass('placeholder');
            }
        }).blur(function() {
                    var input = $(this);
                    if (input.val() == '' || input.val() == input.attr('placeholder')) {
                        input.addClass('placeholder');
                        input.val(input.attr('placeholder'));
                    }
                }).blur();
    }

    // Load up university list
    //    $.ajax(
    //        type: "post",
    //        dataType: "json",
    //        url: "",
    //        success: function(response)
    //            universitiesList = response['universities_list'];
    //            $("#university").typeahead(
    //                items: 10,
    //                source: universitiesList
    //            });
    //        }
    //    });

    $(".tm-input-aoi").tagsManager({
        hiddenTagListId: 'hidden-tags-aoi',
        hiddenTagListName: 'interestTags',
        delimiters: [124]
    });
    $('#interestId').change(function(){
        if ( ! $("#interestId").find(":selected").val())
            return false;
        $("#hidden-tags-aoi").tagsManager('pushTag', $("#interestId").find(":selected").text());
        $(this).find(":first-child").text("Select another interest...");
        $(this).val("");
        $(this).focus();
    });

    // "Other" dropdowns functionality
    $("select").change(function(e) {
        if ($(this).find("option:selected").text() === "Other") {
            $(this).removeClass("span6").addClass("span4");
            $(this).siblings('input').hide().slideDown();
        }
        else if ($(this).siblings('input.other').is(':visible')) {
            var $select = $(this);
            $(this).siblings('input').show().slideUp(400, function() {
                $select.removeClass("span4").addClass("span6");
            });
        }
    });
    // Input verification
    $("input[required], select[required]").blur(function(e) {
        checkRequired(this);
    });

    // Tooltips
    $("input[required], select[required]").each(function(i) {
        $(this).tooltip({
            placement: 'bottom',
            title: $(this).data('validation-message') || 'Required',
            trigger: 'manual'
        });
    });

    /* NUID */
    $(".checkbox-nuid").click(function(e) {
        $("#nuid").toggle();
    });

    $("form").submit(function(e) {
        var validInputs = true;
        $("input[required], select[required]").each(function(index) {
            var isValid = checkRequired(this);
            validInputs = validInputs && isValid;
        });

        // If inputs are all valid, and placeholder attribute is not supported, then blank out all inputs set to their placeholder
        if (placeholderNotSupported && validInputs ) {
            $("[placeholder]").each(function(e) {
                var input = $(this);
                if (input.val() == input.attr('placeholder')) {
                    input.val('');
                }
            });
        }

        if (! validInputs) e.preventDefault();
        return validInputs;
    });
});
function checkRequired(input) {
    var $input = $(input);
    var isValid;

    // Validate email
    if ($input.attr('type') === 'email' && $input.val()) {
        isValid = isEmailValid($input.val());
        if (isValid) {
            markInputValid($input);
        } else {
            markInputInvalid($input);
        }
    }
    // Validate NUID
    else if ($input.attr('name') === 'nuid') {
        isValid = (! $input.val()) || /^[a-zA-Z]\d{6}$/g.test($input.val());
        if (isValid) {
            markInputValid($input);
        } else {
            markInputInvalid($input);
        }
    }
    else if (! $input.val() || $input.hasClass('invalid') || (placeholderNotSupported && $input.val() === $input.attr('placeholder'))) {
        markInputInvalid($input);
        isValid = false;
    } else {
        markInputValid($input);
        isValid = true;
    }

    return isValid;
}

function createDegreeOptions(){
    var degrees = ['Associates', 'Bachelors', 'Masters', 'Doctorate', 'Professional', 'Other'];
    var degreeSelector = document.getElementById('degree');
    var option;
    for (var i=0; i < degrees.length; i++){
        option = document.createElement("option");
        option.label = degrees[i];
        option.value = degrees[i];
        option.text = degrees[i];
        degreeSelector.add(option);
    }
    return true;
}

function createGraduationYearOptions(){
    var minYear = 2011;
    var currentYear= minYear;
    var maxYear = 2020;
    var optGroup;
    var option;
    var graduationSelector = document.getElementById('graduation');
    var semesters = ['Spring', 'Fall/Winter', 'Summer'];
    while (currentYear <= maxYear) {
        optGroup = document.createElement('OPTGROUP')
        optGroup.label = currentYear;
        for (var i=0; i< semesters.length; i++){
            option = document.createElement('option');
            option.label = semesters[i] + ' ' + currentYear;
            option.value = semesters[i] + ' ' + currentYear;
            option.text = semesters[i] + ' ' + currentYear;
            optGroup.appendChild(option)
        }
        graduationSelector.add(optGroup);
        currentYear += 1;
    }
}

createDegreeOptions();
createGraduationYearOptions();