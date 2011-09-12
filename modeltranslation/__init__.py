# -*- coding: utf-8 -*-


# Every model registered with the modeltranslation.translator.translator is
# patched to contain additional localized versions for every field specified
# in the model's translation options.
def autodiscover(*args, **kwargs):
    """
    Auto-discover INSTALLED_APPS translations.py modules and fail silently when
    not present. This forces an import on them to register any translations
    bits they may want.
    """
    import sys
    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule
    from modeltranslation.translator import translator

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's translations module.
        try:
            before_import_registry = copy.copy(translator._registry)
            import_module('%s.translations' % app)
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            translator._registry = before_import_registry

            # Decide whether to bubble up this error. If the app just
            # doesn't have a translations module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'translations'):
                raise

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
