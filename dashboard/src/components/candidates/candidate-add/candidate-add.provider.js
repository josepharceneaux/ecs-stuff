(function () {
    'user strict';

    angular
        .module('app.candidates')
        .provider('candidatesAddService', providerFunction);

    function providerFunction() {
        this.$get = $get;

        $get.$inject = ['candidateService', 'candidatePoolService'];

        /* @ngInect */
        function $get(candidateService, candidatePoolService) {
            function postCandidate(candidateObj) {
                console.log('preparing to POST candidate data');
                var formattedCandidate = {
                    candidates: [{
                        first_name: candidateObj.firstName,
                        last_name: candidateObj.lastName,
                        emails: [{address: candidateObj.email}],
                        talent_pool_ids: {
                            "add": candidateObj.talentPools
                        }
                    }]
                };
                return candidateService.all('candidates').post(formattedCandidate).then(
                    // Success State
                    function (candidateResponse) {
                        return candidateResponse.candidates[0]
                    },
                    // Failure State
                    function (candidateResponse) {
                        return candidateResponse.data
                    }
                )
            }

            function getUserTalentPools() {
                return candidatePoolService.one('talent-pools').customGET().then(
                    function (talentPools) {
                        return talentPools.talent_pools
                    }
                )
            }

            return {
                getUserTalentPools: getUserTalentPools,
                postCandidate: postCandidate
            }
        }
    }
})();