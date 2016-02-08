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
        vm.removeActivity = removeActivity;

        activate();
        init();

        function activate() {
            logger.log('Activated Notification Center');
        }

        function init() {
            notificationCenterService.addListener('openStateChanged', setOpen);
            notificationCenterService.setOpen(vm.isOpen);
            getActivityMessages().then(getActivity);

        }

        function getActivity() {
            var activityRequest = notificationService.getActivity();
            vm.activity = activityRequest.$object;
            vm.unreadActivity = [];

            activityRequest.then(function () {
                notificationCenterService.broadcast('activityCountChanged', vm.activity.length);
                vm.activity.forEach(function (item) {
                    item.added_time = moment(item.added_time).toDate();
                    var messages  = getFormattedMessage(item);
                    item.toastrMessage = messages.toastr;
                    item.feedMessage = messages.feed;
                    var css = notificationService.getCss(item.type);
                    item.icon = css.icon;
                    item.class = css.class;
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
                var toastrMessage = message;
                var feedMessage = message;
                for (var key in params) {
                    // TODO: DO it for user and campaign
                    var href  = createLink(type, params, key, activity);
                    feedMessage = feedMessage.replace('%(' + key + ')s', href + params[key] + '</a>');
                    toastrMessage = toastrMessage.replace('%(' + key + ')s', '<strong>' + params[key] + '</strong>');
                }
                return {toastr: toastrMessage, feed: feedMessage};
            }
            return '';
        }

        function createLink(type, params, key, activity){
            // in case of a candidate added in smartlist
            if (type == 10 && 'candidateId' in params && key == 'formattedName'){
               return "<a href='candidates/"+ params.candidateId+"'>";
            }
            // if someone creates a campaign
            else if (type == 4 && ['email_campaign', 'sms_campaign', 'push_campaign'].indexOf(activity.source_table) != -1){
                return "<a href='campaigns/"+ activity.source_id+"'>";
            }
            // if a candidate opened an campaign / email
            else if (type == 16 && 'candidateId' in params && key == 'candidate_name'){
               return "<a href='candidates/"+ params.candidateId+"'>";
            }
            else {
                return '<a href="#">';
            }
        }

        function showMessage(){
            notificationCenterService.broadcast('activityCountChanged', vm.activity.length);
            var activity = vm.activity.pop();
            if (activity && !vm.hideNotifications && !vm.isBarOpen){
                var message = activity.toastrMessage || 'No message';
                toastr.success(message, 'Notification', {
                    onHidden: showMessage,
                    onTap: function(){
                        setOpen(true);
                    },
                    iconClass: activity.icon,
                    toastClass: activity.class
                });
            }

        }

        function removeActivity(id){
            debugger;
            vm.activity.forEach(function(item, index){
                if (item.id == id){
                    vm.activity.splice(index,1);
                    return false;
                }
            })
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
