# Import from libraries
import logging

# Import from files
from data_load_and_transformation.load_input_data_and_generate_initial_solution import load_input_data
from data_load_and_transformation.load_input_data_and_generate_initial_solution import generate_initial_patterns
from master_problem.master_problem_formulation_and_solver import solve_relax_master_problem
from master_problem.master_problem_formulation_and_solver import solve_non_relax_master_problem
from sub_problem.sub_problem_formulation_and_solver import solve_sub_problem


logging.basicConfig(level=logging.INFO)

input_data_file = "./data/data_0_cutting.json"

# Load input data
input_data = load_input_data(input_data_file)
logging.info("review input_data")
logging.info(input_data)

# Generate initial cutting patterns
input_data_updated = generate_initial_patterns(input_data)
logging.info("review initial patterns generated")
logging.info(input_data_updated)

algorithm_iteration = 0

# Find new patterns solving relax mater problem + sub_problem
while input_data_updated[None]["stop_new_patterns_generation"][None] == 0:

    algorithm_iteration += 1
    logging.info("algorithm_iteration: " + str(algorithm_iteration))

    input_data_updated = solve_relax_master_problem(input_data_updated)
    logging.info("review output_relax_master_problem")
    logging.info(input_data_updated)

    input_data_updated = solve_sub_problem(input_data_updated)
    logging.info("review output_sub_problem")
    logging.info(input_data_updated)

# Find the final solution using the non relax master problem
logging.info("review output_non_relax_master_problem")
solve_non_relax_master_problem(input_data_updated)
