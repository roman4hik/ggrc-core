/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  GGRC.Components('snapshotLoaderItem', {
    tag: 'snapshot-loader-item',
    template: can.view(
      GGRC.mustache_path +
      '/components/snapshot-loader/snapshot-loader-item.mustache'
    ),
    viewModel: {
      itemData: {},
      objectType: '@',
      title: function () {
        return this.attr('itemData.title') ||
          this.attr('itemData.description_inline') ||
          this.attr('itemData.name') || this.attr('itemData.email');
      },
      objectTypeIcon: function () {
        return 'fa-' + this.attr('objectType').toLowerCase();
      },
      toggleIconCls: function () {
        return this.attr('showDetails') ? 'fa-caret-down' : 'fa-caret-right';
      },
      toggleDetails: function () {
        this.attr('showDetails', !this.attr('showDetails'));
      }
    }
  });
})(window.can, window.GGRC);
