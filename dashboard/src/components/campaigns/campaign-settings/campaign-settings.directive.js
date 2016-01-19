(function () {
    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaignSettings', directiveFunction)
        .controller('CampaignSettingsController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaign-settings/campaign-settings.html',
            replace: true,
            scope: {},
            controller: 'CampaignSettingsController',
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
            logger.log('Activated Campaign Settings View');
        }

        function init() {
            //
        }
    }
})();
