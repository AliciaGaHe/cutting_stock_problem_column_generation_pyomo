import logging
import json


logging.basicConfig(level=logging.INFO)


def load_input_data(file):
    """load input data from a json file and return a dictionary that pyomo understands"""
    # Open the json file
    f = open(file)

    # Load the data in a dictionary
    input_data = json.load(f)

    # Close the json file
    f.close()

    # Create a dictionary that pyomo understands
    input_data_pyomo_dict_format = {
        None: {
            "sProducts": {None: input_data["sProducts"]},
            "pProductSize": input_data["pProductSize"],
            "pProductDemand": input_data["pProductDemand"],
            "pBarSize": {None: input_data["pBarSize"]}
        }
    }

    return input_data_pyomo_dict_format


def generate_initial_patterns(input_data):
    """Generate an initial set of patterns and add it to the input data"""
    # One cutting pattern per final product
    input_data[None]["sCuttingPatterns"] = {
        None: [
            "P" + str(index + 1)
            for index in range(len(input_data[None]["sProducts"][None]))
        ]
    }

    # We cut the maximum number of one final product in each pattern
    input_data[None]["pNumberProductsPerCuttingPattern"] = {
        (pattern, product): int(input_data[None]["pBarSize"][None]/input_data[None]["pProductSize"][product])
        for pattern in input_data[None]["sCuttingPatterns"][None]
        for product in input_data[None]["sProducts"][None]
        if input_data[None]["sCuttingPatterns"][None].index(pattern) == input_data[None]["sProducts"][None].index(product)
    }

    # Available combinations of patterns and products
    input_data[None]["sCuttingPatterns_sProducts"] = {
        None: list(input_data[None]["pNumberProductsPerCuttingPattern"].keys())
    }

    # Element to continue generating new cutting patterns or not
    input_data[None]["stop_new_patterns_generation"] = {None: 0}

    return input_data
