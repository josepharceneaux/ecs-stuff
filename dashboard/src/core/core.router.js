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
            .state('forgot-password', {
                url: '/forgot-password',
                views: {
                    content: {
                        template: '<gt-forgot-password></gt-forgot-password'
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
            .state('pipelines.smart-lists', {
                url: '/smart-lists',
                views: {
                    '@site': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipelines.candidate-search', {
                url: '/candidate-search',
                views: {
                    '@site': {
                        template: '<gt-candidate-search></gt-candidate-search>'
                    }
                }
            })
            .state('pipelines.import-candidates', {
                url: '/import-candidates',
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
            .state('campaigns.email-campaigns', {
                url: '/email-campaigns',
                views: {
                    '@site': {
                        template: '<gt-email-campaigns></gt-email-campaigns>'
                    }
                }
            })
            .state('campaigns.event-campaigns', {
                url: '/event-campaigns',
                views: {
                    '@site': {
                        template: '<gt-event-campaigns></gt-event-campaigns>'
                    }
                }
            })
            .state('campaigns.sms-campaigns', {
                url: '/sms-campaigns',
                views: {
                    '@site': {
                        template: '<gt-sms-campaigns></gt-sms-campaigns>'
                    }
                }
            })
            .state('campaigns.social-media-campaigns', {
                url: '/social-media-campaigns',
                views: {
                    '@site': {
                        template: '<gt-social-media-campaigns></gt-social-media-campaigns>'
                    }
                }
            })
            .state('campaigns.content-campaigns', {
                url: '/content-campaigns',
                views: {
                    '@site': {
                        template: '<gt-content-campaigns></gt-content-campaigns>'
                    }
                }
            })
            .state('campaigns.push-notifications', {
                url: '/push-notifications',
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
