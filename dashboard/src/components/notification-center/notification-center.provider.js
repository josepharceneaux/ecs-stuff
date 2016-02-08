(function () {
    'use strict';

    angular
        .module('app.notificationCenter')
        .provider('notificationCenterService', providerFunction);

    /**
     * @return {[type]}
     */
    function providerFunction() {
        this.$get = $get;

        $get.$inject = [];

        /* @ngInject */
        function $get() {
            var isLockedOpen = false;
            var isOpen = false;
            var events = {
                opened: 'opened',
                closed: 'closed',
                locked: 'locked',
                unlocked: 'unlocked',
                activityCountChanged: 'activityCountChanged',
                openStateChanged: 'openStateChanged',
                lockStateChanged: 'lockStateChanged',
                clearActivity: 'clearActivity'
            };
            var listeners = {};

            Object.keys(events).map(function (key) {
                listeners[events[key]] = [];
            });

            return {
                isLockedOpen: isLockedOpen,
                isOpen: isOpen,
                setOpen: setOpen,
                toggle: toggle,
                open: open,
                close: close,
                lock: lock,
                unlock: unlock,
                addListener: addListener,
                broadcast: broadcast
            };

            function isLockedOpen() {
                return isLockedOpen;
            }



            function isOpen() {
                return isOpen;
            }

            function setOpen(value) {
                if (value === true) {
                    open();
                } else {
                    close();
                }
            }

            function toggle() {
                if (isOpen) {
                    close();
                } else {
                    open();
                }
            }

            function open() {
                if (!isOpen) {
                    isOpen = true;
                    broadcast(events.openStateChanged, isOpen);
                    broadcast(events.opened);
                }
            }

            function close() {
                if (isOpen && !isLockedOpen) {
                    isOpen = false;
                    broadcast(events.openStateChanged, isOpen);
                    broadcast(events.closed);
                }
            }

            function lock() {
                isLockedOpen = true;
                broadcast(events.lockStateChanged, isLockedOpen);
                broadcast(events.locked);
            }

            function unlock() {
                isLockedOpen = false;
                broadcast(events.lockStateChanged, isLockedOpen);
                broadcast(events.unlocked);
            }

            function addListener(eventName, listener) {
                if (eventName in listeners && typeof listener === 'function') {
                    listeners[eventName].push(listener);
                    return getRemoveListener(eventName, listener);
                }
                return angular.noop;
            }

            function getRemoveListener(eventName, listener) {
                return function removeListener() {
                    var index = listeners[eventName].indexOf(listener);
                    if (index !== -1) {
                        listeners[eventName].splice(index, 1);
                    }
                }
            }

            function broadcast(eventName, value) {
                if (eventName in listeners) {
                    listeners[eventName].forEach(function (listener) {
                        listener.call(null, value);
                    });
                }
            }

        }
    }

})();
