(function() {
    'use strict';

    angular.module('app.core', [
        // Angular modules
        'ngCookies',
        'ngSanitize',
        'angular-oauth2',

        // Our reusable framework
        'fw.exception',
        'fw.logger',
        'app.config',

        // 3rd Party modules
        'ngTagsInput',
        'pickadate',
        'toastr',
        'ui.router'
    ]);
})();
