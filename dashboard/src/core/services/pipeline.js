(function() {
	'use strict';

	angular.module('app.core')
		.factory('pipelineService', serviceFunction);

	serviceFunction.$inject = ['$q'];

	/* @ngInject */
	function serviceFunction($q) {
		var service = {};

		return service;

		function getPipeline(id) {
			var p = {
				name: 'Pipeline1'
			};

			return $q.when(p);
		}
	}
})();