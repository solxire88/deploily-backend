# -*- coding: utf-8 -*-

from datetime import datetime

from flask_appbuilder import Model
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text


class Mail(Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    body = Column(Text)
    mail_state = Column(Enum("outGoing", "sent", "error", "canceled", name="mail_state"))
    email_from = Column(String(255), default="")
    email_to = Column(String(255), default="")
    reply_to = Column(String(255), nullable=True)
    created_on = Column(DateTime, default=lambda: datetime.now(), nullable=True)

    def __repr__(self):
        return str(self.id)
