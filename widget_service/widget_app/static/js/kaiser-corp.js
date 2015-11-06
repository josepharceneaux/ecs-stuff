var stateToCities = {
    'Northern CA': ['Alameda', 'Antioch', 'Berkeley', 'Bolinas', 'Campbell', 'Clovis', 'Concord', 'Cupertino', 'Daly City', 'Davis', 'Elk Grove', 'Emeryville', 'Fairfield', 'Folsom', 'Fremont', 'Fresno', 'Gilroy', 'Greenbrae', 'Hayward', 'Lafayette', 'Lincoln', 'Livermore', 'Lodi', 'Manteca', 'Martinez', 'Mill Valley', 'Milpitas', 'Modesto', 'Moraga', 'Mountain View', 'Napa', 'Novato', 'Oakhurst', 'Oakland', 'Petaluma', 'Pinole', 'Pittsburg', 'Pleasant Hill', 'Pleasanton', 'Point Reyes Station', 'Rancho Cordova', 'Redwood City', 'Richmond', 'Rohnert Park', 'Roseville', 'Sacramento', 'San Bruno', 'San Francisco', 'San Jose', 'San Leandro', 'San Mateo', 'San Rafael', 'San Ramon', 'Santa Clara', 'Santa Rosa', 'Sebastolpol', 'Selma', 'South San Francisco', 'Stinson Beach', 'Stockton', 'Sunnyvale', 'Tracy', 'Turlock', 'Union City', 'Vacaville', 'Vallejo', 'Walnut Creek'],
    'Southern CA': ['Aliso Viejo', 'Anaheim', 'Anaheim Hills', 'Bakersfield', 'Baldwin Park', 'Bell Gardens', 'Bellflower', 'Brea', 'Burbank', 'Camarillo', 'Carlsbad', 'Carson', 'Chatsworth', 'Chino', 'Chino Hills', 'Chula Vista', 'City of Industry', 'Claremont', 'Colton', 'Corona', 'Costa Mesa', 'Cudahy', 'Culver City', 'Cypress', 'Diamond Bar', 'Downey', 'Duarte', 'El Cajon', 'El Monte', 'Encinitas', 'Escondido', 'Fontana', 'Fountain Valley', 'Fullerton', 'Garden Grove', 'Gardena', 'Glendale', 'Glendora', 'Granada Hills', 'Harbor City', 'Hawaiin Gardens', 'Hemet', 'Huntington Beach', 'Indio', 'Inglewood', 'Irvine', 'Irwindale', 'La Mesa', 'La Palma', 'La Puente', 'La Quinta', 'La Verne', 'Laguna Hills', 'Lake Forest', 'Lancaster', 'Lomita', 'Long Beach', 'Los Angeles', 'Lynwood', 'Mission Hills,', 'Mission Viejo', 'Montclair', 'Montebello', 'Moreno Valley', 'North Hills', 'North Hollywood', 'Northridge', 'Norwalk', 'Oceanside', 'Ontario', 'Orange', 'Oxnard', 'Pacoima', 'Palm Desert', 'Palm Springs', 'Palmdale', 'Panorama City', 'Paramount', 'Pasadena', 'Placentia', 'Pomona', 'Poway', 'Rancho Cucamonga', 'Redlands', 'Reseda', 'Riverside', 'San Bernardino', 'San Diego', 'San Dimas', 'San Fernando', 'San Juan Capistrano', 'San Marcos', 'San Pedro', 'Santa Ana', 'Santa Clarita', 'Santa Fe Springs', 'Santee', 'Semi Valley', 'Sylmar', 'Tarzana', 'Temecula', 'Thousand Oaks', 'Torrance', 'Tustin', 'Upland', 'Van Nuys', 'Ventura', 'Vernon', 'Victorville', 'Vista', 'West Covina', 'Whittier', 'Wildomar', 'Woodland Hills', 'Yorba Linda'],
    'Colorado': ['Aurora', 'Boulder', 'Brighton', 'Castle Rock', 'Centennial', 'Colorado Springs', 'Denver', 'Englewood', 'Evergreen', 'Fort Collins', 'Greeley', 'Greenwood Village', 'Highlands Ranch', 'Johnstown', 'Lafayette', 'Lakewood', 'Littleton', 'Lone Tree', 'Longmont', 'Loveland', 'Parker', 'Pueblo West', 'Sheridan', 'Westminster', 'Wheat Ridge'],
    'Washington, D.C.': ['Washington, D.C.'],
    'Georgia': ['Alpharetta', 'Athens', 'Atlanta', 'Austell', 'Chamblee', 'Cumming', 'Decatur', 'Douglasville', 'Duluth', 'Fairburn', 'Fayetteville', 'Forest Park', 'Holly Springs', 'Jonesboro', 'Kennesaw', 'Lawrenceville', 'Lithonia', 'Marietta', 'McDonough', 'Newnan', 'Norcross', 'Peachtree City', 'Sandy Springs', 'Snellville', 'Sugar Hill', 'Tucker'],
    'Hawaii': ['Aiea', 'Hilo', 'Honolulu', 'Kahuku', 'Kailua', 'Kamuela', 'Kaneohe', 'Kapolei', 'Kealakeua', 'Kihei', 'Lahaina', 'Lihue', 'Mililani', 'Waianae', 'Wailuku', 'Waipahu'],
    'Maryland': ['Annapolis', 'Baltimore', 'Beltsville', 'Bethesda', 'Burtonsville', 'Catonsville', 'Colesville', 'Columbia', 'Frederick', 'Fulton', 'Gaithersburg', 'Germantown', 'Glen Burnie', 'Halethorpe', 'Hyattsville', 'Kensington', 'Largo', 'Linthicum Heights', 'Lutherville', 'Odenton', 'Pasadena', 'Riverdale', 'Rockville', 'Silver Spring', 'Suitland', 'Temple Hills', 'Timonium', 'Towson', 'Upper Marlboro', 'Wheaton', 'White Marsh'],
    // 'Ohio': ['Akron', 'Avon', 'Bedford', 'Brecksville', 'Brooklyn Heights', 'Cleveland', 'Cleveland Heights', 'Fairlawn', 'Kent', 'Lakewood', 'Mayfield Heights', 'Mentor', 'North Canton', 'Painesville', 'Parma', 'Rocky River', 'Strongsville', 'Twinsburg', 'Willoughby'],
    'Oregon': ['Aloha', 'Beaverton', 'Clackamas', 'Gresham', 'Hillsboro', 'Keizer', 'Lake Oswego', 'Milwaukie', 'Mt. Angel', 'Oregon City', 'Portland', 'Salem', 'Tigard', 'Tualatin'],
    'Virginia': ['Alexandria', 'Arlington', 'Ashburn', 'Burke', 'Chantilly', 'Dulles', 'Fair Oaks', 'Fairfax', 'Falls Church', 'Fredericksburg', 'Lansdowne', 'Manassas', 'McLean', 'Reston', 'Springfield', 'Sterling', 'Woodbridge'],
    'Washington': ['Longview', 'Orchards', 'Seattle', 'Vancouver']
};

