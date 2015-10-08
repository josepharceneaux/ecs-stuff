(function () {
    'use strict';

    var core = angular.module('app.core');

    core.config(configFunction);

    configFunction.$inject = ['$locationProvider', '$stateProvider', '$urlRouterProvider'];

    /* @ngInject */
    function configFunction($locationProvider, $stateProvider, $urlRouterProvider) {

        $locationProvider.html5Mode(true);

        $urlRouterProvider.otherwise('/');

        $stateProvider
            .state('dashboard', {
                url: '/dashboard',
                template: '<gt-dashboard></gt-dashboard>'
            })
            .state('pipeline', {
                url: '/pipeline',
                template: '<gt-pipeline></gt-pipeline>'
            })
            .state('campaigns', {
                url: '/campaigns',
                template: '<gt-campaigns></gt-campaigns>'
            })
            .state('admin', {
                url: '/admin',
                template: '<gt-admin></gt-admin>'
            })
            .state('help', {
                url: '/help',
                template: '<gt-help></gt-help>'
            });
    }
})();
