from flask import render_template, request, redirect, url_for
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn
from lbrc_flask.forms import SearchForm, FlashingForm
from itertools import groupby
from wtforms import SelectField, StringField, FormField, FieldList, Form
from .. import blueprint


class MappingForm(Form):
    name = StringField('Source', render_kw={'readonly': True})
    mapping = SelectField('Destination', choices=[], default='', validate_choice=False)


class MappingsForm(FlashingForm):
    fields = FieldList(FormField(MappingForm))


def _get_data_dictionary_values():
    data_dictionary = []

    for k, g in groupby(DataDictionary.query.all(), lambda dd: dd.form_name):
        data_dictionary.append({
            'text': k,
            'children': [{'id': dd.field_name, 'text': dd.field_label } for dd in g]
        })

    return [{'id': '', 'text': '[No Mapping]'}] + data_dictionary


@blueprint.route("/column_mapping/<int:id>", methods=['GET', 'POST'])
def column_mapping(id):
    study_data = StudyData.query.get_or_404(id)

    search_form = SearchForm(formdata=request.args)

    q = StudyDataColumn.query.filter(StudyDataColumn.study_data_id == id)

    if search_form.search.data:
        q = q.filter(StudyDataColumn.name.like(f'%{search_form.search.data}%'))

    mapping_form = MappingsForm(data={
        'fields': q.all(),
    })

    return render_template(
        "ui/column_mapping/index.html",
        study_data=study_data,
        search_form=search_form,
        mapping_form=mapping_form,
        data_dictionary=_get_data_dictionary_values(),
    )


@blueprint.route("/column_mapping/<int:id>/save", methods=['POST'])
def column_mapping_save(id):
    study_data = StudyData.query.get_or_404(id)

    form = MappingsForm()

    if form.validate_on_submit():
        for field in form.fields:
            print(field.name)
            print(field.mapping)

    return redirect(url_for('ui.column_mapping', id=id))
