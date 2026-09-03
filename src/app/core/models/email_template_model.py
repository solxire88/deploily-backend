# -*- coding: utf-8 -*-

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import Column, Integer, String, Text


class EmailTemplate(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)

    def __repr__(self):
        return self.key
