# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for custom attribute definitions model."""

from sqlalchemy.exc import IntegrityError

from ggrc import db
from ggrc import models
from ggrc.app import app
from integration.ggrc import TestCase
from integration.ggrc.models import factories

CAD = factories.CustomAttributeDefinitionFactory


class TestCAD(TestCase):
  """Tests for basic functionality of cad model."""

  def test_setting_reserved_words(self):
    """Test setting any of the existing attribute names."""

    with self.assertRaises(ValueError):
      cad = models.CustomAttributeDefinition()
      cad.definition_type = "section"
      cad.title = "title"

    with self.assertRaises(ValueError):
      cad = models.CustomAttributeDefinition()
      cad.title = "title"
      cad.definition_type = "section"

    with self.assertRaises(ValueError):
      models.CustomAttributeDefinition(
          title="title",
          definition_type="Assessment",
      )

    with self.assertRaises(ValueError):
      models.CustomAttributeDefinition(
          title="TITLE",
          definition_type="program",
      )

    with self.assertRaises(ValueError):
      models.CustomAttributeDefinition(
          title="Secondary CONTACT",
          definition_type="program",
      )

    cad = models.CustomAttributeDefinition(
        title="non existing title",
        definition_type="program",
    )
    self.assertEqual(cad.title, "non existing title")

  def test_setting_global_cad_names(self):
    """Test duplicates with global attribute names."""

    db.session.add(models.CustomAttributeDefinition(
        title="global cad",
        definition_type="section",
        attribute_type="Text",
    ))
    db.session.add(models.CustomAttributeDefinition(
        title="non existing title",
        definition_type="section",
        definition_id=1,
        attribute_type="Text",
    ))
    db.session.add(models.CustomAttributeDefinition(
        title="non existing title",
        definition_type="section",
        definition_id=2,
        attribute_type="Text",
    ))
    db.session.commit()

    with self.assertRaises(IntegrityError):
      db.session.add(models.CustomAttributeDefinition(
          title="non existing title",
          definition_type="section",
          definition_id=2,
          attribute_type="Text",
      ))
      db.session.commit()
    db.session.rollback()

    with self.assertRaises(ValueError):
      db.session.add(models.CustomAttributeDefinition(
          title="global cad",
          definition_type="section",
          definition_id=2,
          attribute_type="Text",
      ))
      db.session.commit()

  def test_different_models(self):
    """Test unique names over on different models."""
    db.session.add(models.CustomAttributeDefinition(
        title="my custom attribute title",
        definition_type="section",
        attribute_type="Text",
    ))
    db.session.commit()
    cad = models.CustomAttributeDefinition(
        title="my custom attribute title",
        definition_type="program",
        attribute_type="Text",
    )
    self.assertEqual(cad.title, "my custom attribute title")

  def test_setting_same_name(self):
    """Setting an already existing title should pass the validator."""

    db.session.add(models.CustomAttributeDefinition(
        title="my custom attribute title",
        definition_type="section",
        attribute_type="Text",
    ))
    db.session.commit()
    cad = models.CustomAttributeDefinition.query.first()
    cad.title = "my custom attribute title"
    cad.attribute_type = "Rich Text"
    db.session.commit()
    cad = models.CustomAttributeDefinition.query.first()
    self.assertEqual(cad.title, "my custom attribute title")
    self.assertEqual(cad.attribute_type, "Rich Text")

  def test_assessment(self):
    """Test collisions between assessment template and assessments.

    Assessment template is not allowed to have local CAD that match Assessment
    global CAD, because that will cause collisions when assessments are
    generated when using the mentioned template.
    """
    with app.app_context():
      CAD(
          title="assessment CAD",
          definition_type="assessment_template",
          definition_id=1,
      )

    with app.app_context():
      # check that local assessment local CAD can match AT CAD.
      CAD(
          title="assessment CAD",
          definition_type="assessment",
          definition_id=1,
      )
    with app.app_context():
      with self.assertRaises(ValueError):
        CAD(
            title="assessment CAD",
            definition_type="assessment",
        )

  def test_assessment_template(self):
    """Test collisions between assessment template and assessments.

    Assessment template is not allowed to have local CAD that match Assessment
    global CAD, because that will cause collisions when assessments are
    generated when using the mentioned template.
    """
    with app.app_context():
      CAD(
          title="global title",
          definition_type="assessment",
      )
      CAD(
          title="local title",
          definition_type="assessment",
          definition_id=1,
      )
    with app.app_context():
      # check that assessment template CAD can match an assessment local CAD.
      CAD(
          title="local title",
          definition_type="assessment_template",
          definition_id=1,
      )
    with app.app_context():
      with self.assertRaises(ValueError):
        CAD(
            title="global title",
            definition_type="assessment_template",
            definition_id=1,
        )
