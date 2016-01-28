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

            // Login
            .state('login', {
                url: '/login',
                views: {
                    content: {
                        template: '<gt-login></gt-login>'
                    }
                }
            })

            // Forgot Password
            .state('forgotPassword', {
                url: '/forgot-password',
                views: {
                    content: {
                        template: '<gt-forgot-password></gt-forgot-password'
                    }
                }
            })

            // Reset Password
            .state('resetPassword', {
                url: '/reset-password/:key',
                views: {
                    content: {
                        template: '<gt-reset-password></gt-reset-password>'
                    }
                }
            })

            // Site (Login Required Pages)
            .state('site', {
                abstract: true,
                views: {
                    systemAlerts: {
                        template: '<gt-system-alerts></gt-system-alerts>'
                    },
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

            // Admin
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
            .state('admin.users', {
                url: '/users',
                views: {
                    '@site': {
                        template: '<gt-admin-users></gt-admin-users>'
                    }
                }
            })
            .state('admin.users.add', {
                url: '/add',
                views: {
                    '@site': {
                        template: '<gt-admin-user-add></gt-admin-user-add>'
                    }
                }
            })
            .state('admin.users.user', {
                url: '/:userId',
                redirectTo: 'admin.users.user.edit'
            })
            .state('admin.users.user.edit', {
                url: '/edit',
                views: {
                    '@site': {
                        template: '<gt-admin-user-edit></gt-admin-user-edit>'
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
            })

            // Dashboard
            .state('dashboard', {
                parent: 'site',
                url: '/dashboard',
                redirectTo: 'dashboard.overview',
                ncyBreadcrumb: {
                    label: 'Dashboard'
                }
            })
            .state('dashboard.overview', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-dashboard-overview></gt-dashboard-overview>'
                    }
                },
                ncyBreadcrumb: {
                    label: 'Home'
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

            // Campaigns
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
            .state('campaigns.campaign', {
                url: '/:campaignId',
                redirectTo: 'campaigns.campaign.detail'
            })
            .state('campaigns.campaign.detail', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-campaign-detail></gt-campaign-detail>'
                    }
                }
            })
            .state('campaigns.campaign.settings', {
                url: '/settings',
                views: {
                    '@site': {
                        template: '<gt-campaign-settings></gt-campaign-settings>'
                    }
                }
            })
            .state('campaigns.campaign.emails', {
                abstract: true,
                url: '/emails'
            })
            .state('campaigns.campaign.emails.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-campaign-email-create></gt-campaign-email-create>'
                    }
                }
            })
            .state('campaigns.campaign.emails.email', {
                url: '/:emailId',
                redirectTo: 'campaigns.campaign.emails.email.detail'
            })
            .state('campaigns.campaign.emails.email.detail', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-campaign-email-detail></gt-campaign-email-detail>'
                    }
                }
            })
            .state('campaigns.campaign.emails.email.edit', {
                url: '/edit',
                views: {
                    '@site': {
                        template: '<gt-campaign-email-edit></gt-campaign-email-edit>'
                    }
                }
            })
            .state('campaigns.campaign.events', {
                abstract: true,
                url: '/events'
            })
            .state('campaigns.campaign.events.create', {
                url: '/create',
                views: {
                    '@site': {
                        template: '<gt-campaign-event-create></gt-campaign-event-create>'
                    }
                }
            })
            .state('campaigns.campaign.events.event', {
                url: '/:eventId',
                redirectTo: 'campaigns.campaign.events.event.detail'
            })
            .state('campaigns.campaign.events.event.detail', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-campaign-event-detail></gt-campaign-event-detail>'
                    }
                }
            })
            .state('campaigns.campaign.events.event.edit', {
                url: '/edit',
                views: {
                    '@site': {
                        template: '<gt-campaign-event-edit></gt-campaign-event-edit>'
                    }
                }
            })

            // Candidate Search
            .state('candidateSearch', {
                parent: 'site',
                url: '/candidate-search',
                views: {
                    '@site': {
                        template: '<gt-candidate-search></gt-candidate-search>'
                    }
                }
            })

            // Candidates
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
                        template: '<gt-candidates-manage></gt-candidates-manage>'
                    }
                }
            })
            .state('candidates.profile', {
                url: '/:profileId',
                redirectTo: 'candidates.profile.detail',
            })
            .state('candidates.profile.detail', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-candidate-profile></gt-candidate-profile>'
                    }
                }
            })
            .state('candidates.profile.edit', {
                url: '/edit',
                views: {
                    '@site': {
                        template: '<gt-candidate-edit></gt-candidate-edit>'
                    }
                }
            })
            .state('candidates.profile.verify', {
                url: '/verify',
                views: {
                    '@site': {
                        template: '<gt-candidate-verify></gt-candidate-verify>'
                    }
                }
            })

            // FAQ
            .state('support', {
                parent: 'site',
                url: '/support',
                views: {
                    '@site': {
                        template: '<gt-support></gt-support>'
                    }
                }
            })

            // Onboard
            .state('onboard', {
                parent: 'site',
                url: '/onboard',
                redirectTo: 'onboard.welcome'
            })
            .state('onboard.welcome', {
                url: '/welcome',
                views: {
                    '@site': {
                        template: '<gt-onboard-welcome></gt-onboard-welcome>'
                    }
                }
            })
            .state('onboard.build', {
                url: '/build',
                views: {
                    '@site': {
                        template: '<gt-onboard-build></gt-onboard-build>'
                    }
                }
            })
            .state('onboard.organize', {
                url: '/organize',
                views: {
                    '@site': {
                        template: '<gt-onboard-organize></gt-onboard-organize>'
                    }
                }
            })
            .state('onboard.engage', {
                url: '/engage',
                views: {
                    '@site': {
                        template: '<gt-onboard-engage></gt-onboard-engage>'
                    }
                }
            })
            .state('onboard.getStarted', {
                url: '/get-started',
                views: {
                    '@site': {
                        template: '<gt-onboard-get-started></gt-onboard-get-started>'
                    }
                }
            })
            .state('onboard.noData', {
                url: '/no-data',
                views: {
                    '@site': {
                        template: '<gt-onboard-no-data></gt-onboard-no-data>'
                    }
                }
            })

            // Pipelines
            .state('pipelines', {
                abstract: true,
                parent: 'site',
                url: '/pipelines',
                views: {
                    '@site': {
                        template: '<gt-pipelines></gt-pipelines>'
                    }
                }
            })
            .state('pipelines.overview', {
                url: '',
                views: {
                    '@pipelines': {
                        template: '<gt-pipelines-overview></gt-pipelines-overview>'
                    }
                },
                ncyBreadcrumb: {
                    parent: 'dashboard',
                    label: 'Pipelines'
                }
            })
            .state('pipelines.manage', {
                url: '/manage',
                views: {
                    '@pipelines': {
                        template: '<gt-pipelines-manage></gt-pipelines-manage>'
                    }
                }
            })
            .state('pipelines.create', {
                url: '/create',
                views: {
                    '@pipelines': {
                        template: '<gt-pipeline-create></gt-pipeline-create>'
                    }
                }
            })
            .state('pipelines.pipeline', {
                url: '/:pipelineId',
                redirectTo: 'pipelines.pipeline.detail'
            })
            .state('pipelines.pipeline.detail', {
                url: '',
                views: {
                    '@pipelines': {
                        template: '<gt-pipeline-detail></gt-pipeline-detail>'
                    }
                },
                ncyBreadcrumb: {
                    parent: 'pipelines.overview',
                    label: 'Pipeline detail'
                }
            })
            .state('pipelines.pipeline.settings', {
                url: '/settings',
                views: {
                    '@pipelines': {
                        template: '<gt-pipeline-settings></gt-pipeline-settings>'
                    }
                }
            })
            .state('pipelines.pipeline.team', {
                url: '/team',
                views: {
                    '@pipelines': {
                        template: '<gt-pipeline-team></gt-pipeline-team>'
                    }
                }
            })
            .state('pipelines.pipeline.smartLists', {
                url: '/smart-lists',
                views: {
                    '@pipelines': {
                        template: '<gt-smart-lists></gt-smart-lists>'
                    }
                }
            })
            .state('pipelines.pipeline.smartLists.create', {
                url: '/create',
                views: {
                    '@pipelines': {
                        template: '<gt-smart-list-create></gt-smart-list-create>'
                    }
                }
            })
            .state('pipelines.pipeline.smartLists.smartList', {
                url: '/:pipelineId',
                redirectTo: 'pipelines.pipeline.smartLists.smartList.detail'
            })
            .state('pipelines.pipeline.smartLists.smartList.detail', {
                url: '',
                views: {
                    '@pipelines': {
                        template: '<gt-smart-list-details></gt-smart-list-details>'
                    }
                }
            })

            // Search
            .state('search', {
                parent: 'site',
                url: '/search',
                views: {
                    '@site': {
                        template: '<gt-search></gt-search>'
                    }
                }
            })

            // User
            .state('user', {
                abstract: true,
                parent: 'site',
                url: '/user',
                views: {
                    '@site': {
                        template: '<gt-user></gt-user>'
                    }
                }
            })
            .state('user.profile', {
                url: '/profile',
                views: {
                    '@user': {
                        template: '<gt-user-profile></gt-user-profile>'
                    }
                }
            })
            .state('user.account', {
                url: '/account',
                views: {
                    '@user': {
                        template: '<gt-user-account></gt-user-account>'
                    }
                }
            })
            .state('user.permissions', {
                url: '/permissions',
                views: {
                    '@user': {
                        template: '<gt-user-permissions></gt-user-permissions>'
                    }
                }
            })
            .state('user.customFields', {
                url: '/custom-fields',
                views: {
                    '@user': {
                        template: '<gt-custom-fields></gt-custom-fields>'
                    }
                }
            })
            .state('user.emailMarketing', {
                url: '/email-marketing',
                views: {
                    '@user': {
                        template: '<gt-email-marketing></gt-email-marketing>'
                    }
                }
            })
            .state('user.organization', {
                url: '/organization',
                views: {
                    '@user': {
                        template: '<gt-organization></gt-organization>'
                    }
                }
            })
            .state('user.organization.invite', {
                url: '/invite',
                views: {
                    '@user': {
                        template: '<gt-organization-invite></gt-organization-invite>'
                    }
                }
            })
            .state('user.settings', {
                url: '/settings',
                views: {
                    '@user': {
                        template: '<gt-settings></gt-settings>'
                    }
                }
            })
            .state('user.widgetOptions', {
                url: '/widget-options',
                views: {
                    '@user': {
                        template: '<gt-widget-options></gt-widget-options>'
                    }
                }
            })
            .state('user.widgets', {
                abstract: true,
                url: '/widgets'
            })
            .state('user.widgets.add', {
                url: '/add',
                views: {
                    '@user': {
                        template: '<gt-widget-add></gt-widget-add>'
                    }
                }
            })
            .state('user.widgets.widget', {
                url: '/:widgetId',
                redirectTo: 'user.widgets.widget.edit'
            })
            .state('user.widgets.widget.edit', {
                url: '/edit',
                views: {
                    '@user': {
                        template: '<gt-widget-edit></gt-widget-edit>'
                    }
                }
            })

            // Talent Pools
            .state('talentPools', {
                parent: 'site',
                url: '/talent-pools',
                redirectTo: 'talentPools.manage'
            })
            .state('talentPools.dashboard', {
                abstract: true,
                url: '/dashboard'
            })
            .state('talentPools.dashboard.candidates', {
                url: '/candidates',
                views: {
                    '@site': {
                        template: '<gt-talent-pools-dashboard-candidates></gt-talent-pools-dashboard-candidates>'
                    }
                }
            })
            .state('talentPools.dashboard.pipelines', {
                url: '/pipelines',
                views: {
                    '@site': {
                        template: '<gt-talent-pools-dashboard-pipelines></gt-talent-pools-dashboard-pipelines>'
                    }
                }
            })
            .state('talentPools.dashboard.teams', {
                url: '/teams',
                views: {
                    '@site': {
                        template: '<gt-talent-pools-dashboard-teams></gt-talent-pools-dashboard-teams>'
                    }
                }
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
                        template: '<gt-talent-pool-create></gt-talent-pool-create>'
                    }
                }
            })
            .state('talentPools.talentPool', {
                url: '/:poolId',
                redirectTo: 'talentPools.talentPool.detail'
            })
            .state('talentPools.talentPool.detail', {
                url: '',
                views: {
                    '@site': {
                        template: '<gt-talent-pool-detail></gt-talent-pool-detail>'
                    }
                }
            });
    }
})();
