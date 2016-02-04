(function() {
	'use strict';

	angular.module('app.core')
		.factory('pipelineService', serviceFunction);

	serviceFunction.$inject = ['$q', 'candidatePoolService'];

	/* @ngInject */
	function serviceFunction($q, candidatePoolService) {
		var service = {
			getPipeline: getPipeline,
			getPipelines: getPipelines,
			getPipelineSmartlists: getPipelineSmartlists,
			getSmartlistsCandidates: getSmartlistsCandidates
		};

		return service;

		function getPipeline(id) {
			var p = {
				name: 'Pipeline1'
			};
			return candidatePoolService.one('talent-pipelines', id);
			//return $q.when(p);
		}
		function getPipelines() {
			var p = {
				name: 'Pipeline1'
			};
			return candidatePoolService.all('talent-pipelines').getList();
			//return $q.when(p);
		}
		function getPipelineSmartlists(id) {
			return candidatePoolService.one('talent-pipeline', id).all('smartlists').getList();
		}

		function getSmartlistsCandidates(id) {
			return candidatePoolService.one('smartlists', id).all('candidates').getList();
		}


	}
})();