# Import from libraries
import logging
from pyomo.environ import (
    AbstractModel,
    Suffix,
    Set,
    Param,
    Var,
    Constraint,
    Objective,
    NonNegativeIntegers,
    maximize,
    SolverFactory,
    value
)


logging.basicConfig(level=logging.INFO)


def create_sub_problem_model():
    """problem that proposes new cutting patterns to improve the master problem outputs"""
    # Create an abstract model
    model = AbstractModel()

    # Create sets
    # Products
    model.sProducts = Set()

    # Create parameters
    # Size for each product
    model.pProductSize = Param(model.sProducts, mutable=True)
    # Size for the bar
    model.pBarSize = Param(mutable=True)
    # Shadow price from the master problem for each product
    model.pShadowPrices = Param(model.sProducts, mutable=True)

    # Create the decision variable
    # Number of products to include in the new pattern
    model.vNumberProducts = Var(model.sProducts, domain=NonNegativeIntegers, initialize=0)

    # Create constraints
    # Bar size satisfaction
    def c01_bar_size_satisfaction(model):
        """bar size satisfaction"""
        return (
                sum(
                    model.pProductSize[iProduct] *
                    model.vNumberProducts[iProduct]
                    for iProduct in model.sProducts
                )
                <= value(model.pBarSize)
        )

    # Create the objective function
    # We want to maximize the value in the master problem for the new cutting pattern that we are generating
    def obj_expression(model):
        """total reduction of mater problem objective function per new cutting pattern that we are generating"""
        return (
                sum(
                    model.pShadowPrices[iProduct] *
                    model.vNumberProducts[iProduct]
                    for iProduct in model.sProducts
                )
        )

    # Active constraints
    model.c01_bar_size_satisfaction = Constraint(
        rule=c01_bar_size_satisfaction
    )

    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=maximize)

    # Return the model
    return model

def solve_sub_problem(input_data):
    """solve the sub problem and add results to the input data"""
    # Create the model
    model = create_sub_problem_model()

    # Create the instance to solve
    instance = model.create_instance(input_data)

    # Solve the instance using 'cbc' solver
    opt = SolverFactory("cbc")
    results = opt.solve(instance)

    if instance.f_obj() > 1:

        logging.info("we find a new pattern")

        # Number for the new cutting pattern
        num_new_cutting_patterns = len(input_data[None]["sCuttingPatterns"][None]) + 1

        # Add the new cutting pattern to sCuttingPatterns
        input_data[None]["sCuttingPatterns"][None].append("P" + str(num_new_cutting_patterns))

        # Add the new cutting pattern information to pNumberProductsPerCuttingPattern
        dict_num_products_new_pattern = {
            ("P" + str(num_new_cutting_patterns), iProduct): value(instance.vNumberProducts[iProduct])
            for iProduct in instance.sProducts
            if value(instance.vNumberProducts[iProduct]) > 0
        }

        input_data[None]["pNumberProductsPerCuttingPattern"].update(dict_num_products_new_pattern)

        # Add the new cutting pattern information to sCuttingPatterns_sProducts
        indexes_dict_num_products_new_pattern = list(dict_num_products_new_pattern.keys())

        input_data[None]["sCuttingPatterns_sProducts"][None] = (
                input_data[None]["sCuttingPatterns_sProducts"][None] + indexes_dict_num_products_new_pattern
        )

        # Value of the objective function for the sub_problem
        input_data[None]["objective_function_sub_problem"] = {None: instance.f_obj()}

    else:

        logging.info("we do not find a new pattern")

        # Stop generating new patterns
        input_data[None]["stop_new_patterns_generation"][None] = 1

        # Value of the objective function for the sub_problem
        input_data[None]["objective_function_sub_problem"][None] = {None: instance.f_obj()}

    return input_data
