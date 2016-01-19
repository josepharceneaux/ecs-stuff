(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolCreate', directiveFunction)
        .controller('TalentPoolCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pool-create/talent-pool-create.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolCreateController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Talent Pool Create View');
        }

        function init() {
            //
        }
    }
})();
