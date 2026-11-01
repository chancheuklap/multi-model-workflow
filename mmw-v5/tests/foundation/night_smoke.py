import json


def greet(name, config_path):
    name = name.strip()
    if not name:
        raise ValueError('name must not be blank')
    with open(config_path, encoding='utf-8') as config_file:
        config = json.load(config_file)
    prefix = config.get('prefix') if isinstance(config, dict) else None
    if not isinstance(prefix, str) or not prefix.strip():
        raise ValueError('prefix must be a non-empty string')
    prefix = prefix.strip()
    return f'{prefix}, {name}!'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('name')
    args = parser.parse_args()
    try:
        greeting = greet(args.name, args.config)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(greeting)
