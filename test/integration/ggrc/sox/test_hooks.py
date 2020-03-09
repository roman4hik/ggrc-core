# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for sox notifications hooks."""

from datetime import datetime, timedelta
import ddt

from ggrc import db
from ggrc.models import all_models
from ggrc.sox.notifications import notification_types as notif_types
from integration.ggrc import api_helper
from integration.ggrc.models import factories
from integration.ggrc import TestCase


@ddt.ddt
class TesSoxNotificationHook(TestCase):
  """Test checks hooks for sox notifications"""

  def setUp(self):
    super(TesSoxNotificationHook, self).setUp()
    self.client.get("/login")
    self.api = api_helper.Api()

  @ddt.data(
      {"date_offset": 0, "expected_result": 2},
      {"date_offset": 1, "expected_result": 3},
      {"date_offset": 3, "expected_result": 4},
      {"date_offset": 4, "expected_result": 5},
      {"date_offset": 8, "expected_result": 6},
  )
  @ddt.unpack
  def test_create_sox_notif(self, date_offset, expected_result):
    """Test checks generate sox notif after creating asmt."""
    with factories.single_commit():
      audit = factories.AuditFactory()
      asmt_tmpl = factories.AssessmentTemplateFactory(
          audit=audit,
          sox_302_enabled=True,
      )
    today = datetime.utcnow().date()
    send_on = today + timedelta(days=date_offset)
    self.api.post(
        all_models.Assessment,
        {
            "assessment": {
                "audit": {"id": audit.id},
                "template": {"id": asmt_tmpl.id},
                "title": "Assessment Title",
                "sox_302_enabled": True,
                "start_date": send_on
            },
        },
    )
    notif_count = len(db.session.query(all_models.Notification).all())
    self.assertEqual(notif_count, expected_result)

  @ddt.data(
      {
          "start_date": datetime.today() + timedelta(days=10),
          "sox_302_enabled": False
      },
      {"start_date": None, "sox_302_enabled": True},
      {"start_date": None, "sox_302_enabled": False},
  )
  @ddt.unpack
  def test_not_create_sox_notif(self, start_date, sox_302_enabled):
    """Test checks not creating sox notif."""
    with factories.single_commit():
      audit = factories.AuditFactory()
      asmt_tmpl = factories.AssessmentTemplateFactory(
          audit=audit,
          sox_302_enabled=sox_302_enabled,
      )
    self.api.post(
        all_models.Assessment,
        {
            "assessment": {
                "audit": {"id": audit.id},
                "template": {"id": asmt_tmpl.id},
                "title": "Assessment Title",
                "sox_302_enabled": sox_302_enabled,
                "start_date": start_date
            },
        },
    )
    notif_count = len(db.session.query(all_models.Notification).all())
    self.assertEqual(notif_count, 1)

  @ddt.data(
      {
          "date_offset": 0,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
          ],
          "expected_count": 1
      },
      {
          "date_offset": 1,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value
          ],
          "expected_count": 2
      },
      {
          "date_offset": 3,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_1_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value,
          ],
          "expected_count": 3
      },
      {
          "date_offset": 4,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_1_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_3_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value,
          ],
          "expected_count": 4
      },
      {
          "date_offset": 8,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_1_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_3_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_7_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value,
          ],
          "expected_count": 5
      },
  )
  @ddt.unpack
  def test_create_correct_sox_notif(self,
                                    date_offset,
                                    expected_types,
                                    expected_count):
    """Test checks correct creating sox notifications by type."""
    with factories.single_commit():
      audit = factories.AuditFactory()
      asmt_tmpl = factories.AssessmentTemplateFactory(
          audit=audit,
          sox_302_enabled=True,
      )
    today = datetime.utcnow().date()
    send_on = today + timedelta(days=date_offset)
    self.api.post(
        all_models.Assessment,
        {
            "assessment": {
                "audit": {"id": audit.id},
                "template": {"id": asmt_tmpl.id},
                "title": "Assessment Title",
                "sox_302_enabled": True,
                "start_date": send_on
            },
        },
    )

    sox_notifs = [nt.value for nt in notif_types.SoxNotificationTypes]
    created_sox_notifs = db.session.query(
        all_models.NotificationType.name,
    ).join(
        all_models.Notification,
    ).filter(
        all_models.NotificationType.name.in_(sox_notifs),
    ).order_by('name').all()

    self.assertEqual(len(created_sox_notifs), expected_count)
    self.assertListEqual(
        [name for name, in created_sox_notifs],
        expected_types,
    )

  @staticmethod
  def _create_sox_notifications(obj, sox_notif_types):
    """Create sox notifications."""

    due_date = obj.start_date
    created_notif_ids = []

    sox_notif_types = db.session.query(
        all_models.NotificationType.id,
        all_models.NotificationType.name,
    ).filter(
        all_models.NotificationType.name.in_(
            [nt.value for nt in sox_notif_types]
        ),
    )

    for notif_id, notif_type_name in sox_notif_types:
      notif = factories.NotificationFactory(
          object=obj,
          notification_type_id=notif_id,
          send_on=(
              notif_types.SoxNotificationTypes(
                  notif_type_name
              ).timedelta + due_date
          )
      )
      created_notif_ids.append(notif.id)

    return created_notif_ids

  def test_delete_sox_notif(self):
    """Test checks deleting all sox notif after deleting asmt."""
    with factories.single_commit():
      audit = factories.AuditFactory()
      today = datetime.utcnow().date()
      start_date = today + timedelta(days=8)
      asmt = factories.AssessmentFactory(
          audit=audit,
          sox_302_enabled=True,
          start_date=start_date
      )
      self._create_sox_notifications(asmt,
                                     notif_types.SoxNotificationTypes)

    asmt_id = all_models.Assessment.query.first()
    self.api.delete(asmt_id)

    notif_count = len(db.session.query(all_models.Notification).all())
    self.assertEqual(notif_count, 0)

  @ddt.data(
      {
          "date_offset": 0,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
          ],
          "expected_count": 1
      },
      {
          "date_offset": 1,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value
          ],
          "expected_count": 2
      },
      {
          "date_offset": 3,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_1_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value,
          ],
          "expected_count": 3
      },
      {
          "date_offset": 4,
          "expected_types": [
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_1_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_BEFORE_3_DAY.value,
              notif_types.SoxNotificationTypes.DUE_DATE_EXPIRATION.value,
              notif_types.SoxNotificationTypes.DUE_DATE_TODAY.value,
          ],
          "expected_count": 4
      },
  )
  @ddt.unpack
  def test_update_notif_after_update(self,
                                     date_offset,
                                     expected_types,
                                     expected_count):
    """Test checks updating all sox notif relate with asmt."""

    today = datetime.utcnow().date()
    initial_data = today + timedelta(days=10)

    with factories.single_commit():
      audit = factories.AuditFactory()
      asmt = factories.AssessmentFactory(
          audit=audit,
          sox_302_enabled=True,
          start_date=initial_data
      )
      self._create_sox_notifications(
          asmt,
          notif_types.SoxNotificationTypes
      )

    new_start_date = today + timedelta(days=date_offset)
    self.api.put(asmt, {"start_date": new_start_date})

    created_sox_notifs = db.session.query(
        all_models.NotificationType.name,
    ).join(
        all_models.Notification,
    ).filter(
        all_models.NotificationType.name.in_(expected_types),
    ).order_by('name').all()

    self.assertEqual(len(created_sox_notifs), expected_count)
    self.assertListEqual(
        [name[0] for name in created_sox_notifs],
        expected_types,
    )

  def test_remove_notit_after_update(self):
    """Test checks deleting notifs if we reset start_date."""

    with factories.single_commit():
      audit = factories.AuditFactory()
      today = datetime.utcnow().date()
      start_date = today + timedelta(days=8)
      asmt = factories.AssessmentFactory(
          audit=audit,
          sox_302_enabled=True,
          start_date=start_date
      )
      self._create_sox_notifications(asmt,
                                     notif_types.SoxNotificationTypes)

    self.api.put(asmt, {"start_date": None})

    sox_notifs = [nt.value for nt in notif_types.SoxNotificationTypes]
    sox_notif_count = len(db.session.query(
        all_models.NotificationType.name,
    ).join(
        all_models.Notification,
    ).filter(
        all_models.NotificationType.name.in_(sox_notifs),
    ).all())
    self.assertEqual(sox_notif_count, 0)

  def test_create_notif_after_update(self):
    """Test checks creating notifs if we set start_date."""

    with factories.single_commit():
      audit = factories.AuditFactory()
      asmt = factories.AssessmentFactory(
          audit=audit,
          sox_302_enabled=True,
      )

    today = datetime.utcnow().date()
    start_date = today + timedelta(days=8)
    self.api.put(asmt, {"start_date": start_date})

    sox_notifs = [nt.value for nt in notif_types.SoxNotificationTypes]
    sox_notif_count = len(db.session.query(
        all_models.NotificationType.name,
    ).join(
        all_models.Notification,
    ).filter(
        all_models.NotificationType.name.in_(sox_notifs),
    ).all())
    self.assertEqual(sox_notif_count, 5)
