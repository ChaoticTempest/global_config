

def is_enabled(config, enabled):
    print(config)
    category, option = config

    if isinstance(option, list):
        return any(opt in enabled.get(category, set()) for opt in option)

    # check for feature="x" => True: x is enabled. False: otherwise
    return option in enabled.get(category, set())


class ConfigOp(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def __call__(self, config_data):
        raise NotImplementedError()

    @staticmethod
    def new(check_condition):
        class ConfigOperable(ConfigOp):
            def __init__(self, *operation, **config):
                assert len(operation) + len(config) == 1

                self.operation = operation[0] if len(operation) == 1 else None
                self.config = next(iter(config.items())) if len(config) == 1 else None

            def __call__(self, enabled):
                if self.operation is not None:
                    return check_condition(self.operation(enabled))
                return check_condition(is_enabled(self.config, enabled))

        return ConfigOperable


class MultiConfigOp():
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def assert_multi_predicates(operations, configs):
        assert len(operations) + len(configs) > 0
        assert all(isinstance(op, ConfigOp) for op in operations)
        assert all(isinstance(option, str) for option in configs.values())

    @staticmethod
    def new(check_condition):
        class MultiConfigOperable(ConfigOp):
            def __init__(self, *operations, **configs):
                MultiConfigOp.assert_multi_predicates(operations, configs)
                self.operations = operations
                self.configs = configs

            def __call__(self, enabled):
                are_ops_ok = check_condition(op(enabled) for op in self.operations)
                are_configs_ok = check_condition(is_enabled(config, enabled) for config in self.configs.items())
                return are_ops_ok and are_configs_ok

        return MultiConfigOperable

_is_ = ConfigOp.new(lambda val: val)
Not = ConfigOp.new(lambda val: not val) # `not` is not a function
All = MultiConfigOp.new(all)
Any = MultiConfigOp.new(any)
