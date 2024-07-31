from wtforms import SelectField
from lbrc_flask.forms import SearchForm
from image_study_merge.model import DataDictionary


class MappingSearchForm(SearchForm):
    show_do_not_import = SelectField(f'Show {DataDictionary.DO_NOT_IMPORT}', choices=[('0', 'No'), ('1', 'Yes')], default='0')
    show_not_yet_mapped = SelectField(f'Show {DataDictionary.NOT_YET_MAPPED}', choices=[('0', 'No'), ('1', 'Yes')], default='1')
    show_no_suitable_mapping = SelectField(f'Show {DataDictionary.NO_SUITABLE_MAPPING}', choices=[('0', 'No'), ('1', 'Yes')], default='1')
    show_mapped = SelectField('Show mapped', choices=[('0', 'No'), ('1', 'Yes')], default='1')
    show_suggestions = SelectField('Show suggestions', choices=[('0', 'No'), ('1', 'Unmapped Values'), ('2', 'All')], default='1')
