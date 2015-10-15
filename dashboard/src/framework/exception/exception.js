(function() {
    'use strict';

    angular
        .module('fw.exception')
        .factory('exception', exception);

    exception.$inject = ['logger'];

    /* @ngInject */
    function exception(logger) {
        var service = {
            catcher: catcher
        };
        return service;

        function catcher(message) {
            return function(reason) {
                logger.error(message, reason);
            };
        }
    }
})();
