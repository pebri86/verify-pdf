from pydantic import BaseModel

def to_camel(string):
    init, *temp = string.split('_')
    res = ''.join([init.lower(), *map(str.title, temp)])

    return res

class MyModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
