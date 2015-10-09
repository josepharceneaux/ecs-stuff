(function () {
    'use strict';

    var core = angular.module('app.core');

    core.config(configFunction);

    configFunction.$inject = ['$locationProvider', '$stateProvider', '$urlRouterProvider'];

    /* @ngInject */
    function configFunction($locationProvider, $stateProvider, $urlRouterProvider) {

        $locationProvider.html5Mode(true);

        $urlRouterProvider.otherwise('/dashboard');

        $stateProvider
            .state('site', {
                abstract: true
            })
            .state('dashboard', {
                parent: 'site',
                abstract: true,
                url: '/dashboard'
            })
            .state('dashboard.overview', {
                url: '',
                views: {
                    '@': {
                        template: '<gt-dashboard-overview></gt-dashboard-overview>'
                    }
                }
            })
            .state('dashboard.customize', {
                url: '/customize',
                views: {
                    '@': {
                        template: '<gt-dashboard-customize></gt-dashboard-customize>'
                    }
                }
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
