# Copyright (C) 2019 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Hooks for creating sox notifications."""

from ggrc.models import all_models
from ggrc.services import signals

from ggrc.sox.notifications import utils


# pylint: disable=unused-argument, unused-variable, too-many-arguments
def init_hook():
  """Initializes hooks."""
  @signals.Restful.model_posted_after_commit.connect_via(all_models.Assessment)
  def handle_assessment_post(sender, obj=None, src=None, service=None,
                             event=None):
    """Handles assessment post event."""
    if obj.start_date and obj.sox_302_enabled:
      utils.create_sox_notifications(obj)

  @signals.Restful.model_put_before_commit.connect_via(all_models.Assessment)
  def handle_assessment_put(sender, obj=None, src=None, service=None,
                            event=None, initial_state=None):
    """Handle assessment put event."""
    if obj.start_date and obj.sox_302_enabled:
      if not initial_state.start_date or not initial_state.sox_302_enabled:
        utils.create_sox_notifications(obj)
      if initial_state.start_date and initial_state.sox_302_enabled:
        utils.update_sox_notifications(obj, initial_state)

    else:
      if initial_state.start_date and initial_state.sox_302_enabled:
        utils.remove_sox_notifications(obj)
