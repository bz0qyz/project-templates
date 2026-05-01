import argparse
from .._shared import AppModuleBase
from runtime._shared import EnvDefault

# Initialize the module sub-class from AppModule
class AppModule(AppModuleBase):
    def register_args(self) -> None:
        """
        Add argparse arguments for the module.
        same basic format as an argparse argument,
        except that the arguments must be in a list.
        WARNING: argument options 'envvar' and 'dest' must be unique in all modules
        WARNING: if no 'dest' is specified, only argument flags that start with '--' will work.
        :return: None
        """

        # Example Arguments
        self.add_argument(['--template-foo'],
                        default='bar',
                        help='example string argument foo',
                        dest = "template_foo",
                        type = str,
                        action = EnvDefault,
                        envvar = "TEMPLATE_FOO"
        )
        self.add_argument(['--template-bar'],
                          default=False,
                          help='example boolean argument bar',
                          type=bool,
                          dest="template_bar",
                          action=EnvDefault,
                          envvar="TEMPLATE_BAR"
                          )

    def shutdown(self):
        super().shutdown()
        self.logger.debug(f"Closing connections...")

    def main(self, *args, **kwargs) -> None:
        """"
        Main entry point for the module.
        returns: realm representation with changes
        """
        self.logger.info(f"Running module: '{self.name}'")
        for arg, value in self.args.__dict__.items():
            self.logger.info(f"Argument: '{arg}' -> '{value}' ({type(value)})")


# Initialize the module class
module = AppModule(
    name="template",
    description="Template module",
    version="1.0.0",
    enabled=True,
    default_disabled=True
)
module.register_args()

