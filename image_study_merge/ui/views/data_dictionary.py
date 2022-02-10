from itertools import groupby
import re
from flask import flash, redirect, render_template, url_for
from image_study_merge.model import DataDictionary, FileUploadDirectory
from lbrc_flask.forms import FlashingForm, FileField, ConfirmForm
from flask_wtf.file import FileRequired
from werkzeug.utils import secure_filename
from .. import blueprint
from datetime import datetime
from lbrc_flask.column_data import CsvData
from lbrc_flask.database import db
from lbrc_flask.security import must_be_admin


class UploadDataDictionaryForm(FlashingForm):
    upload = FileField(
        'Data Dictionary File',
        accept=['.csv'],
        validators=[FileRequired()]
    )


@blueprint.route("/data_dictionary/<string:form_name>")
@blueprint.route("/data_dictionary")
def data_dictionary(form_name=None):
    forms = {f[0]: re.sub(r"[-_]", " ", f[0]).title() for f in DataDictionary.query
        .with_entities(DataDictionary.form_name.distinct())
        .all()
    }

    if not form_name and forms:
        form_name = list(forms.keys())[0]

    data_dictionary = (DataDictionary.query
        .filter(DataDictionary.form_name == form_name)
        .order_by(DataDictionary.field_number)
        .all()
    )

    sections = {}

    for section_name, fields in groupby(data_dictionary, key= lambda f: f.section_name):
        sections[section_name] = list(fields)

    return render_template(
        "ui/data_dictionary/index.html",
        forms=forms,
        sections=sections,
        confirm_form=ConfirmForm(),
        form_name=form_name,
    )


@blueprint.route("/data_dictionary/upload", methods=['GET', 'POST'])
@must_be_admin()
def data_dictionary_upload():
    form = UploadDataDictionaryForm()

    if form.validate_on_submit():
        filepath = FileUploadDirectory.path() / secure_filename(f"data_dictionary_{datetime.now():%Y%m%d%H%M%S}_{form.upload.data.filename}")

        form.upload.data.save(filepath)
        
        csv = CsvData(filepath)

        DataDictionary.query.delete()

        section_name = ''
        i = 0

        new_items = []

        for form_name, fields in groupby(csv.iter_rows(), key=lambda f: f.get('Form Name')):
            section_name = ''

            for field in fields:
                i += 1

                dd = DataDictionary()

                dd.field_number = i
                dd.field_name = field.get('Variable / Field Name')
                dd.form_name = form_name

                if field.get('Section Header'):
                    section_name = field.get('Section Header')

                dd.section_name = section_name
                dd.field_type = field.get('Field Type')
                dd.field_label = field.get('Field Label')
                dd.choices = field.get('Choices, Calculations, OR Slider Labels')
                dd.field_note = field.get('Field Note')
                dd.text_validation_type = field.get('Text Validation Type OR Show Slider Number')
                dd.text_validation_min = field.get('Text Validation Min')
                dd.text_validation_max = field.get('Text Validation Max')

                new_items.append(dd)

        db.session.add_all(new_items)
        db.session.commit()

        flash('Data Dictionary Uploaded')

        return redirect(url_for('ui.data_dictionary'))

    return render_template(
        "ui/data_dictionary/upload.html",
        form=form,
    )


