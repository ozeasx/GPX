#!/usr/bin/python
# Ozeas - ozeasx@gmail.com

import os
import sys
import multiprocessing
import argparse
from collections import defaultdict
import logging
import csv
from ga import GA
from tsp import TSPLIB
from gpx import GPX


# https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


# Argument parser
p = argparse.ArgumentParser(description="Genetic algorithm + GPX")

# Inicial population
p.add_argument("-p", help="Population size", type=int, default=100)
p.add_argument("-l", help="Load inicial population from file", type=str,
               default=None)
p.add_argument("-s", help="Save inicial population to file", type=str,
               default=None)
p.add_argument("-M", choices=['random', '2opt', 'nn', 'nn2opt'],
               default='random', help="Method to generate inicial population")
p.add_argument("-R", type=float, default=1.0,
               help="Ratio of inicial popopulation \
                     to be created with method M")

# Population restart
p.add_argument("-r", type=float, default=0,
               help="Percentage of population to be restarted with method S")
p.add_argument("-S", choices=['random', '2opt', 'nn', 'nn2opt'],
               default='random', help="Method to restart population")

# Selection
multual = p.add_mutually_exclusive_group()
multual.add_argument("-k", help="Tournament size", type=int)
multual.add_argument("-P", help="Pairwise Recombination", type=str2bool)
multual.add_argument("-K", help="Selection pressure (Ranking selection)",
                     type=float)

# Crossover
p.add_argument("-c", help="Crossover probability", type=float, default=0)

# Tests
p.add_argument("-t1", help="Test 1", type=str2bool, default=True)
p.add_argument("-t2", help="Test 2", type=str2bool, default=False)
p.add_argument("-t3", help="Test 3", type=str2bool, default=False)

# Fusion
p.add_argument("-F", help="Apply fusion", type=str2bool, default=True)
p.add_argument("-t1f", help="Test 1 for Fusion", type=str2bool, default=True)
p.add_argument("-t2f", help="Test 2 for Fusion", type=str2bool, default=False)
p.add_argument("-t3f", help="Test 3 for Fusion", type=str2bool, default=False)

# Explore
p.add_argument("-E", help="Explore 4 children", type=str2bool, default=True)

# Relaxed GPX
p.add_argument("-L", help="Relaxed GPX", type=str2bool, default=False)

# Mutation
p.add_argument("-m", help="Mutation probability", type=float,
               default=0)
p.add_argument("-t", help="Mutation operator", default='2opt',
               choices=['2opt', 'nn', 'nn2opt'])

# GA
p.add_argument("-e", help="Elitism number", type=int, default=0)
p.add_argument("-g", help="Generation limit", type=int, default=100)
p.add_argument("-G", help="Fitness ploting", type=str2bool, default=False)
p.add_argument("-n", help="Number of iterations (paralelism will be used)",
               type=int, default=1)

# Report
p.add_argument("-o", help="Directory to generate file reports", type=str,
               default=None)

# Instance
p.add_argument("I", help="TSP instance file", type=str)

# Parser
args = p.parse_args()

# Assert arguments
if not args.s:
    if all(v is None for v in (args.k, args.K, args.P)):
        print("One selection method (k, K, P) must be provided")
        exit()
if args.k is not None:
    assert 2 <= args.k <= args.p, "Invalid tournament size"
if args.K is not None:
    assert 1 < args.K <= 2, "Selection pressure must be in (1,2] interval"
assert args.p > 0 and not args.p % 2, "Invalid population size. Must be even" \
                                      " and greater than 0"
assert 0 <= args.r <= 1, "Restart percentage must be in [0,1] interval"
assert 0 < args.R <= 1, "Ratio must be in (0,1] interval"
assert 0 <= args.e <= args.p, "Invalid number of elite individuals"
assert 0 <= args.c <= 1, "Crossover probability must be in [0,1] interval"
assert 0 <= args.m <= 1, "Mutation probability must be in [0,1] interval"
assert args.g > 0, "Invalid generation limit"
assert 0 < args.n, "Invalid iteration limit"
assert os.path.isfile(args.I), "File " + args.I + " doesn't exist"
if args.l:
    assert os.path.isfile(args.l), "File " + args.l + " doesn't exist"

# Instance
instance = TSPLIB(args.I)

