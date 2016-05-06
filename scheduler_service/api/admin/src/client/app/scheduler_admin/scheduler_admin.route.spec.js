/* jshint -W117, -W030 */
describe('admin routes', function() {
  describe('state', function() {
    var view = 'app/scheduler_admin/scheduler_admin.html';

    beforeEach(function() {
      module('app.scheduler_admin', bard.fakeToastr);
      bard.inject('$httpBackend', '$location', '$rootScope', '$state', '$templateCache');
    });

    beforeEach(function() {
      $templateCache.put(view, '');
    });

    it('should map state admin to url /scheduler_admin ', function() {
      expect($state.href('scheduler_admin', {})).to.equal('/scheduler_admin');
    });

    it('should map /scheduler_admin route to admin View template', function() {
      expect($state.get('scheduler_admin').templateUrl).to.equal(view);
    });

    it('of admin should work with $state.go', function() {
      $state.go('scheduler_admin');
      $rootScope.$apply();
      expect($state.is('scheduler_admin'));
    });
  });
});
