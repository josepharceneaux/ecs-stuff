(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignDetail', directiveFunction)
        .controller('CampaignDetailController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-detail/campaign-detail.html',
            scope: {
            },
            controller: 'CampaignDetailController',
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
            logger.log('Activated Campaign Detail View');
        }

        function init() {
            //
        }
    }
})();
