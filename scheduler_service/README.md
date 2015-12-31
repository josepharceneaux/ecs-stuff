## Scheduler Service API

Scheduler Service allows user to schedule their delayed and periodic tasks
asynchronously. In our case, we are sending email, SMS and push notification
campaigns and we need to schedule these campaigns so that we can send the messages 
later e.g after every month or week or day.

### Flow:
  In Scheduler Service, there are two kinds of tasks. Using this service users can schedule either a one time or 
  a periodic task.
  When the task's time is due then this service will run that task asynchronously. Down below we have given an example
  which will hopefully clear things up. 
  

  Using `flower` we can check the status for all the scheduled tasks.
  
Scheduler Task:
    Scheduler has the ability to run a task either periodically or just for one time.
    
Task type:
  - one_time => Runs only one time. 
  - periodic => Runs peridically as per a given frequency. It runs whenever its time is due and ends when stop_datetime is reached.
   
### Examples:     

**I have a long running task (e.g. sending SMS campaign) and I want to run this task every day, how do I do this using Scheduler Service?**
       
We have to do few things in order for that to happen. 
   - User will send a POST request to `http://scheduler-srevice.gettalent.com/tasks` in order to get his task scheduled.
   - Scheduler Service will hit that URL (specified in your original POST) daily.
   - The URL which is hit daily basically contains the impelmentation of your long running task.
       
So let's say my code sends SMS campains and it needs to be run daily. I will send a 
POST request as below
           
    
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
    }
    
    
So now Scheduler Serivce will hit the `http://getTalent.com/sms/send/` (assuming my long running SMS task is impemented
behind this endpoint) daily with POST data (as given in post_data) until `2016-01-05T08:00:00`. 
Avoid using current_datetime as start_datetime when scheduling job. Because there might be delay when hitting schedule endpoint. 
In that case, job will not be scheduled and throws exception `start_datetime` should be in future. To resolve that, add a delay of few seconds.
    
       
### Group Schedule Task

Resources related to scheduler tasks.

### Schedule/Create a periodic task or one_time task  [/tasks/]

A task object has the following attributes:
- Task
    + `id (string):` task id in getTalent database
    + `frequency (dict):` containing information about the task frequency, i.e. run it after every 2 days or after each 5 hours. 
        Possible values is integer greater or equal to 3600 (Seconds). For dev version, the minimum allowed value is 4 seconds.
    + `url (string):` URL where given data will be sent as a post request
    + `task_type (string):` type of job which needs to run periodicically or one time (periodic in this case). 
    Possible values are: `one_time, periodic`.
    + `post_data (dictionary):` data to be sent to given URL, it is a dictionary which can have any values inside.
    For example, in case of SMS campaign, it will be    
    

    
            "post_data": {
                            "phone_number": "09234562348",
                            "smart_list_id": 123456,
                            "content": "text to be sent as sms",
                        }
    
    
        But in case of email campaign, data may contain many other params
    


            "post_data": {
                            "email": "user_email@gmail.com",
                            "smart_list_id": 123456,
                            "email_content": "text to be sent as email",
                            "cc": ["cc1@gmail.com", "cc2@gmail.com"]
                        }
            
    

    + `start_datetime (datetime):` time at which scheduler will start executing this task
    + `end_datetime (datetime):` time after which scheduler will not run this task 
       and remove the task from job store
    + There are some examples below on how to create periodic and one time tasks.



### Get all task [GET]

Returns a list of all task for a specific user.

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
            
+ Response 200 (application/json)

    + Body

            {
                "count": 1,
                "tasks": [
                            {
                                "id": "5das76nbv950nghg8j8433ddd3kfdw2",
                                "url": "http://getTalent.com/sms/send/",
                                "post_data": {
                                    "phone_number": "09230862348",
                                    "smart_list_id": 123456,
                                    "content": "text to be sent as sms",
                                    "other_param1": "abc",
                                    "other_param2": 123
                                },
                                "frequency": 3601, 
                                "start_datetime": "2015-11-05 08:00:00",
                                "end_datetime": "2015-12-05 08:00:00",
                                "next_run_datetime": "2015-11-06 08:00:00"
                            }
               ]
            }
        
+ Response 500 (application/json)
        
    + Body
    
            {
                "error": {"message": "APIError: Internal Server error while retrieving records" }
            }

### Schedule a Task [POST]

One can schedule a task by sending a POST request to this endpoint with
data containing task information.

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
            Content-Type: application/json

    + Body

            For interval job scheduling
            {
                "frequency": 3601, 
                "task_type": "periodic",
                "start_datetime": "2015-12-05 08:00:00",
                "end_datetime": "2016-01-05 08:00:00",
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
                }
                
            }
            
            For one_time job  scheduling
            {
                "task_type": "one_time",
                "run_datetime": "2015-12-05 08:00:00",
                "url": "http://getTalent.com/sms/send/",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms"
                }
                
            }

+ Response 201 (application/json)

    + Headers
    
            Location: /tasks/5das76nbv950nghg8j8-33ddd3kfdw2
    + Body

            {
                "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                "message": "Task has been scheduled successfully"
            }
            
