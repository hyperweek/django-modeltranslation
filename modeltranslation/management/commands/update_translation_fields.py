# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import F, Q
from django.core.management.base import NoArgsCommand

from ...translator import translator
from ...utils import build_localized_fieldname


class Command(NoArgsCommand):
    help = 'Updates the default translation fields of all or the specified'\
           'translated application using the value of the original field.'

    def handle(self, **options):
        print "Using default language:", settings.LANGUAGE_CODE

        for model, trans_opts in translator._registry.items():
            print "Updating data of model '%s'" % model
            for fieldname in trans_opts.fields:
                def_lang_fieldname =\
                build_localized_fieldname(fieldname, settings.LANGUAGE_CODE)

                # We'll only update fields which do not have an existing value:
                model.objects.filter(Q(**{def_lang_fieldname: None}) |\
                                     Q(**{def_lang_fieldname: ""})).update(\
                                     **{def_lang_fieldname: F(fieldname)})
