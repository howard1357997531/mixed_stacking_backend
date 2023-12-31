import math
import random
import numpy as np
import time
from multiprocessing import Pool

# Set a fixed random seed for reproducibility
random_seed = 42
np.random.seed(random_seed)
INFEASIBLE = 100000


def generateInstances(N = 20, m = 10, V = (100,100)):
    def ur(lb, ub):
        # u.r. is an abbreviation of "uniformly random". [Martello (1995)]
        value = random.uniform(lb, ub)
        return int(value) if value >= 1 else 1
    L, W = V
    p = []; q = []
    for i in range(N):
        p.append(ur(1/6*L, 1/4*L))
        q.append(ur(1/6*W, 1/4*W))
    L = [L]*m
    W = [W]*m
    return range(N), range(m), p, q, L, W

def generateInputs(N, m, V):
    N, M, p,q, L,W =generateInstances(N, m, V)
    inputs = {'v':list(zip(p, q)), 'V':list(zip(L, W))}
    return inputs


class Bin():
    def __init__(self, V, verbose=False):
        self.dimensions = V
        self.EMSs = [[np.array((0,0)), np.array(V)]]
        self.load_items = []
        
        if verbose:
            print('Init EMSs:',self.EMSs)
    
    def __getitem__(self, index):
        return self.EMSs[index]
    
    def __len__(self):
        return len(self.EMSs)
    
    def update(self, box, selected_EMS, min_vol = 1, min_dim = 1, verbose=False):

        # 1. place box in a EMS
        boxToPlace = np.array(box)
        selected_min = np.array(selected_EMS[0])
        ems = [selected_min, selected_min + boxToPlace]
        self.load_items.append(ems)
        
        if verbose:
            print('------------\n*Place Box*:\nEMS:', list(map(tuple, ems)))
        
        # 2. Generate new EMSs resulting from the intersection of the box
        for EMS in self.EMSs.copy():
            if self.overlapped(ems, EMS):
                
                # eliminate overlapped EMS
                self.eliminate(EMS)
                
                if verbose:
                    print('\n*Elimination*:\nRemove overlapped EMS:',list(map(tuple, EMS)),'\nEMSs left:', list(map( lambda x : list(map(tuple,x)), self.EMSs)))
                
                # six new EMSs in 3 dimensions
                x1, y1 = EMS[0]; x2, y2 = EMS[1]
                x3, y3 = ems[0]; x4, y4 = ems[1]

                # Calculate the area on top of the box
                box_area = (x4 - x3) * (y4 - y3)

                # Calculate the additional area to consider (18% more than the box area)
                extra_area = 0.14 * box_area

                # Calculate the additional length to add to each side of the box in the XY plane
                extra_length = np.sqrt(extra_area) / 2  # Divide by 2 to add half the extra length to each side

                # Apply constraints to limit the coordinates within the container boundaries
                new_x3 = max(x3 - extra_length, x1)
                new_y3 = max(y3 - extra_length, y1)
                new_x4 = min(x4 + extra_length, x2)
                new_y4 = min(y4 + extra_length, y2)

                new_EMSs = [
                [np.array((x1, y1)), np.array((x3, y2))], # left of box
                [np.array((x4, y1)), np.array((x2, y2))], # right of box
                [np.array((x1, y1)), np.array((x2, y3))], #front of box
                [np.array((x1, y4)), np.array((x2, y2))] # back of box
                # [np.array((new_x3, new_y3, z4)), np.array((new_x4, new_y4, z2))], # top of box
                # [np.array((x1, y1, z1)), np.array((x2, y2, z3))] # down of box
                ]
            
                for new_EMS in new_EMSs:
                    new_box = new_EMS[1] - new_EMS[0]
                    isValid = True
                    
                    if verbose:
                        print('\n*New*\nEMS:', list(map(tuple, new_EMS)))

                    # 3. Eliminate new EMSs which are totally inscribed by other EMSs
                    for other_EMS in self.EMSs:
                        if self.inscribed(new_EMS, other_EMS):
                            isValid = False
                            if verbose:
                                print('-> Totally inscribed by:', list(map(tuple, other_EMS)))
                            
                    # 4. Do not add new EMS smaller than the volume of remaining boxes
                    if np.min(new_box) < min_dim:
                        isValid = False
                        if verbose:
                            print('-> Dimension too small.')
                        
                    # 5. Do not add new EMS having smaller dimension of the smallest dimension of remaining boxes
                    if np.product(new_box) < min_vol:
                        isValid = False
                        if verbose:
                            print('-> Volumne too small.')

                    if isValid:
                        self.EMSs.append(new_EMS)
                        if verbose:
                            print('-> Success\nAdd new EMS:', list(map(tuple, new_EMS)))

        if verbose:
            print('\nEnd:')
            print('EMSs:', list(map( lambda x : list(map(tuple,x)), self.EMSs)))
    
    def overlapped(self, ems, EMS):
        return np.all(ems[1] > EMS[0]) and np.all(ems[0] < EMS[1])
    
    def inscribed(self, ems, EMS):
        return np.all(EMS[0] <= ems[0]) and np.all(ems[1] <= EMS[1])
    
    def eliminate(self, ems):
        # numpy array can't compare directly
        ems = list(map(tuple, ems))    
        for index, EMS in enumerate(self.EMSs):
            if ems == list(map(tuple, EMS)):
                self.EMSs.pop(index)
                return
    
    def get_EMSs(self):
        return  list(map( lambda x : list(map(tuple,x)), self.EMSs))
    
    def load(self):
        return np.sum([ np.product(item[1] - item[0]) for item in self.load_items]) / np.product(self.dimensions)
    
