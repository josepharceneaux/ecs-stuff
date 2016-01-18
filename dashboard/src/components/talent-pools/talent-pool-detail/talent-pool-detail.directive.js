(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolDetail', directiveFunction)
        .controller('TalentPoolDetailController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pool-detail/talent-pool-detail.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolDetailController',
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
            logger.log('Activated Talent Pool Detail View');
        }

        function init() {
            //
        }
    }
})();
