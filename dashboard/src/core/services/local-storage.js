/**
 * Created by zohaib on 2/10/16.
 */
(function() {
	'use strict';

	angular.module('app.core')
		.factory('localStorage', serviceFunction);

	serviceFunction.$inject = ['$window'];

	/* @ngInject */
	function serviceFunction($window) {
		return {
            set: function(key, value) {
              $window.localStorage[key] = value;
            },
            get: function(key, defaultValue) {
              return $window.localStorage[key] || defaultValue;
            },
            setObject: function(key, value) {
              $window.localStorage[key] = JSON.stringify(value);
            },
            getObject: function(key) {
              return JSON.parse($window.localStorage[key] || '{}');
            }
          };
	}
})();