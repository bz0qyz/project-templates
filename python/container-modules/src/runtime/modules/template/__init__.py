import argparse
from .._shared import AppModule
from runtime._shared import EnvDefault

# Initialize the module sub-class from AppModule
class TemplateModule(AppModule):
    def register_args(self, parser: argparse.ArgumentParser):
        super().register_args(parser)  # gets the base --disable-<name> arg
        args = parser.add_argument_group(f"{self.name} options")
        # WARNING: 'envvar' and 'dest' must be unique in all modules
        args.add_argument('--template-foo',
                        default='bar',
                        dest = "template_foo",
                        action = EnvDefault,
                        envvar = "TEMPLATE_FOO"
        )
    def shutdown(self):
        super().shutdown()
        self.logger.info(f"Closing connections...")

# Initialize the module class
module = TemplateModule(
    name="template",
    description="Template module",
    version="0.0.1",
    disabled=False,
)
