(function () {
    'use strict';

    angular
        .module('app.notificationCenter')
        .directive('gtNotificationCenter', directiveFunction)
        .controller('NotificationCenterController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/notification-center/notification-center.html',
            replace: true,
            scope: {},
            controller: 'NotificationCenterController',
            controllerAs: 'vm',
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['logger', 'toastr', 'notificationService'];

    /* @ngInject */
    function ControllerFunction(logger, toastr, notificationService) {
        var vm = this;

        activate();
        init();

        function activate() {
            logger.log('Activated Notification Center');
        }

        function init() {
            var activityRequest = notificationService.getActivity()
            vm.activity = activityRequest.$object;
            vm.unreadActivity = [];

            activityRequest.then(function () {
                vm.activity.forEach(function (item, i) {
                    if (!item.read) {
                        vm.unreadActivity.unshift(item);
                    }
                });
                if (vm.unreadActivity.length > 1) {
                    toastr.info('You have <strong>%d</strong> unread notifications'.replace('%d', vm.unreadActivity.length), '<p>Notifications</p>');
                } else if (vm.unreadActivity.length === 1) {
                    toastr.info('<a href="">$name</a> opened your email from the <a href="">campaign</a> of name here.'.replace('$name', vm.unreadActivity[0].params.firstName + ' ' + vm.unreadActivity[0].params.lastName), 'Unread Activity');
                }
            });
        }
    }
})();
