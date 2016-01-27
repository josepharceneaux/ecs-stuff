(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignsManage', directiveFunction)
        .controller('CampaignsManageController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaigns-manage/campaigns-manage.html',
            replace: true,
            scope: {},
            controller: 'CampaignsManageController',
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
            logger.log('Activated Campaigns Manage View');
        }

        function init() {
            //
        }
    }
})();
