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
            scope: {
                isOpen: '=open'
            },
            controller: 'NotificationCenterController',
            controllerAs: 'vm',
            bindToController: true,
            link: linkFunction
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$timeout', 'logger', 'toastr', 'notificationService', 'notificationCenterService'];

    /* @ngInject */
    function ControllerFunction($timeout, logger, toastr, notificationService, notificationCenterService) {
        var vm = this;
        vm.time = new Date();
        vm.toggleNotificationCenter = notificationCenterService.toggle;
        vm.messages = [];
        vm.hideNotifications = false;
        activate();
        init();

        function activate() {
            logger.log('Activated Notification Center');
        }

        function init() {
            notificationCenterService.addListener('openStateChanged', setOpen);
            notificationCenterService.setOpen(vm.isOpen);
            getActivityMessages().then(getActivity);
            //getActivity();

        }

        function getActivity() {
            var activityRequest = notificationService.getActivity();
            vm.activity = activityRequest.$object;
            vm.unreadActivity = [];

            activityRequest.then(function () {
                notificationCenterService.broadcast('activityCountChanged', vm.activity.length);
                vm.activity.forEach(function (item, i) {
                    item.added_time = moment(item.added_time).toDate();
                    item.message = getFormattedMessage(item);
                    if (!item.read) {
                        vm.unreadActivity.unshift(item);
                    }
                });
                if (vm.unreadActivity.length > 1) {
                    toastr.info('You have <strong>%d</strong> unread notifications'.replace('%d', vm.unreadActivity.length), '<p>Notifications</p>');
                } else if (vm.unreadActivity.length === 1) {
                    toastr.info('<a href="">$name</a> opened your email from the <a href="">campaign</a> of name here.'.replace('$name', vm.unreadActivity[0].params.firstName + ' ' + vm.unreadActivity[0].params.lastName), 'Unread Activity');
                }
                showMessage();
            });
        }

        function getActivityMessages(){
            return notificationService.getActivityMessages()
                .then(function(res){
                    vm.messages = res.messages;
                    return vm.messages;
                });
        }

        function getFormattedMessage(activity){
            var type = activity.type;
            var params = activity.params;
            if (activity.type in vm.messages){
                var message = vm.messages[type][0];
                for (var key in params){
                    message = message.replace('%('+key+')s', '<strong>' + params[key] + '</strong>');
                }
                return message;
            }
            return '';
        }

        function showMessage(){
            notificationCenterService.broadcast('activityCountChanged', vm.activity.length);
            var activity = vm.activity.pop();
            if (activity && !vm.hideNotifications){
                var css = notificationService.getCss(activity.type);
                var message = '<span class="feed__item__sub" am-time-ago="activity.added_time"></span>' + activity.message || 'No message';
                toastr.success(message, 'Notification', {
                    onHidden: showMessage,
                    iconClass: css.icon,
                    toastClass: css.class
                });
            }

        }

        function setOpen(value) {
            if (value) {
                open();
            } else {
                close();
            }
        }

        function open() {
            vm.isBarOpen = true;
            notificationCenterService.open();
            $timeout(function () {
                vm.isInnerOpen = true;
            }, 200);
        }

        function close() {
            vm.isBarOpen = false;
            vm.isInnerOpen = false;
        }
    }

    function linkFunction(scope, elem, attrs) {
        //
    }
})();
