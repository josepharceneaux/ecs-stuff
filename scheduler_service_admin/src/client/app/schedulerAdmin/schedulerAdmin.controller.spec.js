/* jshint -W117, -W030 */

describe('SchedulerAdminController', function() {
  var controller, apiService;

  beforeEach(function() {
    bard.appModule('app.schedulerAdmin');
    module('ngMockE2E');
    bard.inject('$httpBackend', '$controller', '$log', '$rootScope', 'apiInfo');
  });

  beforeEach(function() {
    mockService($httpBackend);
    apiService = apiInfo;

    apiInfo.apiInfo = apiConfig.apiInfo;

    controller = $controller('SchedulerAdminController');
    $rootScope.$apply();

  });

  bard.verifyNoOutstandingHttpRequests();

  describe('Scheduler Admin controller', function() {

    it('should return response of all mock URLs', function () {

            expect(apiInfo.apiInfo).to.equal(apiConfig.apiInfo);
        });

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
