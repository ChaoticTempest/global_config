import sys
import yaml

EMPTYSET = set()

__config_data = None
__config_usage = None
__config_enabled = None
__config_defaults_enabled = None



def crawl(name, deps, graph, seen=None):
    """
    Crawls the definitions.yaml deplists

    definitions.yaml
    device:
      android: [utils]
      ios: [tools]

    crawl(name=android, deps=[utils], graph=device { ... })
    """

    seen = seen or set()
    deps = filter(lambda dep: dep not in seen, deps)
    for dep in deps:
        seen.add(dep)
        crawl(dep, graph[dep], graph, seen)
    return seen


def parse_deps(deps, usage):
    """
    - use deps to get categorical graph

    usage.yaml:
    device: [android]   # category: deplist
    """

    deptable = dict()
    for category, deplist in usage.items():
        result = crawl(name=category, deps=deplist, graph=deps[category])
        deptable[category] = result

    return deptable


def find_defaults(deflist):
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

    default_usages = find_defaults(__config_data)
    __config_defaults_enabled = parse_deps(__config_data, default_usages)
    __config_enabled = parse_deps(__config_data, __config_usage)


def fmt(s, *args, **kwargs):
    return s.format(*args, **kwargs)


def cfg(**configs):
    def inner(fn):
        original_name = fn.__name__

        # Save the function renamed in the callframe:
        new_name = "_{}".format(fn.__name__)
        callframe = sys._getframe(1)
        callframe.f_locals[new_name] = fn

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
        if original_name in callframe.f_locals:
            return callframe.f_locals[original_name]

        # Not a valid function: return a function that throws on call:
        return lambda *args, **kwargs: (_ for _ in ()).throw(
            Exception(fmt("Cannot call cfg({}='{}') invalidated function `{}`", category, option, original_name)))

    return inner