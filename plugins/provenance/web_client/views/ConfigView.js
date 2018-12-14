import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import View from 'girder/views/View';
import events from 'girder/events';
import { restRequest } from 'girder/rest';

import ConfigViewTemplate from '../templates/configView.pug';

var ConfigView = View.extend({
    events: {
        'submit #g-provenance-form': function (event) {
            event.preventDefault();
            this.$('#g-provenance-error-message').empty();

            this._saveSettings([{
                key: 'provenance.resources',
                value: this.$('#g-provenance-resources').val().trim()
            }]);
        }
    },
    initialize: function () {
        restRequest({
            method: 'GET',
            url: 'system/setting',
            data: {
                list: JSON.stringify(['provenance.resources'])
            }
        }).done((resp) => {
            this.render();
            this.$('#g-provenance-resources').val(
                resp['provenance.resources']
            );
        });
    },

    render: function () {
        this.$el.html(ConfigViewTemplate());

        if (!this.breadcrumb) {
            this.breadcrumb = new PluginConfigBreadcrumbWidget({
                pluginName: 'Provenance tracker',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }

        return this;
    },

    _saveSettings: function (settings) {
        restRequest({
            method: 'PUT',
            url: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(() => {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }).fail((resp) => {
            this.$('#g-provenance-error-message').text(
                resp.responseJSON.message
            );
        });
    }
});

export default ConfigView;