+ Response 401 (application/json)

    + Body
    
            {
                "error" : {"message": "User Not authorized"}
            }

+ Response 500 (application/json)

    + Body
    
            {
                "error": { "message": "APIError: Internal Server error occurred!" }
            }
            

### Task by Id [/tasks/id/{id}]

+ Parameters
    + id (required) - ID of the task in getTalent database


### Get task detail[GET]

Returns a task details based on task id. User can only get his own tasks.

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)

    + Body

            {
                "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                "url": "http://getTalent.com/sms/send/",
                "task_type": "peridic",
                "post_data": {
                    "campaign_name": "SMS Campaign",
                    "phone_number": "09230862348",
                    "smart_list_id": 123456,
                    "content": "text to be sent as sms",
                    "other_param1": "abc",
                    "other_param2": 123
                },
                "frequency": 3601, 
                "start_datetime": "2015-11-05 08:00:00",
                "end_datetime": "2015-12-05 08:00:00",
                "next_run_datetime": "2015-11-06 08:00:00"
            }
        
+ Response 500 (application/json)
        
    + Body
    
            {
                "error" : {"message": "APIError: Unable to serialize task data" }
            }

+ Response 404 (application/json)
        
    + Body
    
            {
                "error" : {"message": "APIError: task does not exist with given id"}
            }
        



### Remove a task [DELETE]

Remove a task now, it will remove the task from job store and it will not be executed afterwards.

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
        

+ Response 200 (application/json)
        
    + Body
        
            {
                "message": "Task has been removed successfully"
            }

+ Response 401 (application/json)

    + Body
            
            {
                "error" : {"message": "User not authorized"}
            }
            
            
+ Response 403 (application/json)

    + Body
        
            {
                "error" : {"message": "Forbidden: Task does not belong to this user"}
            }
            
            
            
+ Response 404 (application/json)

    + Body
        
            {
                "error" : {"message": "Task not found"}
            }
            
            
### Resume a task by Id [/tasks/{id}/resume/]

### Resume a task [POST]

Resume a task that was paused earlier. 

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
        

+ Response 200 (application/json)
        
    + Body
        
            {
                "message": "Task resumed successfully"
            }

+ Response 401 (application/json)

    + Body
            
            {
                "error" : {"message": "User not authorized"}
            }
            
            
+ Response 403 (application/json)

    + Body
        
            {
                "error" : {"message": "Forbidden: Task does not belong to this user"}
            }
            
            
+ Response 404 (application/json)

    + Body
        
            {
                "error" : {"message": "Task not found"}
            }


### Pause a task by Id [/tasks/{id}/pause/]

### Pause a task [POST]

Pause a task using task id. This task will not be removed from job store (database) 
and it can be resumed again using scheduler service.


+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
        

+ Response 200 (application/json)
        
    + Body
        
            {
                "message": "Task paused successfully"
            }

+ Response 401 (application/json)

    + Body
            
            {
                "error" : {"message": "User not authorized"}
            }
            
            
+ Response 403 (application/json)

    + Body
        
            {
                "error" : {"message": "Forbidden: Task does not belong to this user"}
            }
            
            
+ Response 404 (application/json)

    + Body
        
            {
                "error" : {"message": "Task not found"}
            }
            

### Resume multiple task by Id [/tasks/resume/]

### Resume multiple task [POST]

Resume tasks that was paused earlier. 

+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
            Content-Type: application/json

    + Body
    
            {
                "ids": ["fasdff12n22m2jnr5n6skf","ascv3h5k1j43k6k8k32k345jmn","123n23n4n43m2kkcj53vdsxc"]
            }
        

+ Response 200 (application/json)
        
    + Body
        
            {
                "message": "Tasks have been resumed successfully"
            }

+ Response 401 (application/json)

    + Body
            
            {
                "error" : {"message": "User not authorized"}
            }
            
            
+ Response 403 (application/json)

    + Body
        
            {
                "error" : {"message": "Forbidden: Task does not belong to this user"}
            }
            
            
+ Response 404 (application/json)

    + Body
        
            {
                "error" : {"message": "Task not found"}
            }


### Pause multiple tasks using Id [/tasks/pause/]

### Pause multiple tasks [POST]

Pause multiple tasks using task ids. These tasks will not be removed from job store (database) 
and they can be resumed again using scheduler service.


+ Request

    + Headers
        
            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE
            Content-Type: application/json

    + Body
    
            {
                    "ids": ["fasdff12n22m2jnr5n6skf","ascv3h5k1j43k6k8k32k345jmn","123n23n4n43m2kkcj53vdsxc"]
            }
        

+ Response 200 (application/json)
        
    + Body
        
            {
                "message": "Tasks have been successfully paused"
            }

+ Response 401 (application/json)

    + Body
            
            {
                "error" : {"message": "User not authorized"}
            }
            
            
+ Response 403 (application/json)

    + Body
        
            {
                "error" : {"message": "Forbidden: Task does not belong to this user"}
            }
            
            
+ Response 404 (application/json)

    + Body
        
            {
                "error" : {"message": "Task not found"}
            }
