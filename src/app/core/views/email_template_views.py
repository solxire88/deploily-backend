# -*- coding: utf-8 -*-

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from markupsafe import Markup
from wtforms import TextAreaField
from wtforms.widgets import TextArea

from app import appbuilder, db
from app.core.models.email_template_model import EmailTemplate


class QuillWidget(TextArea):
    # Quill edits a <div>, not the <textarea> — hide the textarea (it stays the
    # real form field WTForms reads), mount Quill on a sibling div seeded with
    # the textarea's current value, and sync Quill's HTML back into the
    # textarea on form submit so FAB/WTForms sees it like any normal field.
    def __call__(self, field, **kwargs):
        kwargs.setdefault("style", "display:none;")
        textarea_html = super().__call__(field, **kwargs)

        editor_id = f"quill-editor-{field.id}"
        widget_html = Markup(
            f'<div id="{editor_id}" style="height:300px;background:#fff;"></div>'
            '<link href="https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.snow.css" rel="stylesheet">'
            '<script src="https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.js"></script>'
            "<script>"
            "(function () {"
            f'  var textarea = document.getElementById("{field.id}");'
            f'  var quill = new Quill("#{editor_id}", {{ theme: "snow" }});'
            "  quill.clipboard.dangerouslyPasteHTML(textarea.value);"
            "  var form = textarea.closest('form');"
            "  if (form) {"
            "    form.addEventListener('submit', function () {"
            "      textarea.value = quill.root.innerHTML;"
            "    });"
            "  }"
            "})();"
            "</script>"
        )
        return textarea_html + widget_html


class EmailTemplateModelView(ModelView):
    route_base = "/admin/email-template"
    datamodel = SQLAInterface(EmailTemplate)
    list_columns = ["key", "subject", "changed_by", "changed_on"]
    add_columns = ["key", "subject", "body"]
    edit_columns = ["subject", "body"]
    base_order = ("key", "asc")

    edit_form_extra_fields = {
        "body": TextAreaField("body", widget=QuillWidget())
    }
    add_form_extra_fields = {
        "body": TextAreaField("body", widget=QuillWidget())
    }


db.create_all()
appbuilder.add_view(
    EmailTemplateModelView,
    "Email Templates",
    icon="fa-solid fa-envelope-open-text",
    category="Configuration",
)
