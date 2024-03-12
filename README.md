Here we solve the cutting stock problem propused by AIMMS in https://download.aimms.com/aimms/download/manuals/AIMMS3OM_CuttingStock.pdf using a column generation algorithm, which we have developed using Pyomo library of Python.

In this problem, we have 1000 cm lenght bars that we need to cut into smaller portions (450 cm, 360 cm, 310 cm and 140 cm lenght bars) to satisfy the customer demand. The objective is to minimize the total number of raw bars required to make the final products. You can find the input data in data/data_0_cutting.json.

In real problems, the number of cutting patterns (columns in the original problem that represent how many final products are cut from a single raw bar) can be extremely large. Then we propose to:

* start with a reduced number of cutting patterns. Here, we create four patterns (one per final product) where each pattern contains the maximum number of a single final product that can be cut from the raw bar.
* solve two auxiliary problems that allow us to find new patterns that improve the initial solution.
	* First we solve the master problem (which is equal to the original problem except because all the variables are reals) using the initial set of cutting patterns and we get the shadows prices for the demand constraints.
	* After that, we use these shadow prices in a subproblem to find a new cutting pattern that improves the master problem objective function.
	* A cutting pattern found by the subproblem will be added to the master problem in the following iteration if 1 - the subproblem objective fuction is less than zero or equivalentely, if the reduced cost for this pattern or column in the master problem is negative, so that it reduces the number of bars that we need to satisfy the demand.
	* Then, we solve the master problem again with the new set of patterns and after we solve the subproblem until all the optimum cutting patterns are in the master problem.
* finally, we solve the orignal problem to get the integer solution.

To try the algorithm, you can use solve_column_generation_algorithms.py. Here you can see that we use four initial patterns and we generate two more to get the optimial solution.

* The objective function for the master problem with four patterns is 515.309527.
* Then we find a new pattern that improves the master problem solution (P5). The subproblem objective function for this pattern is 1.28571428. So the master problem objective function will be reduced in 0.28571428 per bar that we cut using P5 pattern.
* When we include P5 in the master problem, the solution shows that 105.5 bars should be cut using P5 and the objective function will be 485.1666705 (= 515.309527 - 0.28571428 * 105.5).
* Then we find a new pattern that improves the master problem solution (P6). The subproblem objective function for this pattern is 1.16666666. So the master problem objective function will be reduced in 0.16666666 per bar that we cut using P6 pattern.
* When we include P6 in the master problem, the solution shows that 197.5 bars should be cut using P6 and the objective function will be 452.2500051 (= 485.1666705 - 0.16666666 * 197.5).
* Then we do not find any additional pattern that improve the master problem solution.
* So we solve the original problem with the previuos patterns and we get that 453 is the minimum numbers of bars to use to satisfy the demand.

This algorithm can be use in paper, textile and metal industries to get smaller portions from a raw bar or a bidimensional part. It also can be use to calculate new working shifts in an employee shift scheduling problem.
 








