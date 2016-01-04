var gulp = require('gulp');

module.exports = function (config) {
    config.log('Importing test.js...');

    var log = config.log;
    var args = config.args;

    /**
     * Run specs once and exit
     * To start servers and run midway specs as well:
     *    gulp test --startServers
     * @return {Stream}
     */
    gulp.task('test', ['vet', 'templatecache'], function(done) {
        startTests(true /*singleRun*/ , done);
    });

    /**
     * Run specs and wait.
     * Watch for file changes and re-run tests on each change
     * To start servers and run midway specs as well:
     *    gulp autotest --startServers
     */
    gulp.task('autotest', function(done) {
        startTests(false /*singleRun*/ , done);
    });

    /**
     * Start the tests using karma.
     * @param  {boolean} singleRun - True means run once and end (CI), or keep running (dev)
     * @param  {Function} done - Callback to fire when karma is done
     * @return {undefined}
     */
    function startTests(singleRun, done) {
        var child;
        var excludeFiles = [];
        var fork = require('child_process').fork;
        var karma = require('karma').server;
        var serverSpecs = config.serverIntegrationSpecs;

        if (args.startServers) {
            log('Starting servers');
            var savedEnv = process.env;
            savedEnv.NODE_ENV = 'dev';
            savedEnv.PORT = 8888;
            child = fork(config.nodeServer);
        } else {
            if (serverSpecs && serverSpecs.length) {
                excludeFiles = serverSpecs;
            }
        }

        karma.start({
            configFile: __dirname + '/../karma.conf.js',
            exclude: excludeFiles,
            singleRun: !!singleRun
        }, karmaCompleted);

        ////////////////

        function karmaCompleted(karmaResult) {
            log('Karma completed');
            if (child) {
                log('shutting down the child process');
                child.kill();
            }
            if (karmaResult === 1) {
                done('karma: tests failed with code ' + karmaResult);
            } else {
                done();
            }
        }
    }
};
