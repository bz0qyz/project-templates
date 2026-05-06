import argparse
from .._base import AppModuleBase
from runtime._shared import EnvDefault
# IMPORTANT: modules are not loaded by pyinstaller, therefore
#            any base (not pypi) modules used in modules that are not used in the base app, must be imported
#            in runtime._shared to be included in the package


# Initialize the module sub-class from AppModule
class AppModule(AppModuleBase):
    def register_args(self) -> None:
        """
        Add argparse arguments for the module.
        same basic format as an argparse argument,
        except that the arguments must be in a list.
        NOTE: When using EnvDefault (Environment variables), use type 'str' for boolean arguments.
        WARNING: argument options 'envvar' and 'dest' must be unique in all modules
        WARNING: if no 'dest' is specified, only argument flags that start with '--' will work.
        :return: None
        """

        # Example Arguments
        self.add_argument(['--template-foo'],
                default='bar',
                help='example string argument foo',
                type=str,
                dest="template_foo",
                action=EnvDefault,
                envvar="TEMPLATE_FOO"
        )
        self.add_argument(['--template-bar'],
                default=False,
                help='example boolean argument bar',
                type=str,
                dest="template_bar",
                action=EnvDefault,
                envvar="TEMPLATE_BAR"
        )

    def main(self, *args, **kwargs) -> bool:
        """"
        Main entry point for the module.
        returns: bool. Success or failure.
        """
        self.logger.info(f"Running module: '{self.name}'")
        for arg, value in self.args.__dict__.items():
            self.logger.info(f"Argument: '{arg}' -> '{value}' ({type(value)})")

        # Example run. Simulates ramdom execution time and return value
        import random
        from time import sleep
        sleep(random.randrange(3, 8))
        return bool(random.randint(0, 1))



# Initialize the module class
module = AppModule(
    name="template",
    description="Template module",
    version="1.0.0",
    enabled=True,
    default_disabled=True
)
module.register_args()

"""
FUNCTION DECORATORS:
1. @module.post_init - Specify functions that will execute immediately after the module is initialized.
2. @module.before_run - Specify functions that will execute before the module's main function
3. @module.after_run - Specify functions that will execute after the module completes
"""
# Example function to be executed post init
@module.post_init
def setup() -> None:
    module.logger.info(f"[EXAMPLE] Running {module.name} post-init hook setup()")

# Example function to be executed before the run
@module.before_run
def prepare():
    module.logger.info(f"[EXAMPLE] Running {module.name} pre-run hook prepare()")

# Example function to be executed after the run is complete
@module.after_run
def teardown(result):
    module.logger.info(f"[EXAMPLE] Running {module.name} post-run hook teardown()")
    module.logger.info(f"run result={result}")

