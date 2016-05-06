/* jshint -W117, -W030 */
describe('SchedulerAdminController', function() {
  var controller;

  beforeEach(function() {
    bard.appModule('app.scheduler_admin');
    bard.inject('$controller', '$log', '$rootScope');
  });

  beforeEach(function() {
    controller = $controller('SchedulerAdminController');
    $rootScope.$apply();
  });

  bard.verifyNoOutstandingHttpRequests();

  describe('Scheduler Admin controller', function() {
    it('should be created successfully', function() {
      expect(controller).to.be.defined;
    });

    describe('after activate', function() {
      it('should have title of Admin', function() {
        expect(controller.title).to.equal('Scheduler Service Admin');
      });

      it('should have logged "Activated"', function() {
        expect($log.info.logs).to.match(/Activated/);
      });
    });
  });
});
