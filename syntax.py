import sys
import platform


def repr_config(config):
    category, option = config
    return f"{category}={option}"


def is_enabled(config, enabled: dict, bypasses: dict):
    category, option = config

    # This add a bit more complexity than needs to for now. Will reenable in future
    # if isinstance(option, list):
    #     return any(opt in enabled.get(category, set()) for opt in option)

    for _category, bypass in bypasses.items():
        if bypass(config):
            return True

    # check for feature="x" => True: x is enabled. False: otherwise
    return option in enabled.get(category, set())


class ConfigOp(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def __call__(self, config_data):
        raise NotImplementedError()

    @staticmethod
    def new(check_condition, name: str=None):
        class ConfigOperable(ConfigOp):
            def __init__(self, *operation, **config):
                assert len(operation) + len(config) == 1

                self.operation = operation[0] if len(operation) == 1 else None
                self.config = next(iter(config.items())) if len(config) == 1 else None

            def __call__(self, enabled, bypasses):
                if self.operation is not None:
                    return check_condition(self.operation(enabled, bypasses))
                return check_condition(is_enabled(self.config, enabled, bypasses))

            def __repr__(self):
                args = []
                if self.operation is not None:
                    args.append(repr(self.operation))
                if self.config is not None:
                    args.append(repr_config(self.config))

                s = name if name is not None else ""
                s = f"{s}({', '.join(args)})"

                return s

        return ConfigOperable


class MultiConfigOp(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def assert_multi_predicates(operations, configs):
        assert len(operations) + len(configs) > 0, "Need to provide at least one operation or config"
        assert all(isinstance(op, ConfigOp) for op in operations), "Not all operations are a ConfigOp type"
        assert all(isinstance(option, str) for option in configs.values()), "Expected config values to be of type str"

    @staticmethod
    def new(check_condition, name: str=None):
        class MultiConfigOperable(ConfigOp):
            def __init__(self, *operations, **configs):
                MultiConfigOp.assert_multi_predicates(operations, configs)
                self.operations = operations if len(operations) > 0 else None
                self.configs = configs if len(configs) > 0 else None

            def __call__(self, enabled, bypasses):
                are_ops_ok = True
                are_configs_ok = True

                if self.operations is not None:
                    are_ops_ok = check_condition(
                        op(enabled, bypasses) for op in self.operations)

                if self.configs is not None:
                    are_configs_ok = check_condition(
                        is_enabled(config, enabled, bypasses)
                        for config in self.configs.items())

                return are_ops_ok and are_configs_ok

            def __repr__(self):
                args = []
                if self.operations is not None:
                    args.append(', '.join(repr(op) for op in self.operations))
                if self.configs is not None:
                    args.append(', '.join(repr_config(cf) for cf in self.configs.items()))

                s = name if name is not None else ""
                s = f"{s}({','.join(args)})"
                return s

        return MultiConfigOperable


class Bypass(object):
    """
    Construct a user defined configuration that bypasses any config defined in
    the definitions. Used to support mapping a config to a function. Will raise
    if the user specifies the same config in the definitions/usages.
    """

    def __init__(self, category: str, check_condition):
        self.category = category
        self.check_condition = check_condition
        self.options = None

    def with_options(self, options: list):
        # list of available of options. If provided option is not one of the
        # following options, we will throw and fail.
        self.options = options
        return self

    def __call__(self, config):
        category, option = config
        if category != self.category:
            return False

        if self.options is not None and option not in self.options:
            raise Exception(f"Invalid config: {self.category}='{option}' is not in {self.options}")

        return self.check_condition(config)

    def get_options(self, nocopy=False):
        if self.options is None:
            return []
        if nocopy:
            return self.options
        return self.options.copy()



# ---------------------------------------------------------------------------- #
# Enabled config syntax features                                               #
# ---------------------------------------------------------------------------- #

# Used internally and should not be imported anywhere:
_is_ = ConfigOp.new(lambda val: val, None)


Is = ConfigOp.new(lambda val: val, name='Is')
Not = ConfigOp.new(lambda val: not val, name='Not') # `not` is not a function
All = MultiConfigOp.new(all, name='All')
Any = MultiConfigOp.new(any, name='Any')


def is_correct_os(config):
    _, option = config
    return platform.system().lower() == option


TARGET_OS = Bypass('target_os', is_correct_os).with_options([
    "windows",
    "macos",
    "linux",
    "java",
    "android",
    "freebsd",
    "unknown",
])


SYSTEM_BYPASSES = [
    TARGET_OS,
]
