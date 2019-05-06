import sys
import yaml

from collections import defaultdict


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
def _find_default_usages_inside_category(definitions):
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


def load_global_config(definitions, usage):
    global __config_data
    global __config_usage
    global __config_defaults_enabled
    global __config_enabled

    assert __config_data is None, "Reloading global config disallowed"

    with open(definitions, 'r') as stream:
        __config_data = yaml.load(stream)

    with open(usage, 'r') as stream:
        __config_usage = yaml.load(stream)

    default_usages = find_default_usages(__config_data)
    __config_defaults_enabled = find_enabled(__config_data, default_usages)
    __config_enabled = find_enabled(__config_data, __config_usage)


def cfg(**configs):
    def inner(fn):
        fn_old_name = fn.__name__

        # Save the function renamed in the callframe:
        fn_new_name = "_{}".format(fn.__name__)
        callframe = sys._getframe(1)
        callframe.f_locals[fn_new_name] = fn

        # TODO: temprorary. Only getting the first item:
        category, option = next(iter(configs.items()))

        # Handle default enabled:
        enabled = __config_enabled
        if category not in __config_enabled:
            enabled = __config_defaults_enabled

        # feature="x":  x is enabled
        if option in enabled.get(category, set()):
            return fn

        # Feature is not enabled. Returned the cached function instead:
        if fn_old_name in callframe.f_locals:
            return callframe.f_locals[fn_old_name]

        # Not a valid function: return a function that throws on call:
        return lambda *args, **kwargs: (_ for _ in ()).throw(Exception(
            "Potentially missing all cases for @cfg defined functions. "
            "Cannot call not enabled function:\n\n"
            f"  @cfg({category}='{option}')\n"
            f"  def {fn_old_name}(...):\n"
        ))

    return inner