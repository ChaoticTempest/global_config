# global_config

A global config used for function branching, largely inspired by Rust's cfg macro:
```Python
from global_config import cfg

cfg.load_global_config_from_file("definitions.yaml", "usage.yaml")
# in definitions.yaml
#   coffee:
#     mocha: []
#     caramel: []
#
# in usage.yaml
#   coffee: [mocha]
# 

@cfg(coffee="mocha")
def get_coffee():
  print("Mocha Latte")

@cfg(coffee="caramel")
def get_coffee():
  print("Caramel Latte")

get_coffee()  # prints "Mocha Latte"
```

## Use with Caution

A note on safety of using this module:
- This module loads in the function during runtime: more precisely when the module containing the `@cfg(..)` gets imported and cached.
- `load_global_config` should be run before the python interpreter ever hits a `@cfg` otherwise it will do nothing or raise.
- `@cfg` should be the top most decorater, otherwise the wrong function will be loaded into the module:
  ```Python
  @cfg(...)
  @second_decorator
  ...
  @third_decorator
  def func():
    ...
  ```


## More Examples

```Python
from global_config import cfg, Is, Not, Any, All

cfg.load_global_config(
  definitions={
    'coffee': {
      'mocha': [],
      'caramel': [],
    }
  },
  usages={
    'coffee': []
  }
)

@cfg(Any(Is(coffee="caramel"), Is(coffee="mocha")))
def get_coffee():
  print("Mocha or Caramel Latte")

@cfg(All(Not(coffee="caramel"), Not(coffee="mocha")))
def get_coffee():
  print("Mystery Latte")

get_coffee()  # prints "Mystery Latte"
```
NOTE: python `**kwargs` does not support multiple `coffee=` declarations, so need to create multiple `Is` or `Not` if the feature you want are the same.

