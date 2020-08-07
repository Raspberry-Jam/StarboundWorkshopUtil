import os
import json
import jsonschema

working_dir = os.path.dirname(os.path.realpath(__file__))
schema = {
    "allOf": [{
        "type": "object",
        "properties": {
            "game_dir": {"type": "string"}
        }
    }, {
        "anyOf": [
            {"properties": {"game_dir": {"$ref": "#/definitions/nonEmptyString"}}}
        ]
    }],
    "definitions": {
        "nonEmptyString": {
            "type": "string",
            "minLength": 1
        }
    }
}
blank_config = """{
    "game_dir": ""
}"""


# Create and validate config based on a pre-defined schema
class Config:
    # Get the path to the config.json, ensure it exists, load it using the json library, 
    # validate it, and instantiate self.config using it.
    def __init__(self, config_path):
        self.__config_path = config_path
        self.__check_for_file()
        temp = json.load(open(self.__config_path))
        self.config = self.__validate_config(temp)

    # Check if the file exists on disk, and if not, warn the user, create a new one and exit.
    def __check_for_file(self):
        if not os.path.isfile(self.__config_path):
            print("File doesn't exist. Creating a new empty config file now.")
            os.mknod(self.__config_path)
            config_file = open(self.__config_path, 'w')
            config_file.write(blank_config)
            config_file.close()
            exit(1)

    # Ensure that rules defined by the pre-defined schema are followed by the loaded config file.
    # If not, exit.
    def __validate_config(self, json_data):
        try:
            jsonschema.validate(instance=json_data, schema=schema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            exit(1)
        return json_data


if __name__ == '__main__':
    Config(f'{working_dir}/config.json')
