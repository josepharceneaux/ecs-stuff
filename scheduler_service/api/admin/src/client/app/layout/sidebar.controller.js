(function() {
  'use strict';

  angular
    .module('app.layout')
    .controller('SidebarController', SidebarController);

  SidebarController.$inject = ['$state', 'routerHelper'];
  /* @ngInject */
  //Get all states except login and build NavRoutes.
  function SidebarController($state, routerHelper) {
    var vm = this;
    var states = routerHelper.getStates();

    removeLoginState(states);

    vm.isCurrent = isCurrent;

    activate();

    function activate() { getNavRoutes(); }

    function getNavRoutes() {
      vm.navRoutes = states.filter(function(r) {
        return r.settings && r.settings.nav;
      }).sort(function(r1, r2) {
        return r1.settings.nav - r2.settings.nav;
      });
    }

    function isCurrent(route) {
      if (!route.title || !$state.current || !$state.current.title) {
        return '';
      }
      var menuName = route.title;
      return $state.current.title.substr(0, menuName.length) === menuName ? 'current' : '';
    }

    function removeLoginState(states){

        for(var i = states.length -1; i >= 0 ; i--){
            if(states[i].name == 'login'){
              states.splice(i, 1);
            break;
          }
      }
    }
  }
})();
