(function () {
    'use strict';

    angular.module('app.candidates')
        .directive('gtCandidateAdd', directiveFunction)
        .controller('CandidateAddController', ControllerFunction);

    // ----- directiveFunction -----
    directiveFunction.$inject = [];

    /* @ngInject */
    function directiveFunction() {

        var directive = {
            restrict: 'E',
            templateUrl: 'components/candidates/candidate-add/candidate-add.html',
            replace: true,
            scope: {},
            controller: 'CandidateAddController',
            controllerAs: 'vm'
        };

        return directive;
    }

    // ----- ControllerFunction -----
    ControllerFunction.$inject = ['$q', 'logger', 'candidatesAddService', 'resumeService'];

    /* @ngInject */
    function ControllerFunction($q, logger, candidatesAddService, resumeService) {
        var vm = this;

        init();
        activate();

        function activate() {
            logger.log('Activated Candidate Add View');
        }

        function init() {
            vm.candidateForm = {
                firstName: null,
                lastName: null,
                email: null,
                talent_pools: null
            };
            vm.successfullResponses = [];
            vm.failedResponses = [];

            vm.manualSubmit = function() {
                candidatesAddService.postCandidate(vm.candidateForm).then(function (response) {
                    if ('error' in response) {
                        // Do Some error handling
                        console.log('ERROR: ', response.error.message)
                    }
                    else {
                        // Inform that success occured
                        console.log('SUCCESS: ', response)
                    }
                })
            };

            vm.postFpKey = function(filepickerKey) {
                var candidate_params = {filepicker_key: filepickerKey,
                    resume_file_name: filepickerKey, create_candidate: true};
                console.log(candidate_params);
                resumeService.all('parse_resume').post(candidate_params).then(
                    // Success State
                    function (response) {
                        if ('error' in response) {
                            console.log('Error: ', response.error);
                            vm.failedResponses.push(
                                {filename: candidate_params.resume_file_name,
                                    error: response.error}
                            );
                        }
                        else {
                            console.log('Success! ', response.candidate);
                            vm.successfullResponses.push(candidate_params.resume_file_name)
                        }
                    },
                    // Failure State
                    function (response) {
                        console.log(response.data.error.message);
                        vm.failedResponses.push(
                            {filename: candidate_params.resume_file_name,
                                error: response.data.error.message}
                        );
                    }
                )
            };

            // Should only be able to add once this has completed.
            candidatesAddService.getUserTalentPools().then(function (response) {
                var i;
                var talentPoolIds = [];
                for (i = 0; i < response.length; i++) {
                    talentPoolIds.push(response[i].id);
                }
                vm.candidateForm.talentPools = talentPoolIds;
                console.log('Talent Pool IDs obtained for user.');
            });

            vm.fpInit = function() {
                console.log('initializing FilePicker');
                filepicker.setKey("Ay99lw0fFRXKz5n4qpXCmz");
                filepicker.pickAndStore(
                    {
                        mimetypes:[
                            'application/pdf',
                            'image/jpeg',
                            'image/pjpeg',
                            'image/png',
                            'image/tiff',
                            'image/gif',
                            'image/x-ms-bmp',
                            'image/pcx',
                            'image/jp2',
                            'image/jpc',
                            'image/vnd.djvu',
                            'application/msword',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            'application/vnd.oasis.opendocument.text',
                            'application/vnd.oasis.opendocument.text-web',
                            'application/vnd.oasis.opendocument.text-template',
                            'application/vnd.oasis.opendocument.text-master',
                            'text/plain',
                            'application/rtf',
                            'text/rtf'
                        ],
                        container: 'modal',
                        maxFiles: 10000,
                        multiple: true,
                        services: ['COMPUTER', 'BOX', 'CLOUDDRIVE', 'GOOGLE_DRIVE', 'DROPBOX', 'GMAIL', 'URL', 'FLICKR', 'EVERNOTE', 'INSTAGRAM', 'SKYDRIVE', 'IMAGE_SEARCH', 'WEBCAM', 'FACEBOOK', 'GITHUB', 'CUSTOMSOURCE']
                    },
                    {
                        location: 'S3'
                    },
                    function(Blobs) {
                        var filepickerKeys = [];
                        $.each(Blobs, function() {
                            if (!this.key) {
                                console.error('An error occured during import of resume: %s', this.url);
                                return false;
                            }
                            filepickerKeys.push(this.key)
                        });
                        if (filepickerKeys.length != Blobs.length && Blobs.length) {
                            return false;
                        }
                        var i;
                        for (i = 0; i < filepickerKeys.length; i++) {
                            vm.postFpKey(filepickerKeys[i]);
                        }
                    },
                    function(FPError) {
                        console.error("Error response to parse_filepicker_resume: ", FPError.toString());
                    }
                );
            }
        }
    }
})();
