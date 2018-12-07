import * as auth from './auth';
import * as collections from './collections';
import * as constants from './constants';
import * as dialog from './dialog';
import * as misc from './misc';
import * as models from './models';
import * as rest from './rest';
import * as server from './server';
import * as utilities from './utilities';
import * as version from './version';
import * as views from './views';
import events from './events';
import router from './router';

// This will be modified dynamically when plugins are loaded.
var plugins = {};

export {
    auth,
    collections,
    constants,
    dialog,
    events,
    misc,
    models,
    plugins,
    rest,
    router,
    server,
    utilities,
    version,
    views
};
