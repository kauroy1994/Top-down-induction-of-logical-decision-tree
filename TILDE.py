from string import ascii_uppercase
from itertools import product
from copy import deepcopy
from Prover import Prover
from math import log2
from statistics import pvariance,mean


def entropy(bool_list):
    """computes entropy of list of 1's and 0's
    """

    if (not bool_list) or (len(bool_list) == 1):
        return 0
    p1 = sum(bool_list)/len(bool_list)
    p0 = 1-p1
    return (-1*p1*log2(p1)-1*p0*log2(p0))

class Node(object):
    """implements a tree node with
       information to expand the tree
    """

    #static variable to store target and target variables
    target = None
    typ = None
    score = None
    all_vars = list(ascii_uppercase)
    target_pred = ''


    @staticmethod
    def set_target_pred(bk):
        """sets the target predicate string
           and initializes types for variables
           based on mode specification
        """
    
    def __init__(self,facts,examples,bk,depth = 0,p="root",parent="root",var_types={}):
        """stores data for finding best condition
           background for restriction condition search
           parent to obtain branch info
           depth for tree depth control
           'p' position to know if root, left or right child
        """

        self.facts = facts
        self.examples = examples
        self.best_condition = ""
        self.parent = parent
        self.bk = bk
        self.depth = depth
        self.p = p
        self.var_types = var_types
        if parent == "root":
            Node.target_pred = Node.target+'('
            for functor in bk:
                if functor.split('(')[0] == Node.target:
                    mode = functor.split('(')[1][:-1].split(',')
                    n = len(mode)
                    for i in range(n):
                        variable = Node.all_vars[i]
                        typ = mode[i][1:]
                        Node.target_pred += variable+','
                        self.var_types[variable] = typ
                    break
            Node.target_pred = Node.target_pred[:-1]+')'

    def find_test_conditions(self,bk):
        """generate body literals in clause to score
           based on mode specifications in backgroud
        """

        test_conditions = []
        children_var_types = deepcopy(self.var_types)

        for functor in bk:

            #target mode specification skip
            if functor.split('(')[0] == Node.target:
                continue

            #for others generate literals based on mode
            pred = functor.split('(')[0]
            mode = functor.split('(')[1][:-1].split(',')
            n = len(mode)
            args = [[] for i in range(n)]
            for i in range(n):
                spec = mode[i]

                #if '+' then instantiate with seen var of same type
                if spec[0] == '+':
                    typ = spec[1:]

                    #assume var of similar type doesn't exist
                    exists = False
                    
                    for var in self.var_types:
                        if self.var_types[var] == typ:
                            exists = True
                            args[i].append(var)
                            children_var_types[var] = typ

                    #if no variable of that type in current clause
                    if not exists:

                        #assume variable of that type not seen in some previous mode
                        seen = False
                        for var in Node.all_vars:
                            if (var in children_var_types) and (children_var_types[var] == typ):
                                seen = True
                                args[i].append(var)
                                break

                        if not seen:
                            for new_var in Node.all_vars:
                                if new_var not in children_var_types:
                                    args[i].append(new_var)
                                    children_var_types[new_var] = typ
                                    break

                #if '-' instantiate with new var not in clause
                elif spec[0] == '-':
                    typ = spec[1:]

                    seen = False
                    for var in Node.all_vars:
                        if (var in children_var_types) and (children_var_types[var] == typ) and (var not in self.var_types):
                            seen = True
                            args[i].append(var)
                            break

                    if not seen:
                        for new_var in Node.all_vars:
                            if new_var not in children_var_types:
                                args[i].append(new_var)
                                children_var_types[new_var] = typ
                                break
                
                #if '#' collect all constants from facts at this position
                elif spec[0] == '#':
                    for fact in self.facts:
                        if fact.split('(')[0] == pred:
                            fact_args = fact.split('(')[1][:-1].split(',')
                            if fact_args[i] not in args[i]:
                                args[i].append(fact_args[i])

            combinations = list(product(*args))
            for combination in combinations:
                literal = pred+'('+','.join(list(combination))+')'
                if (literal not in test_conditions):
                    test_conditions.append((literal,functor))


        return ((test_conditions,children_var_types))

    def __repr__(self):
        """call to print outputs this
           this will be clause upto the node
        """

        clause = Node.target_pred+':-'
        if self.parent == "root":
            return (clause)
        pointer = self
        while pointer.parent!="root":
            if pointer.p == "left":
                clause += pointer.parent.best_condition+','
            else:
                clause += ""
            pointer = pointer.parent

        if clause[-1] == ',':
            clause = clause[:-1]
        return (clause)

    def score_clause(self,clause):
        """multiprocessing scoring function
        """
        
        examples = self.examples
        data = self.facts
        example_list = list(examples.keys())
        n = len(example_list)
        true_examples = {}
        false_examples = {}
        score_val = 0.0
        
        Prover.rule = clause
        Prover.facts = data
        
        result = []
        for example in example_list:
            result.append(Prover.prove_rule(example))
        
        for i in range(n):
            if (not not result[i]):
                true_examples[example_list[i]] = examples[example_list[i]]
            else:
                false_examples[example_list[i]] = examples[example_list[i]]
        nt = len(true_examples)
        nf = len(false_examples)
        n = nt+nf
        if Node.score == "IG":
            left_entropy = entropy(list(true_examples.values()))
            right_entropy = entropy(list(false_examples.values()))
            ig = (nt*left_entropy)/n + (nf*right_entropy)/n
            score_val = ig
        elif Node.score == "WV":
            left_variance = 0
            try:
                left_variance = pvariance(list(true_examples.values()))
            except:
                left_variance = 0
            right_variance = 0
            try:
                right_variance = pvariance(list(false_examples.values()))
            except:
                right_variance = 0
                
            wv = (nt*left_variance)/n + (nf*right_variance)/n
            score_val = wv

        return ((score_val,true_examples,false_examples))
        
    def expand(self):
        """scores all clauses with test conditions
           and expands on best test
        """
        
        conditions_and_var_types = self.find_test_conditions(self.bk)
        child_bk = []
        test_conditions_and_modes = conditions_and_var_types[0]
        test_conditions = [item[0] for item in test_conditions_and_modes]
        modes = [item[1] for item in test_conditions_and_modes]
        children_var_types = conditions_and_var_types[1]
        clauses = []
        for test_condition in test_conditions:
            if self.parent != 'root':
                if str(self)[-1] == ')':
                    clause = str(self)+';'+test_condition
                else:
                    clause = str(self)+test_condition
                clauses.append(clause)
            else:
                clause = str(self)+test_condition
                clauses.append(clause)
                
        #score all clauses and extract minimum
        result = []
        for clause in clauses:
            result.append(self.score_clause(clause))
        scores = [r[0] for r in result]
        min_score = min(scores)
        index = scores.index(min_score)
        self.best_condition = test_conditions[index]
        mode_to_remove = modes[index]

        #remove tested mode from child bk
        for mode in self.bk:
            if mode != mode_to_remove:
                child_bk.append(mode)

        #get left children variable types to pass to left node
        child_var_types = {}
        for var in children_var_types:
            if var in self.best_condition.split('(')[1][:-1].split(','):
                child_var_types[var] = children_var_types[var]

        left_child = Node(self.facts,result[index][1],child_bk,depth = self.depth+1,p="left",parent=self,var_types=child_var_types)
        right_child = Node(self.facts,result[index][2],child_bk,depth = self.depth+1,p="right",parent=self,var_types=child_var_types)
        
        return (min_score,left_child,right_child)

