var gulp = require('gulp');

module.exports = function (config) {
    config.log('Importing assets.js...');

    gulp.task('fonts', ['clean-fonts', 'build-icon-font'], function () {
        config.log('Copying fonts');

        return gulp
            .src(config.fonts)
            .pipe(gulp.dest(config.buildDir + 'fonts'));
    });

    gulp.task('images', ['clean-images'], function () {
        config.log('Compressing and copying images');

        return gulp
            .src(config.sourceDir + 'images/**/*.*')
            .pipe(config.$.imagemin({
                optimizationLevel: 4
            }))
            .pipe(gulp.dest(config.buildDir + 'images'));
    });
};
