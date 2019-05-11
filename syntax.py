def repr_config(config):
    category, option = config
    return f"{category}={option}"


def is_enabled(config, enabled):
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
    def new(check_condition, name: str=None):
        class ConfigOperable(ConfigOp):
            def __init__(self, *operation, **config):
                assert len(operation) + len(config) == 1

                self.operation = operation[0] if len(operation) == 1 else None
                self.config = next(iter(config.items())) if len(config) == 1 else None

            def __call__(self, enabled):
                if self.operation is not None:
                    return check_condition(self.operation(enabled))
                return check_condition(is_enabled(self.config, enabled))

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

            def __call__(self, enabled):
                are_ops_ok = True
                are_configs_ok = True

                if self.operations is not None:
                    are_ops_ok = check_condition(
                        op(enabled) for op in self.operations)

                if self.configs is not None:
                    are_configs_ok = check_condition(
                        is_enabled(config, enabled) for config in self.configs.items())

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


# Used internally and should not be imported anywhere:
_is_ = ConfigOp.new(lambda val: val, None)


Is = ConfigOp.new(lambda val: val, name='Is')
Not = ConfigOp.new(lambda val: not val, name='Not') # `not` is not a function
All = MultiConfigOp.new(all, name='All')
Any = MultiConfigOp.new(any, name='Any')