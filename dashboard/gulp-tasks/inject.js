var gulp = require('gulp');

module.exports = function (config) {
    config.log('Importing inject.js...');

    var $ = config.$;

    gulp.task('inject', ['config', 'styles', 'templatecache'], function () {
        return gulp
            .src(config.sourceDir + 'index.html')
            .pipe($.inject(gulp.src(config.js)))
            .pipe($.inject(gulp.src(config.tempDir + 'config.js'), { name: 'inject:config', read: false }))
            .pipe($.inject(gulp.src(config.tempDir + 'templates.js'), { name: 'inject:templates', read: false }))
            .pipe($.inject(gulp.src(config.tempDir + 'app.css')))
            .pipe(gulp.dest(config.tempDir));
    });
};
