import sys
import yaml

from collections import defaultdict
from global_config.syntax import _is_

# Cache of functions declared from using @cfg
__function_cache = dict()


__config_data = None
__config_usage = None
__config_enabled = None
__config_defaults_enabled = None


def is_valid_dep_format(dep):
    return (isinstance(dep, str)
       and  len(dep.split('.')) in range(1, 3)
    )


def parse_dep(dep, default_category=''):
    parts = dep.split('.')
    category = default_category
    if len(parts) == 2:
        category, dep = parts
    return (category, dep)


def crawl(category, definitions, deps, enabled):
    """
    Crawls the definitions.yaml deplists

    definitions.yaml
    device:
      android: [utils]
      ios: [tools]

    crawl(deps=[utils], definitions=device { ... })
    """

    for dep in filter(lambda dep: dep not in enabled[category], deps):
        assert is_valid_dep_format(dep), "Not a valid dep format"

        # Parse dep for the composed parts of of `category.dep` If it's only
        # `dep`, then category=default_category. Otherwise, it's a different
        # category, so we change context to a different category.
        category, dep = parse_dep(dep, default_category=category)
        yield (category, dep)
        yield from crawl(category, definitions, definitions[category][dep], enabled)


def find_enabled(definitions, usage):
    """
    - use deps to get categorical definitions

    usage.yaml:
    device: [android]   # category: deplist
    """
    enabled = defaultdict(set)
    for (category, deps) in usage.items():
        for (category, dep) in crawl(category, definitions, deps, enabled):
            enabled[category].add(dep)

    return enabled


# deprecated
def __find_default_usages_inside_category(definitions):
    usages = dict()
    for category, deps in definitions.items():
        if 'default'  in deps:
            usages[category] = deps['default']
    return usages


def find_default_usages(definitions):
    usages = dict()
    for dep in definitions.get('default', []):
        category, dep = parse_dep(dep)
        usages[category] = [dep]
    return usages


def load_global_config_from_file(definitions, usages):
    global __config_data
    global __config_usage
    with open(definitions, 'r') as stream:
        __config_data = yaml.load(stream)

    with open(usages, 'r') as stream:
        __config_usage = yaml.load(stream)

    load_global_config(__config_data, __config_usage)

def load_global_config(definitions, usages):
    global __config_defaults_enabled
    global __config_enabled
    assert __config_enabled is None, "Reloading global config disallowed"

    default_usages = find_default_usages(definitions)
    __config_defaults_enabled = find_enabled(definitions, default_usages)
    __config_enabled = find_enabled(definitions, usages)
    __config_enabled = {
        **__config_defaults_enabled,
        **__config_enabled,
    }


def cfg(*operation, **config):
    def inner(fn):
        fn_old_name = fn.__name__

        enabled = __config_enabled
        is_function_enabled = _is_(*operation, **config)
        fn_new_name = f"{fn_old_name}{repr(is_function_enabled)}"
        __function_cache[fn_new_name] = fn

        callframe = sys._getframe(1)

        # Disabled saving fn into callframe. Might reenable in future. Old
        # functions can be accessed in more closely monitored __function_cache
        # callframe.f_locals[fn_new_name] = fn

        if is_function_enabled(enabled):
            return fn

        # Feature is not enabled. Returned the cached function instead:
        if fn_old_name in callframe.f_locals:
            return callframe.f_locals[fn_old_name]

        # Not an invalid function: return a function that throws on call:
        return lambda *args, **kwargs: (_ for _ in ()).throw(Exception(
            "Function not enabled. Potentially missing all cases for @cfg defined functions:\n\n"
            f"  def {fn_old_name}(...):\n"
        ))

    return inner

# populdate cfg with helper functions:
cfg.load_global_config = load_global_config
cfg.load_global_config_from_file = load_global_config_from_file