class PlacementProcedure():
    def __init__(self, inputs, solution, verbose=False):
        self.Bins = [Bin(V) for V in inputs['V']]
        self.boxes = inputs['v']
        self.BPS = np.argsort(solution[:len(self.boxes)])
        self.VBO = solution[len(self.boxes):]
        self.num_opend_bins = 1
        
        self.verbose = verbose
        if self.verbose:
            print('------------------------------------------------------------------')
            print('|   Placement Procedure')
            print('|    -> Boxes:', self.boxes)
            print('|    -> Box Packing Sequence:', self.BPS)
            print('|    -> Vector of Box Orientations:', self.VBO)
            print('-------------------------------------------------------------------')
        
        self.infisible = False
        self.placement()
        
    
    def placement(self):
        items_sorted = [self.boxes[i] for i in self.BPS]
        # items_sorted = sorted(items_sorted, key=lambda box: np.product(box), reverse=True)

        # Box Selection
        for i, box in enumerate(items_sorted):
            if self.verbose:
                print('Select Box:', box)
                
            # Bin and EMS selection
            selected_bin = None
            selected_EMS = None
            for k in range(self.num_opend_bins):
                # select EMS using DFTRC-2
                EMS = self.DFTRC_2(box, k)

                # update selection if "packable"
                if EMS != None:
                    selected_bin = k
                    selected_EMS = EMS
                    break
            
            # Open new empty bin
            if selected_bin == None:
                self.num_opend_bins += 1
                selected_bin = self.num_opend_bins - 1
                if self.num_opend_bins > len(self.Bins):
                    self.infisible = True
                    
                    if self.verbose:
                        print('No more bin to open. [Infeasible]')
                    return
                    
                selected_EMS = self.Bins[selected_bin].EMSs[0] # origin of the new bin
                if self.verbose:
                    print('No available bin... open bin', selected_bin)
            
            if self.verbose:
                print('Select EMS:', list(map(tuple, selected_EMS)))
            
            # Box orientation selection
            BO = self.selecte_box_orientaion(self.VBO[i], box, selected_EMS)

            # elimination rule for different process
            min_vol, min_dim = self.elimination_rule(items_sorted[i+1:])
   
            # pack the box to the bin & update state information
            self.Bins[selected_bin].update(self.orient(box, BO), selected_EMS, min_vol, min_dim)

            if self.verbose:
                print('Add box to Bin',selected_bin)
                print(' -> EMSs:',self.Bins[selected_bin].get_EMSs())
                print('------------------------------------------------------------')
        if self.verbose:
            print('|')
            print('|     Number of used bins:',self.num_opend_bins)
            print('|')
            print('------------------------------------------------------------')
    
    # Distance to the Front-Top-Right Corner
    def DFTRC_2(self, box, k):
        maxDist = -1
        selectedEMS = None

        for EMS in self.Bins[k].EMSs:
            D, W = self.Bins[k].dimensions
            for direction in [1,3]:
                d, w = self.orient(box, direction)
                if self.fitin((d, w), EMS):
                    x, y = EMS[0]
                    distance = np.power(D-x-d, 2) + np.power(W-y-w, 2)

                    if distance > maxDist:
                        maxDist = distance
                        selectedEMS = EMS
        return selectedEMS

    def orient(self, box, BO=1):
        d, w = box
        if   BO == 1: return (d, w)
        elif BO == 3: return (w, d)
        
    def selecte_box_orientaion(self, VBO, box, EMS):
        # feasible direction
        BOs = []
        for direction in [1,3]:
            if self.fitin(self.orient(box, direction), EMS):
                BOs.append(direction)
        selectedBO = BOs[math.ceil(VBO*len(BOs))-1]
        if self.verbose:
            print('Select VBO:', selectedBO,'  (BOs',BOs, ', vector', VBO,')')
        return selectedBO
         
    def fitin(self, box, EMS):
        return all(box_dim <= (EMS[1][d] - EMS[0][d]) for d, box_dim in enumerate(box))
    
    def elimination_rule(self, remaining_boxes):
        if len(remaining_boxes) == 0:
            return 0, 0
        
        min_vol = 999999999
        min_dim = 9999
        for box in remaining_boxes:
            # minimum dimension
            dim = np.min(box)
            if dim < min_dim:
                min_dim = dim    
            # minimum volume
            vol = np.product(box)
            if vol < min_vol:
                min_vol = vol
        return min_vol, min_dim
    
    def evaluate(self):
        if self.infisible:
            return INFEASIBLE
        leastLoad = 1
        for k in range(self.num_opend_bins):
            load = self.Bins[k].load()
            if load < leastLoad:
                leastLoad = load
        return self.num_opend_bins + leastLoad%1
    

