/**
 * Created by erikfarmer on 2/16/16.
 */

(function() {
    'use strict';

    angular
        .module('app')
        .config(config);

    function config($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: 'partials/form.html',
                controller: 'HomeController',
                controllerAs: 'vm'
            });
    }

})();