class TILDE(object):
    """implements top-down induction
       of logical decision tree
    """

    def __init__(self,typ="classification",score="IG",max_depth = 2):
        """initializes type and scoring criteria
        """

        self.typ = typ
        self.score = score
        self.max_depth = max_depth
        self.clauses = []
    
    def learn(self,facts,bk,target,pos=[],neg=[],examples={}):
        """learns TILDE tree from data
           examples and background info
        """

        #set values to binary if classification
        #in regression assumed dictionary input like {a(b): <value>}
        if self.typ == "classification":
            examples = {}
            for ex in pos:
                examples[ex] = 1
            for ex in neg:
                examples[ex] = 0

        #assign tree target
        Node.target = target
        Node.typ = self.typ
        Node.score = self.score
        
        #depth first search expansion
        stack = [Node(facts,examples,bk)]
        
        while stack:
            top_node = stack.pop()
            info = top_node.expand()
            score = info[0]
            left_node = info[1]
            right_node = info[2]

            #check if score 0 or max depth reached
            if (top_node.depth + 1 == self.max_depth) or round(score,5) == 0.0:
                left_node_clause = str(left_node)
                if self.typ == "classification":
                    self.clauses.append((left_node_clause,sum(list(left_node.examples.values()))/len(left_node.examples)))
                elif self.typ == "regression":
                    self.clauses.append((left_node_clause,mean(list(left_node.examples.values()))))
                right_node_clause = str(right_node)
                if self.typ == "classification":
                    self.clauses.append((right_node_clause,sum(list(right_node.examples.values()))/len(right_node.examples)))
                elif self.typ == "regression":
                    self.clauses.append((right_node_clause,mean(list(right_node.examples.values()))))
            #if not push right and left child for expansion if there are examples there
            else:
                if right_node.examples:
                    stack.append(right_node)
                if left_node.examples:
                    stack.append(left_node)

    def infer(self,data,example):
        """infers value of example
           from learned target tree
        """

        
        Prover.facts = data
        for clause in self.clauses:
            Prover.rule = clause[0]
            value = clause[1]
            if Prover.prove_rule(example):
                return value
