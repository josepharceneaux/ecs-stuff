/**
 * Created by saad on 6/12/16.
 */

describe('UserToken', function () {

  var userTokenService;
  beforeEach(function() {
    bard.appModule('app.components');
    module('app.core');
    module('ngCookies');
    bard.inject('$httpBackend', '$log', '$rootScope', 'apiInfo', 'UserToken', '$cookies');
  });

  beforeEach(function() {
    mockService($httpBackend);
    userTokenService = UserToken;
    apiInfo.apiInfo = apiConfig.apiInfo;

    $rootScope.$apply();
  });

  bard.verifyNoOutstandingHttpRequests();

  describe('UserToken Factory - Test login', function() {

    it('should be created successfully', function() {
      expect(userTokenService).to.be.defined;
    });

    it('should return response with token pair (bearer token and refresh token)', function () {
          userTokenService.login('saadfast.qc@gmail.com', 'xyz').then(function (response) {
            expect(response.status).to.equal(200);
            expect(response.data.access_token).to.equal("Bearer xyz");
            expect(response.data.refresh_token).to.equal("xyz");
          });

          $httpBackend.flush();
        });

    it('should return unauthroized response', function () {
      $httpBackend.expect('POST', apiConfig.apiInfo.authService.grantPath, function (data) {
        return data === $.param({
          username: 'saadfast.qc@gmail.com',
          password: 'invalid pass',
          grant_type: 'password',
          client_id: apiInfo.apiInfo.authService.clientId,
          client_secret: apiInfo.apiInfo.authService.clientSecret
        });
      }).respond(401);

          userTokenService.login('saadfast.qc@gmail.com', 'invalid pass').then(function (response) {
            expect(response.status).to.equal(401);
          });

          $httpBackend.flush();
        });

    it('should authorize user', function () {
          userTokenService.isLoggedIn().then(function (response) {
            expect(response).to.equal(true);
          });

          $httpBackend.flush();
        });

    it('should not authorize user', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.authService.authorizePath, undefined, function (headers) {
          return headers.Authorization === "Bearer undefined";
          }).respond(401);

          userTokenService.isLoggedIn().then(function (response) {
            expect(response).to.equal(false);
          });

          $httpBackend.flush();
        });
  });

  var token;

  describe('UserToken Factory - Test Login Cycle', function () {
    beforeEach(function () {

      userTokenService.login('saadfast.qc@gmail.com', 'xyz').then(function (response) {
            token = {
              access_token: response.data.access_token,
              expires_in: response.data.expires_in
            }
          });

          $httpBackend.flush();
        });

      it('should authenticate user', function () {
          userTokenService.authenticate(token);
          expect($cookies.get('token')).to.equal('Bearer xyz');
      });

    it('should authenticate that user has admin privileges', function () {
          userTokenService.testAuthenticateUserRole(1, token.access_token)
            .then(function (response) {
              expect(response.status).to.equal(200);
              expect(response.data.roles).to.include({name: "CAN_GET_ALL_SCHEDULER_JOBS", id: 2});
            });

      $httpBackend.flush();

      });

    afterEach(function () {

      userTokenService.logout();
      expect($cookies.get('token')).toBeUndefined;
    });
  });

});