# Create directory to report data
if args.o:
    log_dir = args.o
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

# Stdout logging
stdout_handler = logging.StreamHandler(sys.stdout)
format = logging.Formatter('%(message)s')
stdout_handler.setFormatter(format)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# Plot instance
if args.n == 1 and args.G:
    from streamplot import PlotManager
    plt_mgr = PlotManager(title="Fitness evolution")


# Function to call each ga run
def run_ga(id):
    # Also log to file
    if args.o:
        file_handler = logging.FileHandler(log_dir + "/report%i.log"
                                                     % (id + 1))
        file_handler.setFormatter(format)
        logger.addHandler(file_handler)

    # Summary
    logger.info("------------------------------GA Settings------------------")
    logger.info("Initial population: %i", args.p)
    logger.info("Initial population method: %s", args.M)
    logger.info("Initial population ratio: %i", args.R)
    logger.info("Population restart method: %s", args.S)
    logger.info("Population restart ratio: %f", args.r)
    logger.info("Elitism: %i", args.e)
    if args.k is not None:
        logger.info("Tournament selection size: %i", args.k)
    elif args.K is not None:
        logger.info("Selection pressure (Ranking): %f", args.K)
    elif args.P:
        logger.info("Pairwise selection")
    logger.info("Crossover probability: %f", args.c)
    logger.info("Mutation probability: %f", args.m)
    logger.info("Mutation operator: %s", args.t)
    logger.info("Fusion: %s", args.F)
    logger.info("Explore: %s", args.E)
    logger.info("Generation limit: %i", args.g)
    logger.info("Instance: %s", args.I)
    logger.info("Dimension: %i", instance.dimension)
    logger.info("Iteration: %i/%i", id + 1, args.n)

    # Stats
    avg_fitness = defaultdict(list)
    best_fitness = defaultdict(list)
    best_solution = dict()
    counters = defaultdict(list)
    timers = defaultdict(list)

    # Crossover operator
    gpx = GPX(instance)

    # Define which tests will be applied
    gpx.test_1 = args.t1
    gpx.test_2 = args.t2
    gpx.test_3 = args.t3

    # Fusion, explore and relax switches
    gpx.fusion_on = args.F
    gpx.explore_on = args.E
    gpx.relax = args.L

    # Fusion tests
    gpx.test_1_fusion = args.t1f
    gpx.test_2_fusion = args.t2f
    gpx.test_3_fusion = args.t3f

    # GA Instance
    ga = GA(instance, gpx, args.e)

    # Generate inicial population
    ga.gen_pop(args.p, args.M, args.R, args.l, args.s)

    # Fisrt population evaluation
    ga.evaluate()

    # Begin GA
    while ga.generation < args.g:
        # Update plot
        if args.n == 1 and args.G:
            plt_mgr.add(x=ga.generation, y=ga.counters['avg_fit'][-1],
                        name='Average fitness')
            plt_mgr.add(x=ga.generation, y=ga.counters['best_fit'][-1],
                        name='Best fitness')
            plt_mgr.add(x=ga.generation, y=ga.counters['cross'][-1],
                        name='Crossover')
            plt_mgr.update()

        # Logging
        avg_fitness[ga.generation].append(ga.counters['avg_fit'][-1])
        best_fitness[ga.generation].append(ga.counters['best_fit'][-1])

        # Population restart
        if args.r:
            ga.restart_pop(args.r, args.S)

        # Selection
        if args.k is not None:
            ga.tournament_selection(args.k)
        elif args.K is not None:
            ga.rank_selection(args.K)
        elif args.P:
            ga.pairwise_selection()

        # Recombination
        if args.c:
            ga.recombine(args.c, args.P)

        # Mutation
        if args.m:
            ga.mutate(args.m, args.t)

        # Evaluation
        ga.evaluate()

        # Generation info
        ga.print_info()

    # Final report
    ga.report()

    # Close ploting
    if args.n == 1 and args.G:
        plt_mgr.close()

    # Best solution
    best_solution[id] = ga.best_solution

    # Calc improvement
    parents_dist = float(gpx.counters['parents_dist'])
    children_dist = float(gpx.counters['children_dist'])
    improvement = 0
    if parents_dist != 0:
        improvement = (1 - children_dist / parents_dist) * 100

    # Counters
    counters[id].extend([gpx.counters['feasible_1'],
                         gpx.counters['feasible_2'],
                         gpx.counters['feasible_3'], gpx.counters['feasible'],
                         gpx.counters['infeasible'], gpx.counters['fusion_1'],
                         gpx.counters['fusion_2'], gpx.counters['fusion_3'],
                         gpx.counters['fusion'], gpx.counters['unsolved'],
                         sum(ga.counters['cross']), gpx.counters['improved'],
                         gpx.counters['failed_0'], gpx.counters['failed_1'],
                         gpx.counters['failed_2'], gpx.counters['failed_3'],
                         gpx.counters['failed'], gpx.counters['inf_tour_0'],
                         gpx.counters['inf_tour_1'], gpx.counters['inf_tour'],
                         improvement, sum(ga.counters['mut'])])

    # Timers
    timers[id].extend([sum(ga.timers['total']), sum(ga.timers['population']),
                       sum(ga.timers['evaluation']),
                       sum(ga.timers['tournament']),
                       sum(ga.timers['recombination']),
                       sum(gpx.timers['g_star']),
                       sum(gpx.timers['partitioning']),
                       sum(gpx.timers['simple_graph']),
                       sum(gpx.timers['simple_graph_f']),
                       sum(gpx.timers['classification']),
                       sum(gpx.timers['fusion']), sum(gpx.timers['build']),
                       sum(ga.timers['mutation']),
                       sum(ga.timers['restart_pop'])])
    # Return data
    return avg_fitness, best_fitness, best_solution, counters, timers


