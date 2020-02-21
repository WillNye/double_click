def generate_md_table_str(row_list: list, headers: list) -> str:
    """Creates a markdown compatible table returned as a string

    :param row_list:
    :param headers:
    :return: formatted markdown string
    """
    table_output = f"\n| {' | '.join([header.title() for header in headers])} | \n"
    table_output += f"| {' | '.join(['---' for _ in headers])} | \n"

    for row in row_list:
        table_output += f"| {' | '.join([str(col) for col in row])} | \n"

    return f"\n{table_output}\n"


def generate_md_bullet_str(bullet_list: list) -> str:
    bullet_list = "\n".join([f"* {bullet}" for bullet in bullet_list])
    return f"\n{bullet_list}\n"


def generate_md_code_str(code_snippet: str, description: str = 'Snippet') -> str:
    """The normal ``` syntax doesn't seem to get picked up by mdv. It relies on indentation based code blocks.

    This one liner accommodates for this by just padding a code block with 4 additional spaces.
    Hacky? Sure. Effective? Yup.

    :param code_snippet:
    :param description:
    :return: formatted code snippet
    """
    code_snippet = code_snippet.replace('\n', '\n    ')
    return f'\n###{description}:\n     {code_snippet}\n'
