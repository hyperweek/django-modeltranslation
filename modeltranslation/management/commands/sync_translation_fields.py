"""
 Detect new translatable fields in all models and sync database structure.

 You will need to execute this command in two cases:

   1. When you add new languages to settings.LANGUAGES.
   2. When you add new translatable fields to your models.

Credits: heavily inspired from django-transmete sync_transmeta_db command.
"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction

from ...utils import build_localized_fieldname
from ...translator import translator


def ask_for_confirmation(sql_sentences, model_full_name):
    print '\nSQL to synchronize "%s" schema:' % model_full_name
    for sentence in sql_sentences:
        print '   %s' % sentence
    while True:
        prompt = '\nAre you sure that you want to execute the previous SQL: (y/n) [n]: '
        answer = raw_input(prompt).strip()
        if answer == '':
            return False
        elif answer not in ('y', 'n', 'yes', 'no'):
            print 'Please answer yes or no'
        elif answer == 'y' or answer == 'yes':
            return True
        else:
            return False


def print_missing_langs(missing_langs, field_name, model_name):
    print '\nMissing languages in "%s" field from "%s" model: %s' % \
        (field_name, model_name, ", ".join(missing_langs))


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind."),
    )
    help = "Detect new translatable fields or new available languages and sync database structure"

    def handle(self, *args, **options):
        """ command execution """
        self.cursor = connection.cursor()
        self.introspection = connection.introspection

        self.interactive = options['interactive']

        found_missing_fields = False
        registered_models = translator._registry.keys()
        for model in registered_models:
            options = translator.get_options_for_model(model)
            # options returns full-wide spectrum of localized fields but
            # we only to synchronize the local fields attached to the model.
            local_field_names = [field.name for field in model._meta.local_fields]
            translatable_fields = [field for field in options.localized_fieldnames if field in local_field_names]
            model_full_name = '%s.%s' % (model._meta.app_label, model._meta.module_name)
            db_table = model._meta.db_table
            for field_name in translatable_fields:
                missing_langs = list(self.get_missing_languages(field_name, db_table))
                if missing_langs:
                    execute_sql = True
                    found_missing_fields = True
                    print_missing_langs(missing_langs, field_name, model_full_name)
                    sql_sentences = self.get_sync_sql(field_name, missing_langs, model)
                    if self.interactive:
                        execute_sql = ask_for_confirmation(sql_sentences, model_full_name)
                    if execute_sql:
                        print 'Executing SQL...',
                        for sentence in sql_sentences:
                            self.cursor.execute(sentence)
                        print 'Done'
                    else:
                        print 'SQL not executed'

        transaction.commit_unless_managed()

        if not found_missing_fields:
            print '\nNo new translatable fields detected'

    def get_table_fields(self, db_table):
        """ get table fields from schema """
        db_table_desc = self.introspection.get_table_description(self.cursor, db_table)
        return [t[0] for t in db_table_desc]

    def get_missing_languages(self, field_name, db_table):
        """ get only missings fields """
        db_table_fields = self.get_table_fields(db_table)
        for lang_code, lang_name in settings.LANGUAGES:
            if build_localized_fieldname(field_name, lang_code) not in db_table_fields:
                yield lang_code

    def get_sync_sql(self, field_name, missing_langs, model):
        """ returns SQL needed for sync schema for a new translatable field """
        qn = connection.ops.quote_name
        style = no_style()
        sql_output = []
        db_table = model._meta.db_table
        for lang in missing_langs:
            new_field = build_localized_fieldname(field_name, lang)
            f = model._meta.get_field(new_field)
            col_type = f.db_type()
            field_sql = [style.SQL_FIELD(qn(f.column)), style.SQL_COLTYPE(col_type)]
            # column creation
            sql_output.append("ALTER TABLE %s ADD COLUMN %s;" % (qn(db_table), ' '.join(field_sql)))
            if not f.null and lang == settings.LANGUAGE_CODE:
                sql_output.append("ALTER TABLE %s MODIFY COLUMN %s %s %s;" % \
                                  (qn(db_table), qn(f.column), col_type, \
                                  style.SQL_KEYWORD('NOT NULL')))
        return sql_output
