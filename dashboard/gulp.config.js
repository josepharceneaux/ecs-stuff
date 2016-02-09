/* jshint node: true, -W024, -W040, -W098, -W126, -W069 */

'use strict';

module.exports = function () {

    var src = './src/';
    var test = './test/';
    var temp = './.tmp/';
    var bowerComponents = './bower_components/';

    var $ = require('gulp-load-plugins')({lazy: true});
    var wiredep = require('wiredep');
    var bowerFiles = wiredep({devDependencies: true})['js'];
    var path = require('path');
    var _ = require('lodash');

    var config = {

        // --- Configurables ---
        sourceDir: src,
        testDir: test,
        buildDir: './build/',
        tempDir: temp,
        proxyPort: 7203,
        port: 3000,
        browserReloadDelay: 1000,
        serverIntegrationSpecs: [test + 'server-integration/**/*.spec.js'],
        nodeServer: '../mock-server/app.js',
        /**
         * File paths
         */
        // all javascript that we want to vet
        //alljs: [
        //    './src/**/*.js',
        //    './*.js'
        //],
        alljs: [
            src + '**/*.js',
            test + '**/*.js',
            './*.js'
        ],
        plato: {
            js: src + '**/*.js'
        },
        report: './report',
        js: [
            // module files in desired order
            src + '**/*.module.js',

            // remaining files in desired order
            src + 'core/**/*.js',
            src + 'framework/**/*.js',
            src + '**/*.js'
        ],
        html: src + '**/*.html',
        sass: src + '**/*.scss',
        iconfont: src + 'core/icon-font/**/*.svg',
        fonts: [
            // custom app fonts
            src + 'fonts/**/*.*',

            // third party fonts go here
            bowerComponents + 'font-awesome/fonts/**/*.*'
        ],
        $: $,
        args: require('yargs').argv,

        // --- Utilities ---
        errorLogger: errorLogger,
        log: log,
        notify: notify
    };

    /**
     * karma settings
     */
    config.karma = getKarmaOptions();

    return config;

    ////////////////

    function getKarmaOptions() {
        var options = {
            files: [].concat(
                bowerFiles,
                //config.specHelpers,
                //clientApp + '**/*.module.js',
                //clientApp + '**/*.js',
                //temp + config.templateCache.file,
                //config.serverIntegrationSpecs

                'test/helpers/*.js',
                'src/**/*.module.js',
                'src/**/*.js',
                '.tmp/templates.js',
                'test/**/*.spec.js'
            ),
            exclude: [],
            coverage: {
                dir: 'report/coverage',
                reporters: [
                    // reporters not supporting the `file` property
                    {type: 'html', subdir: 'report-html'},
                    {type: 'lcov', subdir: 'report-lcov'},
                    // reporters supporting the `file` property, use `subdir` to directly
                    // output them in the `dir` directory.
                    // omit `file` to output to the console.
                    // {type: 'cobertura', subdir: '.', file: 'cobertura.txt'},
                    // {type: 'lcovonly', subdir: '.', file: 'report-lcovonly.txt'},
                    // {type: 'teamcity', subdir: '.', file: 'teamcity.txt'},
                    // {type: 'text'}, subdir: '.', file: 'text.txt'},
                    {type: 'text-summary'} //, subdir: '.', file: 'text-summary.txt'}
                ]
            },
            preprocessors: {}
        };
        options.preprocessors['src/**/!(*.spec)+(.js)'] = ['coverage'];
        return options;
    }

    /**
     * Log an error message and emit the end of a task
     */
    function errorLogger(error) {
        log('*** Start of Error ***');
        log(error);
        log('*** End of Error ***');
        this.emit('end');
    }

    /**
     * Log a message or series of messages using chalk's blue color.
     * Can pass in a string, object or array.
     */
    function log(msg) {
        if (typeof(msg) === 'object') {
            for (var item in msg) {
                if (msg.hasOwnProperty(item)) {
                    $.util.log($.util.colors.blue(msg[item]));
                }
            }
        } else {
            $.util.log($.util.colors.blue(msg));
        }
    }

    /**
     * Show OS level notification using node-notifier
     */
    function notify(options) {
        var notifier = require('node-notifier');
        var notifyOptions = {
            sound: 'Bottle',
            contentImage: path.join(__dirname, 'gulp.png'),
            icon: path.join(__dirname, 'gulp.png')
        };
        _.assign(notifyOptions, options);
        notifier.notify(notifyOptions);
    }
};