# Execution decision
if args.n > 1:
    # Execute all runs
    pool = multiprocessing.Pool(multiprocessing.cpu_count()-1)
    result = pool.map(run_ga, range(args.n))
    pool.close()
    pool.join()
else:
    result = run_ga(0)
    instance.best_solution = result[2][0]

# Consolidate data
if args.n > 1:

    # Best solution found
    best_solution = None

    for __, __, best, __, __ in result:
        for key, value in best.items():
            if not best_solution:
                best_solution = value
            elif value.fitness > best_solution.fitness:
                best_solution = value

    # Write best solution
    instance.best_solution = best_solution

    # Write stats to files
    if args.o:

        avg_fitness = defaultdict(list)
        best_fitness = defaultdict(list)
        counters = defaultdict(list)
        timers = defaultdict(list)

        # Average, best, counters and timers
        for a, b, _, c, t in result:
            for key, value in a.items():
                avg_fitness[key].extend(value)
            for key, value in b.items():
                best_fitness[key].extend(value)
            for key, value in c.items():
                counters[key].extend(value)
            for key, value in t.items():
                timers[key].extend(value)

        # Write data
        with open(log_dir + "/avg_fitness.csv", 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key in sorted(avg_fitness):
                writer.writerow(avg_fitness[key])

        with open(log_dir + "/best_fitness.csv", 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key in sorted(best_fitness):
                writer.writerow(best_fitness[key])

        with open(log_dir + "/parametrization.out", 'w') as file:
            print >> file, str(vars(args)).strip("{}")

        with open(log_dir + "/best_tour_found.out", 'w') as file:
            print >> file, ",".join(map(str, best_solution.tour))

        with open(log_dir + "/best_known_tour.out", 'w') as file:
            print >> file, ",".join(map(str, best_solution.tour))

        with open(log_dir + "/counters.csv", 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Feasible_1", "Feasible_2", "Feasible_3",
                             "Feasible", "Infeasible", "Fusion_1", "Fusion_2",
                             "Fusion_3", "Fusion", "Unsolved", "Crossover",
                             "Improved", "Failed_0", "Failed_1", "Failed_2",
                             "Failed_3", "Failed", "Infeasible_tour_1",
                             "Infeasible_tour_2", "Infeasible_tours",
                             "Improvement", "Mutation"])
            for key in sorted(counters):
                writer.writerow(counters[key])

        with open(log_dir + "/timers.csv", 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Total", "Population", "Evaluation", "Tournament",
                             "Recombination", "G_Star", "Partitioning",
                             "Simple_graph", "Simple_graph_fusion",
                             "Classification", "Fusion", "Build", "Mutation",
                             "Pop_restart"])
            for key in sorted(timers):
                writer.writerow(timers[key])
