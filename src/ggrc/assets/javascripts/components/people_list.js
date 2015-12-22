/*!
  Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
  Created By: andraz@reciprocitylabs.com
  Maintained By: andraz@reciprocitylabs.com
*/

(function (can) {
  can.Component.extend({
    tag: "people-list",
    template: can.view(GGRC.mustache_path + "/base_templates/people_list.mustache"),
    scope: {
      editable: "@",
      deferred: "@",
      validate: "@"
    }
  });

  can.Component.extend({
    tag: "people-group",
    template: can.view(GGRC.mustache_path + "/base_templates/people_group.mustache"),
    scope: {
      limit: "@",
      mapping: "@",
      required: "@",
      type: "@",
      toggle_add: false,
      mapped_people: [],
      results: [],
      list_pending: [],
      list_mapped: [],
      get_pending: function () {
        if (!this.attr("deferred")) {
          return [];
        }
        if (!this.attr("instance._pending_joins")) {
          this.attr("instance._pending_joins", []);
        }
        return this.attr("instance._pending_joins");
      },
      get_mapped: function () {
        return this.attr("instance").get_mapping(this.attr("mapping"));
      },
      remove_role: function (parent_scope, el, ev) {
        var person = CMS.Models.Person.findInCacheById(el.data("person")),
            rel = function (obj) {
              return _.map(_.union(obj.related_sources, obj.related_destinations), function (r) {
                return r.id;
              });
            },
            instance = this.instance,
            ids = _.intersection(rel(person), rel(this.instance)),
            type = this.attr("type");

        if (!ids.length && this.attr("deferred")) {
          var list = this.attr("list_pending")
              index = _.findIndex(list, function (item) {
                return item.what.type === "Person" &&
                       item.how === "add" &&
                       item.what.id === person.id;
              });

          return list.splice(index, 1);
        }
        _.each(ids, function (id) {
          var rel = CMS.Models.Relationship.findInCacheById(id);
          if (rel.attrs && rel.attrs.AssigneeType) {
            rel.refresh().then(function (rel) {
              var roles = rel.attrs.AssigneeType.split(",");
              roles = _.filter(roles, function (role) {
                return role && (role.toLowerCase() !== type);
              });
              if (this.attr("deferred") === "true") {
                el.closest("li").remove();
                if (roles.length) {
                  instance.mark_for_deletion("related_objects_as_destination", person);
                } else {
                  instance.mark_for_change("related_objects_as_destination", person, {
                    attrs: {
                      "AssigneeType": roles.join(",")
                    }
                  });
                }
              } else {
                if (roles.length) {
                  rel.attrs.attr("AssigneeType", roles.join(","));
                  rel.save();
                } else {
                  rel.destroy();
                }
              }
            }.bind(this));
          }
        }, this);
      },
    },
    events: {
      "inserted": function () {
        this.scope.attr("list_pending", this.scope.get_pending());
        this.scope.attr("list_mapped", this.scope.get_mapped());
        this.updateResult();
        if (!this.scope.attr("required")) {
          return;
        }
        this.scope.attr("mapped_people", this.scope.get_mapped());
        if (this.scope.instance.isNew() && this.scope.validate) {
          this.validate();
        }
      },
      "validate": function () {
        if (!(this.scope.required && this.scope.validate)) {
          return;
        }
        this.scope.attr("instance").attr("validate_" + this.scope.attr("type"), !!this.scope.results.length);
      },
      "updateResult": function () {
        var type = this.scope.type,
            mapped = _.map(this.scope.get_mapped(), function (item) {
              return item.instance;
            }),
            pending = _.filter(this.scope.get_pending(), function (item) {
              return item.what.type === "Person";
            }),
            added = _.map(_.filter(pending, function (item) {
                var roles = can.getObject("extra.attrs", item);
                return item.how === "add" &&
                  (roles && _.contains(roles.AssigneeType.split(","), can.capitalize(type)));
              }), function (item) {
                return item.what;
              }),
            removed = _.map(_.filter(pending, function (item) {
                return item.how === "remove" && _.find(mapped, function (map) {
                    return map.id === item.what.id;
                  });
              }),function (item) {
                return item.what;
              });

        this.scope.attr("results").replace(_.union(_.filter(mapped, function (item) {
          return !_.findWhere(removed, {id: item.id});
        }), added));
      },
      "{scope.list_mapped} change": "updateResult",
      "{scope.list_pending} change": "updateResult",
      "{scope.results} change": "validate",
      "{scope.instance} modal:dismiss": function () {
        this.scope.attr("instance").removeAttr("validate_" + this.scope.attr("type"));
      },
      ".person-selector input autocomplete:select": function (el, ev, ui) {
        var person = ui.item,
            role = can.capitalize(this.scope.type),
            instance = this.scope.attr("instance"),
            list_pending = this.scope.attr("list_pending"),
            deferred = this.scope.attr("deferred"),
            pending, model;

        if (deferred) {
          pending = true;
          if (list_pending) {
            _.each(list_pending, function (join) {
              if (join.what === person && join.how === "add") {
                var existing= join.extra.attr("attrs.AssigneeType") || "";
                existing = _.filter(existing.split(","));
                var roles = _.union(existing, [role]).join(",");
                join.extra.attr("attrs.AssigneeType", roles);
                pending = false;
              }
            });
          }
          if (pending) {
            instance.mark_for_addition("related_objects_as_destination", person, {
              attrs: {
                "AssigneeType": role,
              },
              context: instance.context,
            });
          }
        } else {
          model = CMS.Models.Relationship.get_relationship(person, instance);
          if (!model) {
            model = new CMS.Models.Relationship({
              attrs: {
                "AssigneeType": role,
              },
              source: {
                href: person.href,
                type: person.type,
                id: person.id
              },
              context: instance.context,
              destination: {
                href: instance.href,
                type: instance.type,
                id: instance.id
              }
            });
            model = $.Deferred().resolve(model);
          } else {
            model = model.refresh();
          }

          model.then(function (model) {
            var type = model.attr("attrs.AssigneeType");
            model.attr("attrs.AssigneeType", role + (type ? "," + type : ""));
            model.save();
          }.bind(this));
        }
      },
    },
    helpers: {
      can_unmap: function (options) {
        var results = this.attr("results"),
            required = this.attr("required");

        if (required) {
          if (results.length > 1) {
            return options.fn(options.context);
          }
          return options.inverse(options.context);
        }
        return options.fn(options.context);
      },
      show_add: function (options) {
        if (this.attr("editable") === "true") {
          return options.fn(options.context);
        }
        return options.inverse(options.context);
      },
      if_has_role: function (roles, role, options) {
        roles = Mustache.resolve(roles) || "";
        role = Mustache.resolve(role) || "";
        roles = _.filter(roles.toLowerCase().split(","));
        role = role.toLowerCase();
        return options[_.includes(roles, role) ? "fn" : "inverse"](options.contexts);
      },
    }
  });
})(window.can);
