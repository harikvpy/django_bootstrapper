const { series, parallel, src, dest } = require('gulp');
const uglify = require('gulp-uglify');
const rename = require('gulp-rename');
const gulpif = require('gulp-if');
const del = require('del');
const concat = require('gulp-concat');
const strip = require('gulp-strip-comments')
const exec = require('child_process').exec;
const cleanCSS = require('gulp-clean-css');
const processhtml = require('gulp-processhtml');
const fs = require('fs');
const bump = require('gulp-bump');
const PluginError = require('plugin-error');
const git = require('gulp-git');
const dateTime = require('date-time');

const PROJECT = '{{cookiecutter.app_name}}'

/* Test task to run a command */
function childProcessTask(cb) {
  exec(`python ./${PROJECT}/manage.py`, function(err, stdout, stderr) {
    console.log(stdout);
    console.log(stderr);
    cb(err);
  });
}

function getPackageJsonVersion () {
  // We parse the json file instead of using require because require caches
  // multiple calls so the version number won't be updated
  return JSON.parse(fs.readFileSync('./package.json', 'utf8')).version;
};

/* Cleans up the dist folder */
function clean() {
  return del('dist/');
}

/*
 * Returns a boolean indicating if the supplied javascript file is not minified.
 * Uses the filenaming convention of using .min.js to determine this.
 */
function isUnminifiedJavascript(file) {
  return file.extname === '.js' && !file.basename.endsWith('.min.js');
}

/*
 * Returns TRUE if the stream being processed belongs to file
 * 'public/templates/templates/public/home_page.html'
 */
function isHTML(file) {
  return file.extname === '.html';
}

function isCSS(file) {
  return file.extname === '.css';
}

function doBuild(cb) {
  let pkg = JSON.parse(fs.readFileSync('./package.json'));
  console.log('Version: ' + pkg.version);
  return src([
      'src/**/*',
      '!src/**/__pycache__',
      '!src/**/*.pyc',
      '!src/**/*.log',
      '!src/*.sqlite3',
    ], { base: 'src' })
    .pipe(gulpif(isHTML, processhtml({
      data: {
        siteVersion: pkg.version,
        buildTime: dateTime()
      }
    })))
    .pipe(gulpif(isCSS, cleanCSS({rebase: false})))
    .pipe(gulpif(isUnminifiedJavascript, uglify()))
    .pipe(gulpif(isUnminifiedJavascript, rename({ extname: '.min.js' })))
    .pipe(dest('dist'));
}

/**
 * Bump package version number. The version quadrant incremented
 * depends on the build type (buildOptions.type).
 */
function bumpVersion(cb) {
  return src('./package.json')
    .pipe(bump({type: buildOptions.release}))
    .pipe(dest('./'));
}

/**
 * Commit all changes made to the Git repo.
 *
 * @param {*} cb Gulp task completion callback
 */
function commitChanges(cb) {
  return src('.')
    .pipe(git.add())
    .pipe(git.commit('Post-release build commit'));
}

/**
 * Push repo changes to 'origin' remote.
 * 
 * @param {*} done Gulp task completion callback.
 */
function pushChange(done) {
  git.push('origin', 'master', done);
}

/**
 * Create release tag.
 * 
 * @param {*} done Gulp task completion callback.
 */
function createGitTag(done) {
  var version = getPackageJsonVersion();
  git.tag(version, 'Relase Version: ' + version, function (error) {
    if (error) {
      return done(error);
    }
    //git.push('origin', 'master', {args: '--tags'}, done);
  });

}

/**
 * Write version.txt with the current version read from package.json
 * to dist/version.txt
 * 
 * @param {*} done Gulp task completion callback.
 */
function emitVersion(cb) {
  var version = getPackageJsonVersion();
  fs.writeFile('dist/version.txt', version, cb);
}

/*
 * PROCESS SCRIPT COMMAND LINE ARGUMENTS
 *
 * Command supports the following command line options:
 * 
 *  --type {[stage]|release}
 *    Type of release. If release type is set to 'stage', integrated
 *    git commit/tag operation won't be carried out.
 * 
 *  --release {major|minor|[patch]}
 *    The type of release. This determines which version quadrant is incremented
 *    for 'release' build types.
 * 
 *  --tests {yes|[no]}
 *    Whether to execute the package tests before going on to build.
 */

// Default build options
let DEFAULT_BUILD_OPTIONS = {
  type: 'stage',    // {stage|release}
  release: 'patch', // {major|minor|patch}
  tests: 'no'       // {yes|no}
};

// fetch command line arguments
let userBuildOptions = (argList => {

  let arg = {}, a, opt, thisOpt, curOpt;
  for (a = 0; a < argList.length; a++) {

    thisOpt = argList[a].trim();
    opt = thisOpt.replace(/^\-+/, '');

    if (opt === thisOpt) {
      // argument value
      if (curOpt) arg[curOpt] = opt;
      curOpt = null;
    } else {
      // argument name
      curOpt = opt;
      arg[curOpt] = true;
    }
  }
  return arg;
})(process.argv);

const buildOptions = Object.assign({}, DEFAULT_BUILD_OPTIONS, userBuildOptions);

// Verify build option values

// build type
if (['stage', 'release'].indexOf(buildOptions.type) < 0) {
  throw new PluginError('params', 'Invalid value specified for "type" parameter. Valid values are {stage|release}');
}

// release type
if (['major', 'minor', 'patch'].indexOf(buildOptions.release) < 0) {
  throw new PluginError('params', 'Invalid value specified for "release" parameter. Valid values are {major|minor|patch}');
}

// tests
if (['yes', 'no'].indexOf(buildOptions.tests) < 0) {
  throw new PluginError('params', 'Invalid value specified for "tests" parameter. Valid values are {yes|no}.');
}

/**
 * Release build type tasks
 */
function emptyTask(cb) {
  cb();
}

function releaseTasks(cb) {
  if (buildOptions.type == 'release') {
    bumpVersion(cb);
    commitChanges(cb);
    createGitTag(cb);  
  } else {
    console.log('Skipping git operations for non-release build')
  }
  cb();
}

/**
 * EXPORTED tasks
 */

// Clean the dist/ folder
exports.clean = clean;

// Build/bump-version/commit code -- all in one
exports.default = series(
  clean,
  doBuild,
  emitVersion,
  releaseTasks
  );