class BRKGA():
    def __init__(self, inputs, num_generations = 200, num_individuals=120, num_elites = 12, num_mutants = 18, eliteCProb = 0.7, multiProcess = True):
        # Setting
        self.multiProcess = multiProcess
        # Input
        self.inputs = inputs
        self.N = len(inputs['v'])
        
        # Configuration
        self.num_generations = num_generations
        self.num_individuals = int(num_individuals)
        self.num_gene = 2*self.N
        
        self.num_elites = int(num_elites)
        self.num_mutants = int(num_mutants)
        self.eliteCProb = eliteCProb
        
        # Result
        self.used_bins = -1
        self.solution = None
        self.best_fitness = -1
        self.history = {
            'mean': [],
            'min': [],
            'time': []
        }
    
    def decoder(self, solution):
        return PlacementProcedure(self.inputs, solution).evaluate()

    def cal_fitness(self, population):
        if self.multiProcess:
            with Pool(8) as pool:
                fitness_list = pool.map(self.decoder, population)
        else:
            fitness_list = [PlacementProcedure(self.inputs, solution).evaluate() for solution in population]
        return fitness_list


    def partition(self, population, fitness_list):
        sorted_indexs = np.argsort(fitness_list)
        return population[sorted_indexs[:self.num_elites]], population[sorted_indexs[self.num_elites:]], np.array(fitness_list)[sorted_indexs[:self.num_elites]]
    
    def crossover(self, elite, non_elite):
        # chance to choose the gene from elite and non_elite for each gene
        return [elite[gene] if np.random.uniform(low=0.0, high=1.0) < self.eliteCProb else non_elite[gene] for gene in range(self.num_gene)]
    
    def mating(self, elites, non_elites):
        # biased selection of mating parents: 1 elite & 1 non_elite
        num_offspring = self.num_individuals - self.num_elites - self.num_mutants
        return [self.crossover(random.choice(elites), random.choice(non_elites)) for i in range(num_offspring)]
    
    def mutants(self):
        return np.random.uniform(low=0.0, high=1.0, size=(self.num_mutants, self.num_gene))
        
    def fit(self, patient = 4, verbose = False):
        # Initial population & fitness
        population = np.random.uniform(low=0.0, high=1.0, size=(self.num_individuals, self.num_gene))
        fitness_list = self.cal_fitness(population)
        
        if verbose:
            print('\nInitial Population:')
            print('  ->  shape:',population.shape)
            print('  ->  Best Fitness:',max(fitness_list))
            
        # best    
        best_fitness = np.min(fitness_list)
        best_solution = population[np.argmin(fitness_list)]
        self.history['min'].append(np.min(fitness_list))
        self.history['mean'].append(np.mean(fitness_list))
        
        
        # Repeat generations
        best_iter = 0
        for g in range(self.num_generations):
            
            start_time = time.time()  # Record the start time of this generation

            # early stopping
            if g - best_iter > patient:
                self.used_bins = math.floor(best_fitness)
                self.best_fitness = best_fitness
                self.solution = best_solution
                if verbose:
                    print('Early stop at iter', g, '(timeout)')
                return 'feasible'
            
            # Select elite group
            elites, non_elites, elite_fitness_list = self.partition(population, fitness_list)
            
            # Biased Mating & Crossover
            offsprings = self.mating(elites, non_elites)
            
            # Generate mutants
            mutants = self.mutants()

            # New Population & fitness
            offspring = np.concatenate((mutants,offsprings), axis=0)
            offspring_fitness_list = self.cal_fitness(offspring)
            
            population = np.concatenate((elites, mutants, offsprings), axis = 0)
            fitness_list = self.cal_fitness(population)

            # Update Best Fitness
            for fitness in fitness_list:
                if fitness < best_fitness:
                    best_iter = g
                    best_fitness = fitness
                    best_solution = population[np.argmin(fitness_list)]
            
            self.history['min'].append(np.min(fitness_list))
            self.history['mean'].append(np.mean(fitness_list))
            
            end_time = time.time()  # Record the end time of this generation
            elapsed_time = end_time - start_time  # Compute the elapsed time

            if verbose:
                num_offspring = self.num_individuals - self.num_elites - self.num_mutants
                print("Generation :", g)
                print("  Number of Elites :", self.num_elites)
                print("  Number of non-Elites :", len(non_elites))
                print("  Number of Children (Offspring):", num_offspring)
                print("  Number of Mutants:", self.num_mutants)
                print("  Best Fitness in this Generation:", np.min(fitness_list))
                print("  Average Fitness in this Generation:", np.mean(fitness_list))
                print("  Total Population Size:", self.num_individuals)
                print("  Crossover Probability:", self.eliteCProb)
                print("  Time Usage: {:.4f} seconds".format(elapsed_time))
            
        if verbose:
            print("Total Time Usage for all Generations: {:.4f} seconds".format(sum(self.history['time'])))
            
        self.used_bins = math.floor(best_fitness)
        self.best_fitness = best_fitness
        self.solution = best_solution
        return 'feasible'