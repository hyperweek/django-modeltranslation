# -*- coding: utf-8 -*-
import sys
import inspect

from django.conf import settings
from django.utils import importlib

from modeltranslation.settings import TRANSLATION_REGISTRY
from modeltranslation.translator import translator


# Every model registered with the modeltranslation.translator.translator is
# patched to contain additional localized versions for every field specified
# in the model's translation options.
def handle_translations(*args, **kwargs):
    # This is a little dirty but we need to run the code that follows only
    # once, no matter how many times the main Haystack module is imported.
    # We'll look through the stack to see if we appear anywhere and simply
    # return if we do, allowing the original call to finish.
    stack = inspect.stack()

    for stack_info in stack[1:]:
        if 'handle_translations' in stack_info[3]:
            return

    # Import the project's global "translation.py" which registers model
    # classes and their translation options with the translator object.
    try:
        importlib.import_module(TRANSLATION_REGISTRY)
    except ImportError:
        sys.stderr.write("modeltranslation: Can't import module '%s'.\n"
                         "(If the module exists, it's causing an ImportError "
                         "somehow.)\n" % TRANSLATION_REGISTRY)
        # For some reason ImportErrors raised in translation.py or in modules
        # that are included from there become swallowed. Work around this
        # problem by printing the traceback explicitly.
        import traceback
        traceback.print_exc()


handle_translations()


# After importing all translation modules, all translation classes are
# registered with the translator.
if settings.DEBUG:
    try:
        if sys.argv[1] in ('runserver', 'runserver_plus'):
            translated_model_names = ', '.join(
                t.__name__ for t in translator._registry.keys())
            print('modeltranslation: Registered %d models for '
                    'translation (%s).' % (len(translator._registry),
                                            translated_model_names))
    except IndexError:
        pass
