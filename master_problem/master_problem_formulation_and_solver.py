# Import from libraries
import logging
import pandas as pd
from pyomo.environ import (
    AbstractModel,
    Suffix,
    Set,
    Param,
    Var,
    Constraint,
    Objective,
    NonNegativeReals,
    NonNegativeIntegers,
    minimize,
    SolverFactory,
    value
)


logging.basicConfig(level=logging.INFO)


def create_master_problem_model(relax_problem=True):
    """problem that decides how many cutting patterns to use given a set of cutting patterns"""
    # Create an abstract model
    model = AbstractModel()

    # Import constraint dual information for sensibility analysis
    model.dual = Suffix(direction=Suffix.IMPORT)

    # Create sets
    # Cutting patterns
    model.sCuttingPatterns = Set()
    # Products
    model.sProducts = Set()
    # Available combinations of patterns and products
    model.sCuttingPatterns_sProducts = Set(dimen=2)

    # Create parameters
    # Size for each product
    model.pProductSize = Param(model.sProducts, mutable=True)
    # Demand for each product
    model.pProductDemand = Param(model.sProducts, mutable=True)
    # Number of products per cutting pattern
    model.pNumberProductsPerCuttingPattern = Param(model.sCuttingPatterns_sProducts, mutable=True)

    # Create the variable type
    # Real if we are working with the relax problem and integer otherwise
    if relax_problem:
        decision_variable_type = NonNegativeReals
    else:
        decision_variable_type = NonNegativeIntegers

    # Create the decision variable
    # Number of cutting patterns to produce
    model.vNumberCuttingPatterns = Var(model.sCuttingPatterns, domain=decision_variable_type, initialize=0)

    # Create constraints
    # Demand satisfaction for each product
    def c01_demand_satisfaction(model, iProduct):
        """demand satisfaction for each product"""
        return (
                sum(
                    model.pNumberProductsPerCuttingPattern[iPattern, iProduct] *
                    model.vNumberCuttingPatterns[iPattern]
                    for iPattern in model.sCuttingPatterns
                    if (iPattern, iProduct) in model.sCuttingPatterns_sProducts
                )
                >= model.pProductDemand[iProduct]
        )

    # Create the objective function
    # We want to minimize the total number of cutting patterns (or bars) in use
    def obj_expression(model):
        """minimum number of cutting patterns in use"""
        return (
                sum(
                    model.vNumberCuttingPatterns[iPattern]
                    for iPattern in model.sCuttingPatterns
                )
        )

    # Active constraints
    model.c01_demand_satisfaction = Constraint(
        model.sProducts, rule=c01_demand_satisfaction
    )

    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)

    # Return the model
    return model


def solve_relax_master_problem(input_data):
    """solve relax master problem and add shadow prices to the input data"""
    # Create the model
    model = create_master_problem_model(relax_problem=True)

    # Create the instance to solve
    instance = model.create_instance(input_data)

    # Solve the instance using 'cbc' solver
    opt = SolverFactory("cbc")
    results = opt.solve(instance)

    # Shadow prices for the products
    shadow_prices = [
        value(instance.dual[instance.c01_demand_satisfaction[product]])
        for product in instance.sProducts
    ]

    # Update input data with the solution for the master problem
    input_data[None]["decision_variables_master_problem"] = {
        iPattern: value(instance.vNumberCuttingPatterns[iPattern])
        for iPattern in instance.sCuttingPatterns
        if value(instance.vNumberCuttingPatterns[iPattern]) > 0
    }

    # Value of the objective function for the master problem
    input_data[None]["objective_function_master_problem"] = {None: instance.f_obj()}

    # Update input data with the shadow prices
    input_data[None]["pShadowPrices"] = {
        input_data[None]["sProducts"][None][i]: shadow_prices[i] for i in range(len(shadow_prices))
    }

    return input_data


def solve_non_relax_master_problem(input_data):
    """solve the problem and print results"""
    # Create the model
    model = create_master_problem_model(relax_problem=False)

    # Create the instance to solve
    instance = model.create_instance(input_data)

    # Solve the instance using 'cbc' solver
    opt = SolverFactory("cbc")
    results = opt.solve(instance)

    # Print the most relevant outputs
    print("\n")
    print("Total number of bars that we need:", instance.f_obj())

    print("\n")
    print("Number of patterns that we need")
    dict_number_cutting_patterns = {
        iPattern: value(instance.vNumberCuttingPatterns[iPattern])
        for iPattern in instance.sCuttingPatterns
        if value(instance.vNumberCuttingPatterns[iPattern]) > 0
    }

    df_number_cutting_patterns = pd.DataFrame.from_dict(
        dict_number_cutting_patterns, orient="index", columns=["Quantity"]
    ).reset_index(names=["Pattern"])

    print(df_number_cutting_patterns)

    print("\n")
    print("Product mix per pattern")
    dict_product_mix_per_pattern = {
        k: v for k, v in input_data[None]["pNumberProductsPerCuttingPattern"].items()
        if k[0] in list(dict_number_cutting_patterns.keys())
    }

    df_dict_product_mix_per_pattern = pd.DataFrame(dict_product_mix_per_pattern.values(),
                                                   index=pd.MultiIndex.from_tuples(dict_product_mix_per_pattern.keys()),
                                                   columns=["Quantity"]
                                                   ).reset_index(names=["Pattern", "Product"])
    print(df_dict_product_mix_per_pattern)

    print("\n")
    print("Check demand satisfaction")
    df_dict_products_demand = pd.DataFrame.from_dict(
        input_data[None]["pProductDemand"], orient="index", columns=["Demand"]
    ).reset_index(names=["Product"])

    df_total_products_produced = df_dict_product_mix_per_pattern.merge(
        df_number_cutting_patterns, on="Pattern", suffixes=("_per_product", "_per_pattern")
    )
    df_total_products_produced["Total_produced"] = (
            df_total_products_produced["Quantity_per_product"] * df_total_products_produced["Quantity_per_pattern"]
    )
    df_total_products_produced = df_total_products_produced.groupby("Product")["Total_produced"].sum().reset_index()

    df_check_demand_satisfaction = df_dict_products_demand.merge(df_total_products_produced, on="Product")
    print(df_check_demand_satisfaction)

    print("\n")
    print("Check bar size satisfaction per all patterns")
    df_dict_products_size = pd.DataFrame.from_dict(
        input_data[None]["pProductSize"], orient="index", columns=["Size"]
    ).reset_index(names=["Product"])

    df_check_bar_size_used = df_dict_product_mix_per_pattern.merge(df_dict_products_size, on="Product")
    df_check_bar_size_used["Total_size_used"] = df_check_bar_size_used["Quantity"] * df_check_bar_size_used["Size"]
    df_check_bar_size_used = df_check_bar_size_used.groupby("Pattern")["Total_size_used"].sum().reset_index()

    df_check_bar_size_used["Bar_size"] = input_data[None]["pBarSize"][None]

    df_check_bar_size_used = df_check_bar_size_used.iloc[:, [0, 2, 1]]

    print(df_check_bar_size_used)