var _gaq = _gaq || [];

_gaq.push(['_setAccount', 'UA-33209718-1']);
_gaq.push(['_trackPageview']);

var placeholderNotSupported = false;

(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();

$(document).ready(function() {

    // Modernizr detection for placeholder (ie8)
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

    // Interest tags
    $(".tm-input-aoi").tagsManager({
        hiddenTagListId: 'hidden-tags-aoi',
        hiddenTagListName: 'interestTags',
        delimiters: [124]
    });
    $("#interestSelect").change(function (e) {
        // Populate & show sub AOI dropdown
        $("#subInterestSelect").empty();
        var aoiId = $(this).find(':selected').val();
        console.log('Primary AOI: ' + aoiId);
        var subAOIList = aoiIdToSubAois(aoiId);
        console.log(subAOIList);

        $("#subInterestSelect").append("<option value=''>Select Subcategory</option>");
        $("#subInterestSelect").append("<option value='All'>All Subcategories</option>");
        for (var i = 0; i < subAOIList.length; i++) {
            $("#subInterestSelect").append("<option value='" + subAOIList[i]['id'] + "'>" + subAOIList[i]['description'] + "</option>");
        }
        if (subAOIList.length < 1){
            $("#subInterestSelect").val('All');
            $("#subInterestSelect").trigger('change');
        }

        $("#subInterestSelect").show();
        return true;
    });

    $("#subInterestSelect").change(function (e) {
        // Add a tag if not the default one
        var subAoiName = $("#subInterestSelect").find(':selected').text();
        if (subAoiName !== $("#subInterestSelect").find("option").first().text()) {
            $("#hidden-tags-aoi").tagsManager('pushTag', $("#interestSelect").find(":selected").text() + ": " + subAoiName);
        }
    });

    // Location tags
    $(".tm-input-location").tagsManager({
        hiddenTagListId: 'hidden-tags-location',
        hiddenTagListName: 'locationOfInterestTags',
        delimiters: [124]
    });

    $("#stateOfInterest").change(function (e) {
        // Populate & show cities dropdown
        $("#cityOfInterest").empty();
        var stateName = $(this).find(':selected').html();
        var citiesList = stateToCities[stateName];
        $("#cityOfInterest").append("<option value=''>Select City</option>");
        $("#cityOfInterest").append("<option value='All'>All Cities</option>");
        for (var i = 0; i < citiesList.length; i++) {
            $("#cityOfInterest").append("<option value='" + citiesList[i] + "'>" + citiesList[i] + "</option>");
        }
        $("#cityOfInterest").show();
        return true;
    });
    $("#cityOfInterest").change(function (e) {
        // Add a tag if not the default one
        var city = $("#cityOfInterest").find(':selected').text();
        if (city !== $("#cityOfInterest").find("option").first().text()) {
            if ($("#stateOfInterest").val() == '') return;

            $("#hidden-tags-location").tagsManager('pushTag', $("#stateOfInterest").find(":selected").html() + ": " + $("#cityOfInterest").find(':selected').html());
        }
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

    $("input[required], select[required]").change(function(e) {
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

    /* Job Alerts */
    $("#job-alerts").click(function(e) {
        $("input[name='jobFrequency']").parent().toggle();

        // If job alerts is unchecked, then uncheck all job alerts
        if (! $("input[name='jobFrequency']").parent().is(":visible")) {
            $("input[name=jobFrequency]").removeAttr("checked");
        }
    });

    /* NUID */
    $(".checkbox-nuid").click(function(e) {
        $("#nuid").toggle();
    });

    /* Recent Graduate */
    $(".education-group").hide();
    $(".checkbox-recent-graduate").click(function(e) {
        $(".education-group").toggle();
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
    else if (! $input.val() || $input.hasClass('invalid') || (placeholderNotSupported && $input.val() === $input.attr('placeholder'))) {
        markInputInvalid($input);
        isValid = false;
    } else {
        markInputValid($input);
        isValid = true;
    }

    return isValid;
}

// Returns array of {'id', 'description'}
function aoiIdToSubAois(aoiId) {
    // Make list of all sub AOIs
    var subAOIs = [];
    for (var i=0; i < SUB_AOIS.length; i++) {
        if (SUB_AOIS[i].parent_id == aoiId) {
            subAOIs.push(SUB_AOIS[i])
        }
    }
    return subAOIs;
}


var protoCounter = {


    setUp: function(max, min){
        this._max = max
        this._min = min || 1
        this._current = this._min
    },

    next: function(){
        if (++this._current > this._max)
            throw new Error("Current counter is already at the max value")
        return this
    },

    previous: function(){
        if (--this._current < this._min)
            throw new Error("Current counter is already at the min value")
        return this
    },

    rewind: function(){
        this._current = this._min
        return this
    },

    value: function(){
        return this._current
    }

};

function getInterestsJSON() {
    var interests;
    var request = $.ajax({
        url: "/v1/domains/" + window.location.pathname.split('/')[3] + "/interests",
        type: "GET",
        dataType: "json"
    });
    request.success(function(interests) {
        SUB_AOIS = interests.secondary_interests;
        renderInterests(interests);
    });
}

getInterestsJSON();