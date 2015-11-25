(function() {
    'use strict';

    angular.module('app.core', [
        // Angular modules
        'ngSanitize',
        'angular-oauth2',

        // Our reusable framework
        'fw.exception',
        'fw.logger',
        'app.config',

        // 3rd Party modules
        'toastr',
        'ui.router'
    ]);
})();
