
import sys
import cfg as t

from syntax import Not, Any, All

def setup():
    t.load_global_config("definitions.yaml", "use.yaml")

setup()


# print(t.__config_data)
# print(t.__config_usage)
# print(t.__config_enabled)
# print(t.__config_defaults_enabled)



@t.cfg(phone_os="ios")
def locate():
    print("Locating on IOS")

# @t.cfg(phone_os="android")
@t.cfg(Not(phone_os="ios"))
def locate():
    print("Locating on Android")


@t.cfg(locale="usa")
def locale():
    print("In USA")

@t.cfg(locale="uk")
def locale():
    print("In UK")

@t.cfg(locale=["japan", "china"])
def locale():
    print("In Japan or China")

@t.cfg(phone="pixel")
def which_phone():
    print("Pixel")

@t.cfg(phone="iphone")
def which_phone():
    print("Iphone")

if __name__ == "__main__":
    locate()
    locale()
    which_phone()
    print()
    # print(f"Config Data: {print(dir(sys.modules[t.__name__]))}")
