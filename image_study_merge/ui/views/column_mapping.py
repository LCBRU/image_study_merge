from itertools import islice
from flask_api import status
from flask import render_template, request
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn
from lbrc_flask.database import db
from sqlalchemy import func, or_

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
        show_suggestions=search_form.show_suggestions.data,
    )


@blueprint.route("/column_mapping/update", methods=['POST'])
def column_mapping_update():
    try:
        study_data_column = StudyDataColumn.query.get_or_404(request.json['study_data_column_id'])

        study_data_column.mapping = request.json['mapping']

        db.session.add(study_data_column)
        db.session.commit()

        if study_data_column.mapped_data_dictionary:
            if study_data_column.mapped_data_dictionary.has_choices:
                automap_value__map_exact_name(study_data_column)

        return '', status.HTTP_205_RESET_CONTENT

    except:
        return 'A problem has occured.  Please try reloading the page.', status.HTTP_500_INTERNAL_SERVER_ERROR


@blueprint.route("/column_mapping/source_sample/", methods=['POST'])
def column_mapping_source_sample():
    col = StudyDataColumn.query.get_or_404(request.json['study_data_column_id'])

    return {
        'samples': list(islice(col.unique_data_value(), None, 20))
    }
