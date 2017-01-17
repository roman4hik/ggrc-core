/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.datepicker', function () {
  'use strict';

  var Component;  // the component under test

  beforeAll(function () {
    Component = GGRC.Components.get('datepicker');
  });

  describe('updateDate() method', function () {
    var method;
    var scope;

    beforeAll(function () {
      scope = new can.Map({
        scope: {
          picker: {
            datepicker: jasmine.createSpy()
          }
        }
      });
      method = Component.prototype.events.updateDate.bind(scope);
    });

    it('returns undefined for empty date', function () {
      expect(method('maxDate')).toBe(null);
      expect(method('maxDate', null)).toBe(null);
      expect(method('minDate', '')).toBe(null);
    });

    it('returns a date incremented by a day for maxDate', function () {
      var result = method('maxDate', new Date(2017, 0, 1));

      expect(result.getDate()).toBe(31);
      expect(result.getFullYear()).toBe(2016);
      expect(result.getMonth()).toBe(11);
    });

    it('returns a date decremented by a day for minDate', function () {
      var result = method('minDate', new Date(2017, 0, 1));

      expect(result.getDate()).toBe(2);
      expect(result.getFullYear()).toBe(2017);
      expect(result.getMonth()).toBe(0);
    });
  });
});
