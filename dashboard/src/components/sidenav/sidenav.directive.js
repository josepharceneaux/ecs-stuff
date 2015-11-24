(function () {
    'use strict';

    angular
        .module('app.sidenav')
        .directive('gtSidenav', directiveFunction)
        .controller('SidenavController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/sidenav/sidenav.html',
            replace: true,
            scope: {
            },
            controller: 'SidenavController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state'];

    /* @ngInject */
    function ControllerFunction($state) {
        var vm = this;
        vm.isCollapsed = true;
        vm.state = $state;
        vm.menuItems = {
            dashboard: {
                overview: 'Overview',
                customize: 'Customize'
            },
            pipeline: {
                overview: 'Overview',
                smartLists: 'Smart Lists',
                candidateSearch: 'Candidate Search',
                importCandidates: 'Import Candidates'
            },
            campaigns: {
                overview: 'Overview',
                emailCampaigns: 'Email Campaigns',
                smsCampaigns: 'SMS Campaigns',
                socialMediaCampaigns: 'Social Media Campaigns',
                contentCampaigns: 'Content Campaigns',
                pushNotifications: 'Push Notifications'
            },
            admin: {}
        };
    }
})();
