(function() {
    'use strict';

    angular
        .module('fw.logger')
        .factory('logger', logger);

    logger.$inject = ['$log', 'toastr'];

    /* @ngInject */
    function logger($log, toastr) {
        var service = {
            log     : log,
            info    : info,
            success : success,
            warn    : warn,
            error   : error,
            debug   : debug
        };

        return service;
        /////////////////////

        function log(/*arg1[, arg2[, arg3...]]*/) {
            $log.log.apply(this, ['log:'].concat(Array.prototype.slice.call(arguments)));
        }

        function info(/*arg1[, arg2[, arg3...]]*/) {
            toastr.info(toString(arguments), 'Information');
            $log.info.apply(this, ['info:'].concat(Array.prototype.slice.call(arguments)));
        }

        function success(/*arg1[, arg2[, arg3...]]*/) {
            toastr.success(toString(arguments), 'Success');
            $log.info.apply(this, ['success:'].concat(Array.prototype.slice.call(arguments)));
        }

        function warn(/*arg1[, arg2[, arg3...]]*/) {
            toastr.warning(toString(arguments), 'Warning');
            $log.warn.apply(this, ['warn:'].concat(Array.prototype.slice.call(arguments)));
        }

        function error(/*arg1[, arg2[, arg3...]]*/) {
            toastr.error(toString(arguments), 'Error');
            $log.error.apply(this, ['error:'].concat(Array.prototype.slice.call(arguments)));
        }

        function debug(/*arg1[, arg2[, arg3...]]*/) {
            $log.debug.apply(this, ['debug:'].concat(Array.prototype.slice.call(arguments)));
        }

        function toString(args) {
            return Array.prototype.reduce.call(args, function (prev, curr) {
                return prev + ' ' + (typeof curr === 'object' && curr ? angular.toJson(curr) : curr);
            }, '');
        }
    }
}());
