import cfg as t

def setup():
    t.load_global_config("definitions.yaml", "use.yaml")

setup()


# print(t.__config_data)
# print(t.__config_usage)
# print(t.__config_graph)


@t.cfg(phone_os="android")
def locate():
    print("Locating on Android")


@t.cfg(phone_os="ios")
def locate():
    print("Locating on IOS")

@t.cfg(phone_os="android")
def locate():
    print("Locating on Android")


@t.cfg(locale="japan")
def locale():
    print("In Japan")

@t.cfg(locale="uk")
def locale():
    print("In UK")


if __name__ == "__main__":
    locate()
    locale()
