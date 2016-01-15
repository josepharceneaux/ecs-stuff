(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignCreate', directiveFunction)
        .controller('CampaignCreateController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-create/campaign-create.html',
            scope: {
            },
            controller: 'CampaignCreateController',
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
            logger.log('Activated Campaign Create View');
        }

        function init() {
            //
        }
    }
})();
