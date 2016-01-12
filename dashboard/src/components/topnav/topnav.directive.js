(function () {
    'use strict';

    angular
        .module('app.topnav')
        .directive('gtTopnav', directiveFunction)
        .controller('TopnavController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/topnav/topnav.html',
            replace: true,
            scope: {
            },
            controller: 'TopnavController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'OAuthToken'];

    /* @ngInject */
    function ControllerFunction($state, OAuthToken) {
        var vm = this;
        vm.isCollapsed = true;
        vm.logout = logout;

        init();

        function init() {
            vm.userProfilePicThumbSrc = './images/placeholder/profile.png';
            vm.dashboardScopeOptions = [
                { id: 'sr-java-developers', name: 'Sr Java Developers' },
                { id: 'jr-java-engineers', name: 'Jr Java Engineers' },
                { id: 'developers-in-nevada', name: 'Developers in Nevada' }
            ];
            vm.selectedDashboardScope = vm.dashboardScopeOptions[0];

            vm.talentPools = [
                {
                    name: 'Talent Pool 1'
                },
                {
                    name: 'Talent Pool 2'
                },
                {
                    name: 'Talent Pool 3'
                }
            ];
            vm.selectedTalentPool = vm.talentPools[0];

            vm.pipelines = [
                {
                    name: 'Pipeline 1'
                },
                {
                    name: 'Pipeline 2'
                },
                {
                    name: 'Pipeline 3'
                }
            ];

            vm.campaigns = [
                {
                    name: 'Campaign 1'
                },
                {
                    name: 'Campaign 2'
                },
                {
                    name: 'Campaign 3'
                }
            ];
        }

        function logout() {
            OAuthToken.removeToken();
            $state.go('login');
        }
    }
})();
