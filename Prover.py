import string
from copy import deepcopy

class Proof_node(object):

    def __init__(self,literal,bindings,facts):
        """proof node during backtracking
        """

        self.literal = literal
        self.bindings = bindings
        self.facts = []
        for fact in facts:
            lit_pred = self.literal.split('(')[0].strip()
            fact_pred = fact.split('(')[0].strip()
            lit_args = self.literal.split('(')[1][:-1].split(',')
            fact_args = fact.split('(')[1][:-1].split(',')
            n = len(lit_args)
            m = len(fact_args)
            if lit_pred == fact_pred and n == m:
                self.facts.append(fact)

    def __repr__(self):
        """call to print displays this info
        """

        rep = ""
        rep += str(self.literal)+"\n"
        rep += str(self.bindings)+"\n"
        rep += str(self.facts)+"\n"
        return (rep)

    def substitute_with_bindings(self,bindings):
        """substitutes literal vars
           with given bindings
        """

        n_chars = len(self.literal)
        term = ['' for i in range(n_chars)]

        for i in range(n_chars):
            if self.literal[i] in bindings:
                term[i] = bindings[self.literal[i]]
            else:
                term[i] = self.literal[i]

        return (''.join(term))
        

    def substitute(self):
        """substitutes literal vars
           with bindings
        """

        n_chars = len(self.literal)
        term = ['' for i in range(n_chars)]

        for i in range(n_chars):
            if self.literal[i] in self.bindings:
                term[i] = self.bindings[self.literal[i]]
            else:
                term[i] = self.literal[i]

        return (''.join(term))

    def unify(self,term,fact,bindings):
        """unification of two terms
        """

        n = len(term.split('(')[1][:-1].split(','))
        term_args = term.split('(')[1][:-1].split(',')
        fact_args = fact.split('(')[1][:-1].split(',')
        for i in range(n):
            if (not Prover.is_var(term_args[i])) and (not Prover.is_var(fact_args[i])):
                if term_args[i] != fact_args[i]:
                    return False
            elif (Prover.is_var(term_args[i])) and (not Prover.is_var(fact_args[i])):
                bindings[term_args[i]] = fact_args[i]
            elif (not Prover.is_var(term_args[i])) and (Prover.is_var(fact_args[i])):
                bindings[fact_args[i]] = term_args[i]
        return bindings
        

    def search(self):
        """searches facts after substituting
           with bindings
        """

        term = self.substitute()
        ##print ("searching:",term)
        ##print ("in facts",self.facts)
        ##input()
        bindings = deepcopy(self.bindings)
        found = False
        for fact in self.facts:
            found = self.unify(term,fact,bindings)
            if found:
                bound_vars = list(bindings.keys())
                n_bound_vars = len(bound_vars)
                for i in range(n_bound_vars):
                    for j in range(i+1,n_bound_vars):
                        if bindings[bound_vars[i]] == bindings[bound_vars[j]]:
                            return False
                self.facts.remove(self.substitute_with_bindings(bindings)) #THINK ABOUT THIS
                break
        return found

class Prover(object):
    """contains functions for proving theories
    """

    facts = []
    rule = ""

    @staticmethod
    def is_var(argument):
        """checks is argument is a variable
           by checking if it starts with uppercase
        """
        if argument[0] in list(string.ascii_uppercase):
            return True
        return False

    @staticmethod
    def prove_rule(example,exists=True):
        """checks if example satisfies
           rule and against the facts
        """

        facts = Prover.facts
        rule = Prover.rule
        
        #if no rule body then trivially true
        if not rule.split(':-')[1]:
            return True
        
        #assume example is true
        proved = True
        
        #collect head variables and bind to example atoms
        bindings = {}
        head = rule.split(':-')[0].strip()
        head_args = head.split('(')[1][:-1].split(',')
        example_args = example.split('(')[1][:-1].split(',')
        n_args = len(head_args)
        for i in range(n_args):
            if Prover.is_var(head_args[i]):
                bindings[head_args[i]] = example_args[i]
            else:
                if head_args[i] != example_args[i]:
                    bindings = {}
                    break

        #if no binding for head, example is false
        if not bindings:
            proved = False

        #two different vars cant have same binding
        bound_vars = list(bindings.keys())
        n_bound_vars = len(bound_vars)
        for i in range(n_bound_vars):
            for j in range(i+1,n_bound_vars):
                if bindings[bound_vars[i]] == bindings[bound_vars[j]]:
                    return False
        
        #collect body literals
        body = rule.split(':-')[1].strip()
        body_literals = body.split(';')
        pointer = 0
        stack = [Proof_node(body_literals[0],bindings,facts)]
        solutions = []
        while stack:
            node = stack[-1]
            ##print (node)
            ##input()
            x = node.search()
            ##print (x)
            ##input()
            if x:
                if len(stack) != len(body_literals):
                    new_node = Proof_node(body_literals[len(stack)],x,facts)
                    stack.append(new_node)
                else:
                    if exists:
                        return True
                    solutions.append(x)
                    stack.pop()
            elif not x:
                stack.pop()

        if not solutions:
            return False
        return (solutions)
        
#============TEST-CASE-1=====================#
'''
facts = ['p(a,b,d,20)','p(a,b,c,20)','h(a,c,50)','h(a,d,50)']
example = 'q(a,b)'
rule = 'q(A,B) :- p(A,B,C,20);h(A,C,50)'
Prover.facts = facts
Prover.rule = rule
solutions = Prover.prove_rule(example)
print (solutions)
'''
