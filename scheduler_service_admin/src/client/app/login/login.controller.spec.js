/* jshint -W117, -W030 */
describe('LoginController', function() {
  var controller;

  beforeEach(function() {
    bard.appModule('app.login');
    bard.inject('$httpBackend','$controller', '$log', '$rootScope');
  });

  beforeEach(function() {
    mockService($httpBackend);
    controller = $controller('LoginController');
    $rootScope.$apply();
  });

  specHelper.verifyNoOutstandingHttpRequests();

  describe('Login controller', function() {
    it('should be created successfully', function() {
      expect(controller).to.be.defined;
    });

    describe('after activate', function() {
      it('should have title of Admin', function() {
        expect(controller.title).to.equal('Login');
      });

      it('should have logged "Activated"', function() {
        expect($log.info.logs).to.match(/Activated/);
      });
    });
  });
});
