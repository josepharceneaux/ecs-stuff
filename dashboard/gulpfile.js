/* jshint node: true, -W024, -W040, -W098, -W126 */

'use strict';

/**
 * yargs variables can be passed in to alter the behavior, when present.
 * Example: gulp serve-dev
 *
 * --verbose  : Various tasks will produce more output to the console.
 * --nosync   : Don't launch the browser with browser-sync when serving code.
 * --debug    : Launch debugger with node-inspector.
 * --debug-brk: Launch debugger and break on 1st line with node-inspector.
 * --startServers: Will start servers for midway tests on the test task.
 */

var gulp = require('gulp');
var config = require('./gulp.config')();

var buildTask = (function buildTask(config, taskFile) {
    require('./gulp-tasks/' + taskFile)(config);
}).bind(null, config);

[
    'serve',
    'vet',
    'styles',
    'clean',
    'plato',
    'assets',
    'template-cache',
    'inject',
    'optimize',
    'test',
    'bump',
    'config'
].forEach(buildTask);

gulp.task('help', config.$.taskListing);
gulp.task('default', ['help']);

module.exports = gulp;
