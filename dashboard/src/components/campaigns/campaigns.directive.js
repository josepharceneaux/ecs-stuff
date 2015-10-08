(function () {

    'use strict';

    angular.module('app.campaigns')
        .directive('gtCampaigns', directiveFunction)
        .controller('CampaignsController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/campaigns.html',
            scope: {
            },
            controller: 'CampaignsController',
            controllerAs: 'vm'
        };

        return directive;
    }


    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger'];

    /* @ngInject */
    function ControllerFunction(logger) {

        activate();

        function activate() {
            logger.log('Activated Campaigns View');
        }
    }

})();
