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
                        template: '<gt-main></gt-main>'
                    }/*,
                    footer: {
                        template: '<gt-footer></gt-footer>'
                    }*/
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
            .state('pipelines', {
                parent: 'site',
                url: '/pipelines',
                redirectTo: 'pipelines.overview'
            })
            .state('pipelines.overview', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-pipelines-overview></gt-pipelines-overview>'
                    }
                }
            })
            .state('pipelines.smartLists', {
                url: '/smartLists',
                views: {
                    '@site': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipelines.candidateSearch', {
                url: '/candidateSearch',
                views: {
                    '@site': {
                        template: '<gt-candidate-search></gt-candidate-search>'
                    }
                }
            })
            .state('pipelines.importCandidates', {
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
            });
    }
})();
