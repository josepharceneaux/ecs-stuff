(function () {
    'use strict';

    var core = angular.module('app.core');

    core.config(configFunction);

    configFunction.$inject = ['$locationProvider', '$stateProvider', '$urlRouterProvider'];

    /* @ngInject */
    function configFunction($locationProvider, $stateProvider, $urlRouterProvider) {

        $locationProvider.html5Mode(true);

        $urlRouterProvider.otherwise('/dashboard');
        //$urlRouterProvider.when('/dashboard', '/dashboard/overview');

        $stateProvider
            .state('site', {
                abstract: true
            })
            .state('dashboard', {
                parent: 'site',
                url: '/dashboard',
                redirectTo: 'dashboard.overview'
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
                parent: 'site',
                url: '/campaigns',
                redirectTo: 'campaigns.overview'
            })
            .state('campaigns.overview', {
                url: '',
                views: {
                    '@': {
                        template: '<gt-campaigns-overview></gt-campaigns-overview>'
                    }
                }
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
