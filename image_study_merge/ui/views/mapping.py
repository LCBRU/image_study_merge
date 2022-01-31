from email.policy import default
import time
from flask_api import status
from flask import render_template, request
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn
from lbrc_flask.forms import SearchForm, FlashingForm
from lbrc_flask.database import db
from itertools import groupby
from functools import lru_cache
from wtforms import StringField, FormField, FieldList, Form, HiddenField, IntegerField, BooleanField
from wtforms_components import SelectField
from sqlalchemy import func, or_
from .. import blueprint


@lru_cache
def _data_dictionary_choices(time_to_live):
    data_dictionary = []

    for k, g in groupby(DataDictionary.query.all(), lambda dd: dd.group_name):
        data_dictionary.append((
            k,
            [(dd.field_name, dd.field_label ) for dd in g]
        ))

    return [('', '[No Mapping]'), (DataDictionary.DO_NOT_MAP, DataDictionary.DO_NOT_MAP)] + data_dictionary


def data_dictionary_choices():
    return _data_dictionary_choices(time_to_live=round(time.time() / 60))


class MappingForm(Form):
    id = HiddenField('Id')
    column_number = IntegerField('Column Number')
    name = StringField('Source', render_kw={'readonly': True})
    mapping = SelectField(
        'Destination',
        choices=data_dictionary_choices,
        default='',
        validate_choice=False,
    )

class MappingsForm(FlashingForm):
    fields = FieldList(FormField(MappingForm))


class MappingSearchForm(SearchForm):
    show_do_not_map_fields = SelectField('Show [Do Not Map] fields', choices=[('0', 'No'), ('1', 'Yes')], default='0')
    show_no_mapping_fields = SelectField('Show [No Mapping] fields', choices=[('0', 'No'), ('1', 'Yes')], default='1')
    show_mapped_fields = SelectField('Show mapped fields', choices=[('0', 'No'), ('1', 'Yes')], default='1')


@blueprint.route("/column_mapping/<int:id>", methods=['GET', 'POST'])
def column_mapping(id):
    study_data = StudyData.query.get_or_404(id)

    search_form = MappingSearchForm(formdata=request.args)

    q = StudyDataColumn.query.filter(StudyDataColumn.study_data_id == id)

    if search_form.search.data:
        q = q.filter(StudyDataColumn.name.like(f'%{search_form.search.data}%'))

    if search_form.show_do_not_map_fields.data != '1':
        q = q.filter(func.coalesce(StudyDataColumn.mapping, '') != DataDictionary.DO_NOT_MAP)

    if search_form.show_no_mapping_fields.data != '1':
        q = q.filter(func.coalesce(StudyDataColumn.mapping, '') != '')

    if search_form.show_mapped_fields.data != '1':
        q = q.filter(or_(
            func.coalesce(StudyDataColumn.mapping, '') == '',
            func.coalesce(StudyDataColumn.mapping, '') == DataDictionary.DO_NOT_MAP,
        ))

    mappings = q.paginate(
            page=search_form.page.data,
            per_page=20,
            error_out=False,
        )

    mapping_form = MappingsForm(data={
        'fields': mappings.items,
    })

    return render_template(
        "ui/column_mapping/index.html",
        study_data=study_data,
        search_form=search_form,
        mapping_form=mapping_form,
        mappings=mappings,
        data_dictionary_options=DataDictionary.grouped_data_dictionary(),
    )


@blueprint.route("/column_mapping/update", methods=['POST'])
def column_mapping_update():
    try:
        study_data_column = StudyDataColumn.query.get_or_404(request.json['study_data_column_id'])

        study_data_column.mapping = request.json['mapping']

        print(request.json['study_data_column_id'])
        print(request.json['mapping'])

        db.session.add(study_data_column)
        db.session.commit()

        return '', status.HTTP_205_RESET_CONTENT

    except:
        return 'A problem has occured.  Please try reloading the page.', status.HTTP_500_INTERNAL_SERVER_ERROR
