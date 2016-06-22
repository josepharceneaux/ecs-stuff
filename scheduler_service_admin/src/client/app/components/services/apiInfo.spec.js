/**
 * Created by saad on 6/12/16.
 */

describe('UserToken', function () {

  var apiInfoService;
  beforeEach(function() {
    bard.appModule('app.core');
    bard.inject('$httpBackend', '$log', '$rootScope', 'apiInfo');
  });

  beforeEach(function() {
    mockService($httpBackend);
    apiInfoService = apiInfo;

    $rootScope.$apply();
  });

  bard.verifyNoOutstandingHttpRequests();

  describe('API Info Service', function() {

    it('should be created successfully', function () {
      expect(apiInfoService).to.be.defined;
    });

    it('should read apiInfo', function () {
      apiInfoService.readApiInfo().then(function (response) {
        expect(apiInfoService.apiInfo).to.deep.equal(apiConfig.apiInfo);
      });

      $httpBackend.flush();

    });

  });
});
