(function () {

    'use strict';

    angular.module('app.campaigns')
        .directive('gtPushNotifications', directiveFunction)
        .controller('PushNotificationsController', ControllerFunction);


    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/campaigns/push-notifications/push-notifications.html',
            scope: {
            },
            controller: 'PushNotificationsController',
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
            logger.log('Activated Push Notifications View');
        }
    }

})();
