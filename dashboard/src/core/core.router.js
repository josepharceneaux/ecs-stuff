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
            .state('login', {
                url: '/login',
                template: '<gt-login></gt-login>'
            })
            .state('site', {
                abstract: true,
                views: {
                    topnav: {
                        template: '<gt-topnav></gt-topnav>'
                    },
                    sidenav: {
                        template: '<div id="app-sidenav-wrapper"><gt-sidenav></gt-sidenav></div>'
                    },
                    footer: {
                        template: '<gt-footer></gt-footer>'
                    }
                }
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
                parent: 'site',
                url: '/pipeline',
                redirectTo: 'pipeline.overview'
            })
            .state('pipeline.overview', {
                url: '',
                views: {
                    '@': {
                        template: '<gt-pipeline-overview></gt-pipeline-overview>'
                    }
                }
            })
            .state('pipeline.smartLists', {
                url: '/smartLists',
                views: {
                    '@': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipeline.candidateSearch', {
                url: '/candidateSearch',
                views: {
                    '@': {
                        template: '<gt-candidate-search></gt-candidate-search>'
                    }
                }
            })
            .state('pipeline.importCandidates', {
                url: '/importCandidates',
                views: {
                    '@': {
                        template: '<gt-import-candidates></gt-import-candidates>'
                    }
                }
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
            .state('campaigns.emailCampaigns', {
                url: '/emailCampaigns',
                views: {
                    '@': {
                        template: '<gt-email-campaigns></gt-email-campaigns>'
                    }
                }
            })
            .state('campaigns.eventCampaigns', {
                url: '/eventCampaigns',
                views: {
                    '@': {
                        template: '<gt-event-campaigns></gt-event-campaigns>'
                    }
                }
            })
            .state('campaigns.smsCampaigns', {
                url: '/smsCampaigns',
                views: {
                    '@': {
                        template: '<gt-sms-campaigns></gt-sms-campaigns>'
                    }
                }
            })
            .state('campaigns.socialMediaCampaigns', {
                url: '/socialMediaCampaigns',
                views: {
                    '@': {
                        template: '<gt-social-media-campaigns></gt-social-media-campaigns>'
                    }
                }
            })
            .state('campaigns.contentCampaigns', {
                url: '/contentCampaigns',
                views: {
                    '@': {
                        template: '<gt-content-campaigns></gt-content-campaigns>'
                    }
                }
            })
            .state('campaigns.pushNotifications', {
                url: '/pushNotifications',
                views: {
                    '@': {
                        template: '<gt-push-notifications></gt-push-notifications>'
                    }
                }
            })
            .state('admin', {
                parent: 'site',
                url: '/admin',
                views: {
                    '@': {
                        template: '<gt-admin></gt-admin>'
                    }
                }
            })
            .state('help', {
                parent: 'site',
                url: '/help',
                views: {
                    '@': {
                        template: '<gt-help></gt-help>'
                    }
                }
            });
    }
})();
