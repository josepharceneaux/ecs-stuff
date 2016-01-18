(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolsCreate', directiveFunction)
        .controller('TalentPoolsCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pools-create/talent-pools-create.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolsCreateController',
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
            logger.log('Activated Talent Pools Create View');
        }

        function init() {
            //
        }
    }
})();
