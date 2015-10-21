(function() {
    'use strict';

    angular.module('app.core', [
        // Angular modules (ngAnimate 1.4.x is not compatible with ui.bootstrap 0.13.0)
        /* 'ngAnimate', */
        'ngSanitize',
        'angular-oauth2',

        // Our reusable framework
        'fw.exception',
        'fw.logger',
        'app.config',

        // 3rd Party modules
        'toastr',
        'ui.bootstrap',
        'ui.router'
    ]);
})();
