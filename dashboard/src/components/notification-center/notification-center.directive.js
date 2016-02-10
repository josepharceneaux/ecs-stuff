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
    ControllerFunction.$inject = ['$timeout', '$q', '$cookies', 'logger', 'toastr',
        'notificationService', 'notificationCenterService', 'localStorage'];

    /* @ngInject */
    function ControllerFunction($timeout, $q, $cookies, logger, toastr, notificationService,
                                notificationCenterService, localStorage) {
        var vm = this;

        // Time in seconds to updated activities periodically
        var UPDATE_ACTIVITY_INTERVAL = 10;

        // unforamted messages to show proper message according to activity type and params
        vm.messages = [];

        // List of user activities to be shown in activity feed
        vm.activities = [];

        // an object where keys are activity ids to maintain which activities have been shown
        // if some activities from server do not exists in this collection, show a notification
        // count on bell and also updated vm.activities list
        vm.activityIds = localStorage.getObject('activityIds') || {};

        // it contains only ids of activities which have been shown as toasts. So if server
        // sends same activities that have been shown as toast then don't show that toast
        // for those that have ids in this collection
        vm.activityToastIds = localStorage.getObject('activityToastIds') || {};

        // contains activities that needed to be shown as toast.
        vm.newActivityIds = {};

        // flag to determine whether to show toasts or not
        vm.hideNotifications = false;

        // when user saw activities last time
        vm.lastReadTime = false;
        var count = localStorage.getObject('notificationCount');
        vm.notificationCount = isNaN(count) ? 0 : count;

        vm.removeSingleActivity = removeSingleActivity;
        vm.toggleNotificationCenter = notificationCenterService.toggle;

        activate();
        init();
        notificationCenterService.addListener('clearActivity', function(){
            if (vm.activities.length > 100){
                // if on logout, we have more than hundred activities in memory,
                // then clear it to avoid too much memory usage
                localStorage.setObject('activityIds', {});
            }

            if (Object.keys(vm.activityToastIds).length > 50){
                // On logout, if there are more than 50 toast still to be shown, then clear
                // this data to avoid too much memory usage
                localStorage.setObject('activityToastIds', {});
            }
            vm.activities = [];
        });

        function activate() {
            logger.log('Activated Notification Center');
        }

        function init() {
            notificationCenterService.addListener('openStateChanged', setOpen);
            notificationCenterService.setOpen(vm.isOpen);
            initActivities();
            getLastReadTime().then(function(){
                getActivity();
            });
            // Updated activities after every one minute
            setInterval(getActivity, UPDATE_ACTIVITY_INTERVAL * 1000);
        }

        function getActivity() {
            var messagesRequest = getActivityMessages();
            var activityRequest = notificationService.getActivity(vm.lastReadTime);
            var promise = $q.all([messagesRequest, activityRequest]);
            promise.then(function (responses) {
                var activities = responses[1];
                vm.activityIndex = 0;
                vm.activityIds = localStorage.getObject('activityIds') || {};
                activities.forEach(function (activity) {
                    if (!(activity.id in vm.activityIds)) {
                        vm.activities.push(activity);
                        vm.activityIds[activity.id] = activity;
                        vm.notificationCount += 1;
                    }
                });
                localStorage.setObject('notificationCount', vm.notificationCount);
                vm.activities.forEach(function (activity) {
                    activity.added_time = moment(activity.added_time).toDate();
                    var messages  = getFormattedMessage(activity);
                    activity.toastrMessage = messages.toastr;
                    activity.feedMessage = messages.feed;
                    var css = notificationService.getCss(activity.type);
                    activity.icon = css.icon;
                    activity.class = css.class;
                    vm.newActivityIds[activity.id] = activity;
                });
                localStorage.setObject('activityIds', vm.activityIds);
                if (vm.notificationCount > 0) {
                    if (!notificationCenterService.isOpen){
                        $cookies.put('isActivityCountHidden', false);
                        notificationCenterService.activityCountChanged(vm.notificationCount);
                    }
                    //toastr.info('You have <strong>%d</strong> unread notifications'.replace('%d', vm.activities.length), '<p>Notifications</p>');
                }
                showToast();
            });
        }

        function getLastReadTime(){
            return notificationService.getLastReadTime().then(function(res){
                vm.lastReadTime = moment(res.last_read_datetime).toDate();
                return vm.lastReadTime;
            })
        }

        function setLastReadTime(){
            return notificationService.setLastReadTime().then(function(res){
                vm.lastReadTime = moment(res.last_read_datetime).toDate();
                return vm.lastReadTime;
            })
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
                    var href  = createLink(type, params, key, activity);
                    feedMessage = feedMessage.replace('%(' + key + ')s', href + params[key] + '</a>');
                    toastrMessage = toastrMessage.replace('%(' + key + ')s', '<strong>' + params[key] + '</strong>');
                }
                return {toastr: toastrMessage, feed: feedMessage};
            }
            return '';
        }

        function initActivities(){
            vm.activityIds = localStorage.getObject('activityIds') || {};
            for (var id in vm.activityIds){
                vm.activities.push(vm.activityIds[id]);
                notificationCenterService.activityCountChanged(vm.activities.length);
            }

        }

        function createLink(type, params, key, activity){
            // in case of a candidate added in smartlist
            if (type === 10 && 'candidateId' in params && key === 'formattedName'){

               return '<a ui-sref="candidates.profile({ profileId: ' + params.candidateId + ' })">'; //"<a href='candidates/"+ params.candidateId+"'>";
            }
            // if someone creates a campaign
            else if (type === 4 && ['email_campaign', 'sms_campaign', 'push_campaign'].indexOf(activity.source_table) !== -1 && key === 'campaign_name'){
                return '<a ui-sref="campaigns.campaign({ campaignId: ' + activity.socurce_id + ' })">'; //"<a href='campaigns/"+ activity.source_id+"'>";
            }
            // if a candidate opened an campaign / email
            else if (type === 16 && 'candidateId' in params && key === 'candidate_name'){
               return '<a ui-sref="candidates.profile({ profileId: ' + params.candidateId + ' })">';// "<a href='candidates/"+ params.candidateId+"'>";
            }
            else {
                return '<a href="#">';
            }
        }

        function showToast(){

            vm.activityToastIds = localStorage.getObject('activityToastIds') || {};
            var id = Object.keys(vm.newActivityIds).pop();
            if (id && !(id in vm.activityToastIds)){
                var activity = vm.newActivityIds[id];

                if (!vm.hideNotifications && !vm.isBarOpen){
                    delete vm.newActivityIds[id];
                    vm.activityToastIds[id] = id;
                    localStorage.setObject('activityToastIds', vm.activityToastIds);
                    var message = activity.toastrMessage;
                    if (message){
                        toastr.success(message, {
                            onHidden: showToast,
                            onTap: function(){
                                setOpen(true);
                            },
                            iconClass: activity.icon,
                            toastClass: activity.class
                        });
                    }
                }
            } else if(id){
                delete vm.newActivityIds[id];
                if (Object.keys(vm.newActivityIds).length){
                    showToast();
                }
            }
        }

        function removeSingleActivity(id){
            vm.activities.forEach(function(activity, index){
                if (activity.id == id){
                    vm.activities.splice(index, 1);
                    vm.activityIds = localStorage.getObject('activityIds') || {};
                    delete vm.activityIds[id];
                    localStorage.setObject('activityIds',vm.activityIds);
                    vm.activityToastIds = localStorage.getObject('activityToastIds') || {};
                    vm.activityToastIds[id] = id;
                    localStorage.setObject('activityToastIds',vm.activityToastIds);
                }
            })
        }

        function setOpen(value) {
            if (value) {
                setLastReadTime();
                notificationCenterService.removeAllToasts();
                notificationCenterService.hideNotificationCount();
                vm.notificationCount = 0;
                localStorage.setObject('notificationCount', 0);
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
