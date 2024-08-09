from flask import flash, render_template, render_template_string, request
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataColumnSuggestion, StudyDataColumnValueMapping
from lbrc_flask.database import db
from lbrc_flask.logging import log_exception
from lbrc_flask.response import refresh_response
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from image_study_merge.services import automap_value__map_exact_name
from image_study_merge.ui.views.forms import MappingSearchForm
from .. import blueprint


@blueprint.route("/column_mapping/<int:id>", methods=['GET', 'POST'])
def column_mapping(id):
    study_data = StudyData.query.get_or_404(id)

    search_form = MappingSearchForm(formdata=request.args)

    q = StudyDataColumn.query.filter(StudyDataColumn.study_data_id == id)

    if search_form.search.data:
        q = q.filter(StudyDataColumn.name.like(f'%{search_form.search.data}%'))

    if search_form.show_do_not_import.data != '1':
        q = q.filter(func.coalesce(StudyDataColumn.mapping, '') != DataDictionary.DO_NOT_IMPORT)

    if search_form.show_not_yet_mapped.data != '1':
        q = q.filter(func.coalesce(StudyDataColumn.mapping, '') != '')

    if search_form.show_no_suitable_mapping.data != '1':
        q = q.filter(func.coalesce(StudyDataColumn.mapping, '') != DataDictionary.NO_SUITABLE_MAPPING)

    if search_form.show_mapped.data != '1':
        q = q.filter(or_(
            func.coalesce(StudyDataColumn.mapping, '') == '',
            func.coalesce(StudyDataColumn.mapping, '') == DataDictionary.DO_NOT_IMPORT,
        ))

    q = q.options(
        selectinload(StudyDataColumn.suggested_mappings).selectinload(StudyDataColumnSuggestion.data_dictionary),
        selectinload(StudyDataColumn.mapped_data_dictionary),
        selectinload(StudyDataColumn.value_mappings),
    )

    mappings = q.paginate(
            page=search_form.page.data,
            per_page=20,
            error_out=False,
        )

    return render_template(
        "ui/column_mapping/index.html",
        study_data=study_data,
        search_form=search_form,
        mappings=mappings,
        data_dictionary_options=DataDictionary.grouped_data_dictionary(),
    )


@blueprint.route("/column_mapping/<int:id>/map_to/", methods=['POST'])
@blueprint.route("/column_mapping/<int:id>/map_to/<string:mapping>", methods=['POST'])
def column_mapping_update(id, mapping=''):
    try:
        details_selector=request.form.get('details_selector', 'suggestions')

        study_data_column = StudyDataColumn.query.get_or_404(id)
        study_data_column.mapping = mapping

        db.session.add(study_data_column)
        db.session.commit()

        if study_data_column.mapped_data_dictionary:
            if study_data_column.mapped_data_dictionary.has_choices:
                automap_value__map_exact_name(study_data_column)

        db.session.commit()

        return refresh_column_mapping_details(id, details_selector)

    except Exception as e:
        log_exception(e)
        flash('A problem has occured.  Please try reloading the page.', 'error')

    return refresh_response()


@blueprint.route("/study_data_column/<int:id>/<string:details_selector>")
def column_mapping_details(id, details_selector):
    return refresh_column_mapping_details(id, details_selector)


def refresh_column_mapping_details(id, details_selector):
    col = db.get_or_404(StudyDataColumn, id)

    value_mapping_choices = {
        '': DataDictionary.NOT_YET_MAPPED,
        DataDictionary.DO_NOT_IMPORT: DataDictionary.DO_NOT_IMPORT,
        DataDictionary.NO_SUITABLE_MAPPING: DataDictionary.NO_SUITABLE_MAPPING,
    }

    if col.has_value_choices():
        value_mapping_choices.update({value: f'{name} ({value})' for value, name in
            col.mapped_data_dictionary.choice_values.items()
        })

    template = '''
        {% from "ui/column_mapping/_details.html" import render_column_mapping with context %}

        {{ render_column_mapping(mapping, details_selector) }}
    '''

    return render_template_string(
        template,
        mapping=col,
        details_selector=details_selector,
        value_mapping_choices=value_mapping_choices,
        data_dictionary_options=DataDictionary.grouped_data_dictionary(),
    )


@blueprint.route("/value_mapping/<int:id>/map_to/", methods=['POST'])
@blueprint.route("/value_mapping/<int:id>/map_to/<string:mapping>", methods=['POST'])
def value_mapping_update(id, mapping=''):
    try:
        vm = StudyDataColumnValueMapping.query.get_or_404(id)

        vm.mapping = mapping

        db.session.add(vm)
        db.session.commit()
    except:
        flash('A problem has occured.  Please try reloading the page.')

    return refresh_column_mapping_details(vm.study_data_column_id, 'value_mappings')