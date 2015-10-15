/* global _ */

(function() {
    'use strict';

    angular
        .module('app.core')
        .constant('_', _)
        .constant('authInfo', {
            baseUrl: 'https://secure-webdev.gettalent.com',
            //baseUrl: 'https://private-67134-gettalentauth.apiary-mock.com',
            clientId: 'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921UX1',
            clientSecret: 'DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYjMw',
            grantPath: '/oauth2/token'
        });
})();
