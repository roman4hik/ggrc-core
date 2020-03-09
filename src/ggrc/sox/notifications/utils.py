# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Helper functions for working with sox notifications"""

from datetime import datetime

from ggrc import db
from ggrc.login import get_current_user_id
from ggrc.models import all_models
from ggrc.sox.notifications import notification_types as notif_types


def create_sox_notification(obj, notification_type, send_on):
  """Create notification.

    Args:
      obj: Object instance.;
      notification_type: name of notification type from notification_type
                         table;
      send_on: date for sending notification;
  """
  notif_type_id = all_models.NotificationType.query.filter_by(
      name=notification_type).one().id
  repeating = notification_type == \
      notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value

  db.session.add(all_models.Notification(
      object=obj,
      send_on=send_on,
      notification_type_id=notif_type_id,
      modified_by_id=get_current_user_id(),
      repeating=repeating
  ))


def get_notification_types(*names):
  """Get notifications types by name."""
  return all_models.NotificationType.query.filter(
      all_models.NotificationType.name.in_(names)
  ).all()


def create_sox_notifications(obj):
  """Create sox notifications all types for assessment. """
  due_date = obj.start_date
  today = datetime.utcnow().date()
  for notif_type in notif_types.SoxNotificationTypes:
    send_on = due_date + notif_type.timedelta
    if (
        send_on > today or
        notif_type == notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION
    ):
      create_sox_notification(obj, notif_type.value, send_on)


def remove_sox_notifications(obj):
  """Remove all sox notifications relate with assessment."""
  notif_type_names = [
      notif.value for notif in notif_types.SoxNotificationTypes
  ]
  notif_type_ids = [
      i.id for i in get_notification_types(*notif_type_names)
  ]

  all_models.Notification.query.filter(
      all_models.Notification.object_id == obj.id,
      all_models.Notification.object_type == obj.type,
      all_models.Notification.notification_type_id.in_(notif_type_ids)
  ).delete(synchronize_session='fetch')


def update_sox_notifications(obj, initial_state):
  """Update sox notification relate with assessment."""
  if obj.start_date != initial_state.start_date:
    remove_sox_notifications(obj)
    create_sox_notifications(obj)
