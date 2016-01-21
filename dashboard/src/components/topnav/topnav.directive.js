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
            scope: {},
            controller: 'TopnavController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$state', 'OAuth'];

    /* @ngInject */
    function ControllerFunction($state, OAuth) {
        var vm = this;
        vm.isCollapsed = true;
        vm.logout = logout;

        init();

        function init() {
            vm.talentPools = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Talent Pool 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Talent Pool 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Talent Pool 3'
                }
            ];
            vm.selectedTalentPool = vm.talentPools[0];

            vm.pipelines = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Pipeline 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Pipeline 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Pipeline 3'
                }
            ];

            vm.campaigns = [
                {
                    id: '0cc175b9c0f1b6a831c399e269772661',
                    name: 'Campaign 1'
                },
                {
                    id: '187ef4436122d1cc2f40dc2b92f0eba0',
                    name: 'Campaign 2'
                },
                {
                    id: '900150983cd24fb0d6963f7d28e17f72',
                    name: 'Campaign 3'
                }
            ];
        }

        function logout() {
            OAuth.revokeToken();
            $state.go('login');
        }
    }
})();
