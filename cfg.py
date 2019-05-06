import sys
import yaml


__config_data = None
__config_usage = None
__config_enabled = None
__config_defaults_enabled = None


def crawl(name, deps, deflist, seen=None):
    """
    Crawls the definitions.yaml deplists

    definitions.yaml
    device:
      android: [utils]
      ios: [tools]

    crawl(name=android, deps=[utils], deflist=device { ... })
    """

    seen = seen or set()
    for dep in filter(lambda dep: dep not in seen, deps):
        seen.add(dep)
        crawl(dep, deflist[dep], deflist, seen)
    return seen


def find_enabled(deps, usage):
    """
    - use deps to get categorical deflist

    usage.yaml:
    device: [android]   # category: deplist
    """

    deptable = dict()
    for category, deplist in usage.items():
        result = crawl(name=category, deps=deplist, deflist=deps[category])
        deptable[category] = result

    return deptable


def find_default_usages(deflist):
    usages = dict()
    for category, deps in deflist.items():
        if 'default'  in deps:
            usages[category] = deps['default']
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