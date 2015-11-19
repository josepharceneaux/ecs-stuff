# GetTalent Dashboard
This app is the dashboard of GetTalent made using AngularJS.
This app has been built from [Angular Template](https://github.com/archfirst/angular-template)
This template provides a starter project that implements best practices in coding, building and testing AngularJS applications. Features include:
- A well-organized component hierarchy starting from `approot`. Components are implemented using directives (no dangling controllers). This provides a good architectural direction until Angular 2.0 becomes available.
- Follows AngularJS style guidelines (e.g. `controller as` syntax).
- Uses [AngularUI Router](https://github.com/angular-ui/ui-router) for flexible routing and nested views.
- Uses [Angular Bootstrap](http://angular-ui.github.io/bootstrap/) to remove dependencies on jQuery and Bootstrap’s JavaScript.
- Provides logging and exception handling frameworks with toaster notifications.
- Provides a Gulp based build system – code changes are reflected in the browser immediately.
- Uses Karma, Mocha and Chai for testing.
- Allows front-end development to proceed independently of the back-end by providing a mock server to serve an API and the sample data.

### Further Reading
Visit our [wiki](https://github.com/archfirst/angular-template/wiki) for detailed concepts and useful recipes for extending the template.

## Requirements

- Install Node
    - on OSX, install [home brew](http://brew.sh/) and type `brew install node`
    - on Windows, use the installer available at [nodejs.org](http://nodejs.org/)
    - On OSX you can alleviate the need to run as sudo by [following John Papa's instructions](http://jpapa.me/nomoresudo)
- Open terminal
- Type `npm install -g node-inspector bower gulp`

## Quick Start
Go to this directory and run the content locally:

    $ npm install
    $ bower install
    $ gulp serve-dev

- `npm install` will install the required node libraries under `node_modules` and then call `bower install` which will install the required client-side libraries under `bower_components`.
- `gulp serve-dev` will serve up the Angular application in a browser window. It is designed for an efficient development process. As you make changes to the code, the browser will update to reflect the changes immediately.

When you are ready to build the application for production, run the following command:

    $ gulp serve-build

This will build a production-ready package in the `/build` folder.

## Folder Structure

The folder structure is somewhat simplified and flatter compared to John Papa's [Gulp Patterns](https://github.com/johnpapa/gulp-patterns) project. The description below includes reasons for some of my customizations.

### Highest Level Structure

```
/bower_components
/build
/node_modules
/src
/test
```

- `bower_components:` Bower components downloaded by `bower install` (do not check in)

- `build:` Production build (do not check in)

- `node_modules:` Node.js modules downloaded by `npm install` (do not check in)

- `src:` contains all the client source files including HTML, styles (in SASS format), JavaScript and images

- `test:` contains client tests. This folder is intentionally kept separate from client source because I expect many different types of tests in this folder (unit, integration, acceptance). On real projects, the number of test files can be put aside the real source code file under /src.

### Source Folder Structure

```
/src
    /components
    /core
    /framework
    /images
    /app.module.js
    /app.scss
    /index.html
```

The `src` folder contains only the source for the AngularJS client application. It treats all 3 web technologies (HTML, CSS and JavaScript) as first class citizens and arranges them into logical modules. At the highest level you will find the main html, css (well, scss) and js files:

- `index.html`
- `app.scss`
- `app.module.js`

Below this level you will find various folders that arrange the application's functionality into logical modules.

- `framework:` Container for reusable services such as logging, exception handling, routing, security, local storage etc. These services are expected to work out-of-the-box without any changes for most applications. The template provides sample implementations for the first three. (This folder is called `blocks` in the gulp-patterns project.)

- `core:` Contains functionality that is shared across the application and will probably need customization for a specific application. This includes directives, filters and services and styles common to the entire application.

- `components:` Contains all the components of the application. We recommend thinking of an Angular application as a tree of components, starting with the `app` component as the root of this tree.

- `images:` Images used in the application.

## Tasks

### Task Listing

- `gulp help`

    Displays all of the available gulp tasks.

### App Config
- `gulp config`

    Builds environment constants using GT\_NODE\_ENV env variable
    Default environment is `development`.

        $ GT_NODE_ENV=development gulp config
        $ GT_NODE_ENV=production gulp config
        $ GT_NODE_ENV=local gulp config

    Running `gulp serve-dev` simply will run the app with development environment variable.
    Running `GT_NODE_ENV=production gulp serve-dev` will run the app with production environment variable.

### Code Analysis

- `gulp vet`

    Performs static code analysis on all javascript files. Runs jshint and jscs.

- `gulp vet --verbose`

    Displays all files affected and extended information about the code analysis.

- `gulp plato`

    Performs code analysis using plato on all javascript files. Plato generates a report in the reports folder.

### Testing

- `gulp serve-specs`

    Serves and browses to the spec runner html page and runs the unit tests in it. Injects any changes on the fly and re runs the tests. Quick and easy view of tests as an alternative to terminal via `gulp test`.

- `gulp test`

    Runs all unit tests using karma runner, mocha, chai and sinon with phantomjs. Depends on vet task, for code analysis.

- `gulp test --startServers`

    Runs all unit tests and midway tests. Cranks up a second node process to run a server for the midway tests to hit a web api.

- `gulp autotest`

    Runs a watch to run all unit tests.

- `gulp autotest --startServers`

    Runs a watch to run all unit tests and midway tests. Cranks up a second node process to run a server for the midway tests to hit a web api.

### Cleaning Up

- `gulp clean`

    Remove all files from the build and temp folders

- `gulp clean-images`

    Remove all images from the build folder

- `gulp clean-code`

    Remove all javascript and html from the build folder

- `gulp clean-fonts`

    Remove all fonts from the build folder

- `gulp clean-styles`

    Remove all styles from the build folder

### Fonts and Images

- `gulp fonts`

    Copy all fonts from source to the build folder

- `gulp images`

    Copy all images from source to the build folder

### Styles

- `gulp styles`

    Compile scss files to CSS, add vendor prefixes, and copy to the build folder

### Angular HTML Templates

- `gulp templatecache`

    Create an Angular module that adds all HTML templates to Angular's $templateCache. This pre-fetches all HTML templates saving XHR calls for the HTML.

- `gulp templatecache --verbose`

    Displays all files affected by the task.

### Serving Development Code

- `gulp serve-dev`

    Serves the development code and launches it in a browser. The goal of building for development is to do it as fast as possible, to keep development moving efficiently. This task serves all code from the source folders and compiles less to css in a temp folder.

- `gulp serve-dev --nosync`

    Serves the development code without launching the browser.

- `gulp serve-dev --debug`

    Launch debugger with node-inspector.

- `gulp serve-dev --debug-brk`

    Launch debugger and break on 1st line with node-inspector.

### Building Production Code

- `gulp optimize`

    Optimize all javascript and styles, move to a build folder, and inject them into the new index.html

- `gulp build`

    Copies all fonts, copies images and runs `gulp optimize` to build the production code to the build folder.

### Serving Production Code

- `gulp serve-build`

    Serve the optimized code from the build folder and launch it in a browser.

- `gulp serve-build --nosync`

    Serve the optimized code from the build folder and manually launch the browser.

- `gulp serve-build --debug`

    Launch debugger with node-inspector.

- `gulp serve-build --debug-brk`

    Launch debugger and break on 1st line with node-inspector.

## Credits
This template is heavily influenced by John Papa's [AngularJS Style Guide](https://github.com/johnpapa/angularjs-styleguide) and his [Gulp Patterns](https://github.com/johnpapa/gulp-patterns) project.
