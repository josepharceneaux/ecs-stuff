(function () {
    'use strict';

    angular.module('app.talentPools')
        .directive('gtTalentPoolsManage', directiveFunction)
        .controller('TalentPoolsManageController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/talent-pools/talent-pools-manage/talent-pools-manage.html',
            replace: true,
            scope: {},
            controller: 'TalentPoolsManageController',
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
            logger.log('Activated Talent Pools Manage View');
        }

        function init() {
            //
        }
    }
})();
