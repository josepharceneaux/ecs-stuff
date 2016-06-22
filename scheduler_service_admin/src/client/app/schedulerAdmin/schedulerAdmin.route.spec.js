/* jshint -W117, -W030 */
describe('admin routes', function() {
  describe('state', function() {
    var view = 'app/schedulerAdmin/schedulerAdmin.html';

    beforeEach(function() {
      module('app.schedulerAdmin', bard.fakeToastr);
      bard.inject('$httpBackend', '$location', '$rootScope', '$state', '$templateCache');
    });

    beforeEach(function() {
      $templateCache.put(view, '');
    });

    it('should map state admin to url /schedulerAdmin ', function() {
      expect($state.href('schedulerAdmin', {})).to.equal('/');
    });

    it('should map /schedulerAdmin route to admin View template', function() {
      expect($state.get('schedulerAdmin').templateUrl).to.equal(view);
    });

    it('of admin should work with $state.go', function() {
      $state.go('schedulerAdmin');
      $rootScope.$apply();
      expect($state.is('schedulerAdmin'));
    });
  });
});
