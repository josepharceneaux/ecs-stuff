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
                views: {
                    content: {
                        template: '<gt-login></gt-login>'
                    }
                }
            })
            .state('site', {
                abstract: true,
                views: {
                    topnav: {
                        template: '<gt-topnav></gt-topnav>'
                    },
                    content: {
                        template: '<div id="app-sidenav-wrapper"><gt-sidenav></gt-sidenav></div><div id="app-view-wrapper"><div ui-view></div></div>'
                    },
                    footer: {
                        template: '<gt-footer></gt-footer>'
                    }
                },
                data: {
                    loginRequired: true
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
                    '@site': {
                        template: '<gt-dashboard-overview></gt-dashboard-overview>'
                    }
                }
            })
            .state('dashboard.customize', {
                url: '/customize',
                views: {
                    '@site': {
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
                    '@site': {
                        template: '<gt-pipeline-overview></gt-pipeline-overview>'
                    }
                }
            })
            .state('pipeline.smartLists', {
                url: '/smartLists',
                views: {
                    '@site': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipeline.candidateSearch', {
                url: '/candidateSearch',
                views: {
                    '@site': {
                        template: '<gt-candidate-search></gt-candidate-search>'
                    }
                }
            })
            .state('pipeline.importCandidates', {
                url: '/importCandidates',
                views: {
                    '@site': {
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
                    '@site': {
                        template: '<gt-campaigns-overview></gt-campaigns-overview>'
                    }
                }
            })
            .state('campaigns.emailCampaigns', {
                url: '/emailCampaigns',
                views: {
                    '@site': {
                        template: '<gt-email-campaigns></gt-email-campaigns>'
                    }
                }
            })
            .state('campaigns.eventCampaigns', {
                url: '/eventCampaigns',
                views: {
                    '@site': {
                        template: '<gt-event-campaigns></gt-event-campaigns>'
                    }
                }
            })
            .state('campaigns.smsCampaigns', {
                url: '/smsCampaigns',
                views: {
                    '@site': {
                        template: '<gt-sms-campaigns></gt-sms-campaigns>'
                    }
                }
            })
            .state('campaigns.socialMediaCampaigns', {
                url: '/socialMediaCampaigns',
                views: {
                    '@site': {
                        template: '<gt-social-media-campaigns></gt-social-media-campaigns>'
                    }
                }
            })
            .state('campaigns.contentCampaigns', {
                url: '/contentCampaigns',
                views: {
                    '@site': {
                        template: '<gt-content-campaigns></gt-content-campaigns>'
                    }
                }
            })
            .state('campaigns.pushNotifications', {
                url: '/pushNotifications',
                views: {
                    '@site': {
                        template: '<gt-push-notifications></gt-push-notifications>'
                    }
                }
            })
            .state('admin', {
                parent: 'site',
                url: '/admin',
                views: {
                    '@site': {
                        template: '<gt-admin></gt-admin>'
                    }
                }
            })
            .state('help', {
                parent: 'site',
                url: '/help',
                views: {
                    '@site': {
                        template: '<gt-help></gt-help>'
                    }
                }
            });
    }
})();
