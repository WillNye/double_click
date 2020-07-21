import click


class NumericOption(click.Option):
    def __init__(self, param_decls=None, **attrs):
        click.Option.__init__(self, param_decls, **attrs)
        if not isinstance(self.type, click.Choice):
            raise Exception('ChoiceOption type arg must be click.Choice')

        if self.prompt:
            prompt_text = '{}:\n{}\n'.format(
                self.prompt,
                '\n'.join(f'{idx: >4}: {c}' for idx, c in enumerate(self.type.choices, start=1))
            )
            self.prompt = prompt_text

    def process_prompt_value(self, ctx, value, prompt_type):
        if value is not None:
            index = prompt_type(value, self, ctx)
            return self.type.choices[index - 1]

    def prompt_for_value(self, ctx):
        # Calculate the default before prompting anything to be stable.
        default = self.get_default(ctx)

        prompt_type = click.IntRange(min=1, max=len(self.type.choices))
        return click.prompt(
            self.prompt, default=default, type=prompt_type,
            hide_input=self.hide_input, show_choices=False,
            confirmation_prompt=self.confirmation_prompt,
            value_proc=lambda x: self.process_prompt_value(ctx, x, prompt_type))
