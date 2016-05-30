(function() {
  'use strict';

  angular
    .module('app.core')
    .run(appRun);

  appRun.$inject = ['routerHelper', 'api_info'];

  /* @ngInject */
  function appRun(routerHelper, api_info) {
    var otherwise = '/404';
    routerHelper.configureStates(getStates(), otherwise);

    api_info.read_apiInfo();
  }

  function getStates() {
    return [
      {
        state: '404',
        config: {
          url: '/404',
          templateUrl: 'app/core/404.html',
          title: '404'
        }
      }
    ];
  }
})();
