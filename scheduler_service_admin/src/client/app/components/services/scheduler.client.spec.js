/**
 * Created by saad on 6/12/16.
 */


describe('SchedulerClientService', function () {

  var apiInfoService,
    schedulerClientService,
    userTokenService;
  beforeEach(function() {
    bard.appModule('app.core');
    bard.appModule('app.components');
    bard.inject('$httpBackend', '$log', 'UserToken', '$rootScope', 'apiInfo', 'SchedulerClientService', '$cookies');
  });

  var oneTimeTasks = {
    tasks: [
    {
       "user_id": "1",
            "user_email": "saad_lhr@hotmail.com",
                      "task_category": "user",
                      "task_type": "one_time",
                      "run_datetime": "2015-12-05T08:00:00-05:00",
                      "url": "http://getTalent.com/sms/send/",
                      "post_data": {
                          "campaign_name": "Push Campaign",
                          "smart_list_id": 93456,
                          "content": "Text to show"
                      }
                  }
        ]
      };

  var periodicTasks = {
    tasks: [
          {
             "user_id": "1",
            "user_email": "saad_lhr@hotmail.com",
                      "task_category": "user",
                      "frequency": 3601,
                      "task_type": "interval",
                      "start_datetime": "2015-12-05T08:00:00-05:00",
                      "end_datetime": "2016-01-05T08:00:00-05:00",
                      "url": "http://getTalent.com/sms/send/",
                      "post_data": {
                          "campaign_name": "SMS Campaign",
                          "phone_number": "09230862348",
                          "smart_list_id": 123456,
                          "content": "text to be sent as sms"
                      }
                  }
        ]
      };

  var userTasks = {
    tasks: [
          {
             "user_id": "1",
            "user_email": "saad_lhr@hotmail.com",
                      "task_category": "user",
                      "frequency": 3601,
                      "task_type": "interval",
                      "start_datetime": "2015-12-05T08:00:00-05:00",
                      "end_datetime": "2016-01-05T08:00:00-05:00",
                      "url": "http://getTalent.com/sms/send/",
                      "post_data": {
                          "campaign_name": "SMS Campaign",
                          "phone_number": "09230862348",
                          "smart_list_id": 123456,
                          "content": "text to be sent as sms"
                      }
                  }
        ]
      };

  var generalTasks = {
    tasks: [
          {
                      "task_category": "general",
                      "frequency": 3601,
                      "task_type": "interval",
                      "start_datetime": "2015-12-05T08:00:00-05:00",
                      "end_datetime": "2016-01-05T08:00:00-05:00",
                      "url": "http://getTalent.com/sms/send/",
                      "post_data": {
                          "campaign_name": "SMS Campaign",
                          "phone_number": "09230862348",
                          "smart_list_id": 123456,
                          "content": "text to be sent as sms"
                      }
                  }
        ]
      };

  var pausedTasks = {
    tasks: [
          {
             "user_id": "1",
            "user_email": "saad_lhr@hotmail.com",
                      "task_category": "user",
                      "frequency": 3601,
                      "task_type": "interval",
                      "start_datetime": "2015-12-05T08:00:00-05:00",
                      "end_datetime": "2016-01-05T08:00:00-05:00",
                      "url": "http://getTalent.com/sms/send/",
                      "post_data": {
                          "campaign_name": "SMS Campaign",
                          "phone_number": "09230862348",
                          "smart_list_id": 123456,
                          "content": "text to be sent as sms"
                      }
                  }
        ]
      };


  beforeEach(function() {
    mockService($httpBackend);
    apiInfo.apiInfo = apiConfig.apiInfo;
    apiInfoService = apiInfo;
    userTokenService = UserToken;
    schedulerClientService = SchedulerClientService;

    $rootScope.$apply();
  });

  bard.verifyNoOutstandingHttpRequests();

  describe('Scheduler Client Service', function() {

    beforeEach(function () {
      userTokenService.access_token = "Bearer xyz";
    });

    it('should be created successfully', function () {
      expect(schedulerClientService).to.be.defined;
    });

    it('should get all tasks', function () {
      schedulerClientService.getTasks({}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(allTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all one_time tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_category=one_time'))
        .respond(oneTimeTasks);

      schedulerClientService.getTasks({'task_category': 'one_time'}).then(function (response) {
        console.log(response.data.tasks);
          expect(response.data.tasks).to.deep.equal(oneTimeTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all periodic tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_category=periodic'))
        .respond(periodicTasks);

      schedulerClientService.getTasks({'task_category': 'periodic'}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(periodicTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all user tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_type=user'))
        .respond(userTasks);

      schedulerClientService.getTasks({'task_type': 'user'}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(userTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all general tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_type=general'))
        .respond(generalTasks);

      schedulerClientService.getTasks({'task_type': 'general'}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(generalTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all paused tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?paused=true'))
        .respond(pausedTasks);

      schedulerClientService.getTasks({'paused': 'true'}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(pausedTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get all paused and user tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_type=user&paused=true'))
        .respond(pausedTasks);

      schedulerClientService.getTasks({'task_type': 'user', 'paused': 'true'}).then(function (response) {
          expect(response.data.tasks).to.deep.equal(pausedTasks.tasks);
      });

      $httpBackend.flush();

    });

    it('should get general and userId=1 tasks', function () {

      $httpBackend.expect('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl.concat('?task_type=general&userId=1'))
        .respond({tasks:[]});

      schedulerClientService.getTasks({'task_type': 'general', 'userId': 1}).then(function (response) {
          expect(response.data.tasks).to.deep.equal([]);
      });

      $httpBackend.flush();

    });

  });
});
