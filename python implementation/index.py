import os

def lexer(input):
    """
    Lexical analyzer for the Quanta programming language.
    This function takes an input string and tokenizes it into a list of tokens.

    Parameters:
    input (str): The input code written in Quanta language.

    Returns:
    list: A list of dictionaries, where each dictionary represents a token with 'type' and 'value' keys.

    Raises:
    ValueError: If an invalid character is encountered in the input.
    """
    tokens = []
    cursor = 0

    while cursor < len(input):
        char = input[cursor]

        # Skip whitespace characters
        if char.isspace():
            cursor += 1
            continue

        # Identify and tokenize keywords and identifiers
        if char.isalpha():
            word = ''

            while cursor < len(input) and (input[cursor].isalnum()):
                word += input[cursor]
                cursor += 1

            # Check if the word is a keyword
            if word in {'let', 'write', 'if', 'elif', 'else', 'end', 'repeat'}:
                tokens.append({'type': 'keyword', 'value': word})
            else:
                tokens.append({'type': 'identifier', 'value': word})

            continue

        # Identify and tokenize numbers
        if char.isdigit():
            number = ''

            while cursor < len(input) and input[cursor].isdigit():
                number += input[cursor]
                cursor += 1

            tokens.append({'type': 'number', 'value': int(number)})
            continue

        # Identify and tokenize strings
        if char == '"':
            string = ''
            cursor += 1  # skip the opening quote
            while cursor < len(input) and input[cursor] != '"':
                string += input[cursor]
                cursor += 1
            cursor += 1  # skip the closing quote
            tokens.append({'type': 'string', 'value': string})
            continue

        # Identify and tokenize operators
        if char in '+-*/=<>&|':
            tokens.append({'type': 'operator', 'value': char})
            cursor += 1
            continue

        # Raise an error for invalid characters
        raise ValueError(f"Invalid character '{char}' at position {cursor}")

    return tokens

def parser(tokens):
    """
    Parses the list of tokens into an Abstract Syntax Tree (AST).

    Parameters:
    tokens (list): A list of dictionaries, where each dictionary represents a token with 'type' and 'value' keys.

    Returns:
    dict: A dictionary representing the AST.
    """

    def parse_expression(tokens):
        """
        Parses a sequence of tokens into an expression.

        Parameters:
        tokens (list): A list of dictionaries, where each dictionary represents a token with 'type' and 'value' keys.

        Returns:
        str: A string representing the parsed expression.
        """
        expression = ''
        while tokens and tokens[0]['type'] not in {'keyword'}:
            if tokens[0]['type'] == 'string':
                expression += f'"{tokens.pop(0)["value"]}"' + ' '

            else:
                expression += str(tokens.pop(0)['value']) + ' '

        return expression.strip()

    def parse_block(tokens):
        body = []
        while tokens:
            if tokens[0]['value'] == 'end':
                tokens.pop(0)  # Consume the 'end' token
                break
            token = tokens.pop(0)

            if token['type'] == 'keyword' and token['value'] == 'let':
                declaration = {
                    'type': 'Declaration',
                    'name': tokens.pop(0)['value'],
                    'value': None,
                }

                if tokens[0]['type'] == 'operator' and tokens[0]['value'] == '=':
                    tokens.pop(0)
                    declaration['value'] = parse_expression(tokens)
                body.append(declaration)

            elif token['type'] == 'keyword' and token['value'] == 'write':
                body.append({
                    'type': 'Print',
                    'expression': parse_expression(tokens),
                })

            elif token['type'] == 'keyword' and token['value'] == 'if':
                body.append(parse_if(tokens))

            elif token['type'] == 'keyword' and token['value'] == 'repeat':
                body.append(parse_repeat(tokens))

        return body

    def parse_if(tokens):
        """
        Parses an 'if' statement and its associated 'elif' and 'else' clauses.

        Parameters:
        tokens (list): A list of dictionaries, where each dictionary represents a token with 'type' and 'value' keys.

        Returns:
        dict: A dictionary representing the parsed 'if' statement.
        """
        if_node = {
            'type': 'If',
            'test': parse_expression(tokens),
            'consequent': parse_block(tokens),
            'alternate': None,
        }

        if tokens and tokens[0]['value'] == 'elif':
            tokens.pop(0)
            if_node['alternate'] = parse_if(tokens)
        elif tokens and tokens[0]['value'] == 'else':
            tokens.pop(0)
            if_node['alternate'] = {'type': 'Block', 'body': parse_block(tokens)}

        return if_node

    def parse_repeat(tokens):
        """
        Parses a 'repeat' loop statement.
        """
        repeat_node = {
            'type': 'Repeat',
            'count': parse_expression(tokens),
            'body': [],
        }
        repeat_node['body'] = parse_block(tokens)
        return repeat_node

    ast = {
        'type': 'Program',
        'body': parse_block(tokens),
    }

    return ast

def codeGenerator(node, indent_level=0):
    """
    This function generates Python code from an Abstract Syntax Tree (AST) node.

    Parameters:
    node (dict): A dictionary representing an AST node. The dictionary must contain a 'type' key
                 indicating the type of node, and other keys representing the node's attributes.
    indent_level (int, optional): The current indentation level for the generated code. Defaults to 0.

    Returns:
    str: The generated Python code corresponding to the given AST node.

    Raises:
    ValueError: If the input node type is not recognized.
    """
    indent = '    ' * indent_level
    if node['type'] == 'Program':
        return '\n'.join(codeGenerator(n, indent_level) for n in node['body'])
    
    elif node['type'] == 'Declaration':
        return f"{indent}{node['name']} = {node['value']}"
    
    elif node['type'] == 'Print':
        return f"{indent}print({node['expression']})"
    
    elif node['type'] == 'If':
        code = f"{indent}if {node['test']}:\n"
        code += codeGenerator({'type': 'Block', 'body': node['consequent']}, indent_level + 1)
        code += f"\n{indent}# end"

        if node['alternate']:
            if node['alternate']['type'] == 'If':
                code += f"\n{indent}el{codeGenerator(node['alternate'], indent_level)}"
            else:
                code += f"\n{indent}else:\n{codeGenerator(node['alternate'], indent_level + 1)}"
                code += f"\n{indent}# end"
        return code
    
    elif node['type'] == 'Block':
        return '\n'.join(codeGenerator(n, indent_level) for n in node['body'])
    
    elif node['type'] == 'Repeat':
        code = f"{indent}for _ in range(int({node['count']})):\n"
        code += codeGenerator({'type': 'Block', 'body': node['body']}, indent_level + 1)
        code += f"\n{indent}# end"
        return code
    
    else:
        raise ValueError(f"Unrecognized node type: {node['type']}")

def compiler(input):
    """
    This function compiles the input code written in a custom language called Quanta into executable Python code.

    Parameters:
    input (str): The input code written in Quanta language.

    Returns:
    str: The executable Python code generated from the input Quanta code.
    """
    tokens = lexer(input)
    ast = parser(tokens)
    executableCode = codeGenerator(ast)
    return executableCode

def runner(input):
    """
    This function executes the input Python code.

    Parameters:
    input (str): The Python code to be executed.
    """
    exec(input)

def main():
    """
    This function reads the Quanta code from a file named 'index.quanta' in the current working directory,
    compiles it into executable Python code, and then runs the Python code.
    """
    path = os.getcwd()
    with open(os.path.join(path, "index.quanta"), 'r') as file:
        code = file.read()

    python_code = compiler(code)
    exec(python_code, globals())

if __name__ == "__main__":
    main()