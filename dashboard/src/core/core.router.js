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
            .state('forgotPassword', {
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
            .state('pipelines.manage', {
                url: '/manage',
                views: {
                    '@site': {
                        template: '<gt-pipelines-manage></gt-pipelines-manage>'
                    }
                }
            })
            .state('pipelines.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-pipeline-create></gt-pipeline-create>'
                    }
                }
            })
            .state('pipelines.detail', {
                url: '/:pipelineId',
                views: {
                    '@site': {
                        template: '<gt-pipeline-detail></gt-pipeline-detail>'
                    }
                }
            })
            .state('pipelines.detail.settings', {
                url: '/settings',
                views: {
                    '@site': {
                        template: '<gt-pipeline-settings></gt-pipeline-settings>'
                    }
                }
            })
            .state('pipelines.detail.team', {
                url: '/team',
                views: {
                    '@site': {
                        template: '<gt-pipeline-team></gt-pipeline-team>'
                    }
                }
            })
            .state('pipelines.detail.smartLists', {
                url: '/smart-lists',
                views: {
                    '@site': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipelines.detail.smartLists.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-smart-list-create></gt-smart-list-create>'
                    }
                }
            })
            .state('pipelines.detail.smartLists.detail', {
                url: '/:smartListId',
                views: {
                    '@site': {
                        template: '<gt-smart-list-details></gt-smart-list-details>'
                    }
                }
            })
            .state('candidates', {
                parent: 'site',
                url: '/candidates',
                redirectTo: 'candidates.overview'
            })
            .state('candidates.overview', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-candidates-overview></gt-candidates-overview>'
                    }
                }
            })
            .state('candidates.add', {
                url: '/add',
                views: {
                    '@site': {
                        template: '<gt-candidate-add></gt-candidate-add>'
                    }
                }
            })
            .state('candidates.manage', {
                url: '/manage',
                views: {
                    '@site': {
                        template: '<gt-candidates-manage></gt-candidate-manage>'
                    }
                }
            })
            .state('candidates.profile', {
                url: '/profile/:profileId',
                views: {
                    '@site': {
                        template: '<gt-candidate-profile></gt-candidate-profile>'
                    }
                }
            })
            .state('talentPools', {
                parent: 'site',
                url: '/talent-pools',
                redirectTo: 'talentPools.manage'
            })
            .state('talentPools.manage', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-talent-pools-manage></gt-talent-pools-manage>'
                    }
                }
            })
            .state('talentPools.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-talent-pools-create></gt-talent-pools-create>'
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
            .state('campaigns.manage', {
                url: '/manage',
                views: {
                    '@site': {
                        template: '<gt-campaigns-manage></gt-campaigns-manage>'
                    }
                }
            })
            .state('campaigns.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-campaign-create></gt-campaign-create>'
                    }
                }
            })
            .state('campaigns.detail', {
                url: '/:campaignId',
                views: {
                    '@site': {
                        template: '<gt-campaign-detail></gt-campaign-detail>'
                    }
                }
            })
            .state('campaigns.detail.settings', {
                url: '/settings',
                views: {
                    '@site': {
                        template: '<gt-campaign-settings></gt-campaign-settings>'
                    }
                }
            })
            .state('campaigns.detail.emails', {
                abstract: true,
                url: '/emails'
            })
            .state('campaigns.detail.emails.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-campaign-email-create></gt-campaign-email-create>'
                    }
                }
            })
            .state('campaigns.detail.emails.detail', {
                url: '/:emailId',
                views: {
                    '@site': {
                        template: '<gt-campaign-email-detail></gt-campaign-email-detail>'
                    }
                }
            })
            .state('campaigns.detail.events', {
                abstract: true,
                url: '/events'
            })
            .state('campaigns.detail.events.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-campaign-event-create></gt-campaign-event-create>'
                    }
                }
            })
            .state('campaigns.detail.events.detail', {
                url: '/:eventId',
                views: {
                    '@site': {
                        template: '<gt-campaign-event-detail></gt-campaign-event-detail>'
                    }
                }
            })
            .state('search', {
                parent: 'site',
                url: '/search',
                views: {
                    '@site': {
                        template: '<gt-search></gt-search>'
                    }
                }
            })
            .state('admin', {
                parent: 'site',
                url: '/admin',
                redirectTo: 'admin.dashboard'
            })
            .state('admin.dashboard', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-admin-dashboard></gt-dashboard>'
                    }
                }
            })
            .state('admin.settings', {
                url: '/settings',
                views: {
                    '@site': {
                        template: '<gt-admin-settings></gt-admin-settings>'
                    }
                }
            })
            .state('admin.systemAlerts', {
                url: '/system-alerts',
                views: {
                    '@site': {
                        template: '<gt-admin-system-alerts></gt-admin-system-alerts>'
                    }
                }
            })
            .state('admin.styleguide', {
                url: '/styleguide',
                redirectTo: 'styleguide.dashboard',
                data: {
                    loginRequired: false,
                    demoModeRequired: true
                }
            })
            .state('admin.styleguide.dashboard', {
                url: '/dashboard',
                views: {
                    '@site': {
                        template: '<gt-styleguide-dashboard></gt-styleguide-dashboard>'
                    }
                }
            })
            .state('admin.styleguide.colors', {
                url: '/colors',
                views: {
                    '@site': {
                        template: '<gt-styleguide-colors></gt-styleguide-colors>'
                    }
                }
            });
    }
})();
