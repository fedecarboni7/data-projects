from schema import Schema, SchemaError
#https://www.andrewvillazon.com/validate-yaml-python-schema/
config_schema = Schema({
    "api": {
        "token": str
    }
})