from schema import Schema, SchemaError, Optional
import yaml


#configuration = yaml.safe_load("""
#input_file_path: ./tests/assets/test_boolean.csv
#output_file_path: ./tests/assets/result/test_boolean.csv
#proxy: http://198.20.180.218:3128
#regex: 
#    - 'object and pass in our loaded YAM'
#    - 'objecto|manzana'
#    - 'obje..'
#""")

config_schema = Schema({
  "input_file_path": str,
  "output_file_path": str,
  Optional("proxy"): str,
  "regex": [str]
})

# TODO
def is_valid_schema(schema):
    try:
        config_schema.validate(schema)
        return True
    except SchemaError as se:
        print(se)
        return False

def validate_schemas(schemas):
    for schema in schemas:
        if not is_valid_schema(schema):
            return False
    return True
