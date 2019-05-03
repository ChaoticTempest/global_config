import sys
import yaml

__config_data = None
__config_usage = None
__config_graph = None


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

        # result = crawl(name=dep, deps=deps[category][dep], graph=deps[category])
        # print(deps[category])
        result = crawl(name=category, deps=deplist, graph=deps[category])
        deptable[category] = result

    return deptable


def load_global_config(definitions, usage):
    global __config_data
    global __config_usage
    global __config_graph

    assert __config_data is None, "Cannot reload global config"

    with open(definitions, 'r') as stream:
        __config_data = yaml.load(stream)

    with open(usage, 'r') as stream:
        __config_usage = yaml.load(stream)

    __config_graph = parse_deps(__config_data, __config_usage)


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
        name, value = next(iter(configs.items()))

        # print(name in __config_graph.keys())
        assert name in __config_graph.keys(), "Could not find config: {}".format(name)

        # feature="x":  x is not enabled
        if value not in __config_graph.get(name, set()):
            if original_name in callframe.f_locals:
                # return the original function
                return callframe.f_locals[original_name]
            else:
                # Not a valid function: return a function that throws on call
                return lambda *args, **kwargs: (_ for _ in ()).throw(
                    Exception(fmt("Cannot call cfg({}='{}') invalidated function `{}`", name, value, original_name)))

        return fn
    return inner