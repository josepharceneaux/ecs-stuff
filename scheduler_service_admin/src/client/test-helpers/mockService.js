/**
 * Created by saad on 6/12/16.
 */

var apiConfig = {

      "apiInfo": {
          "authService": {
            "baseUrl": "http://localhost:8001/v1",
            "clientId": "KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z",
            "clientSecret": "DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z",
            "grantPath": "http://localhost:8001/v1/oauth2/token",
            "authorizePath": "http://localhost:8001/v1/oauth2/authorize"
          },
          "schedulerServiceAdmin": {
            "taskUrl": "http://localhost:8011/v1/admin/tasks"
          },
          "userService": {
            "baseUrl": "http://127.0.0.1:8004/v1/users/",
            "userRolesPath": "/roles"
          }
        }
    };

var allTasks = {
  tasks: [
    {
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
            },
    {
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


function mockService($httpBackend) {
    $httpBackend.when('GET', '/api/api-config').respond(apiConfig);
    $httpBackend.when('POST', apiConfig.apiInfo.authService.grantPath).respond({access_token: "Bearer xyz", refresh_token: "xyz"});
    $httpBackend.when('GET', apiConfig.apiInfo.authService.authorizePath).respond(200, {
            "user_id": "1"
        });

    $httpBackend.when('GET', apiConfig.apiInfo.userService.baseUrl.concat("1", apiConfig.apiInfo.userService.userRolesPath
    , "?role_id_only=false")).respond(200, {
            roles: [{name: "CAN_GET_ALL_SCHEDULER_JOBS", id: 2},
            {name: "DUMMY_PERMISSION", id: 3}]
        });

    $httpBackend.when('GET', apiConfig.apiInfo.schedulerServiceAdmin.taskUrl).respond(200, allTasks);
}


