import hashlib
import operator
from MastExceptions import RootNotReachable, NodeNotValid, LeafNodeNotValid, RootNodeHashDoesNotMatch

EXPR, AND, OR, LPAREN, RPAREN, EOF = (
    'EXPR', 'AND', 'OR', '(', ')', 'EOF'
)

ops = {
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '>': operator.gt
}


def calculate_hash(left_child_hash, right_child_hash):
    return hashlib.sha256((left_child_hash + right_child_hash).encode()).hexdigest()


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


###############################################################################
#                                                                             #
#  LEXER                                                                      #
#                                                                             #
###############################################################################

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def expression(self):
        expression = ''
        self.advance()
        while self.current_char != '}':
            expression += self.current_char
            self.advance()
        self.advance()
        return expression

    def operator(self):
        op = ''
        while self.current_char != ' ' and not self.current_char.isdigit():
            op += self.current_char
            self.advance()
        return op


class ASTLexer(Lexer):
    def __int__(self, text):
        super().__init__(text)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '{':
                return Token(EXPR, self.expression())

            if self.current_char == '+':
                self.advance()
                return Token(OR, '+')

            if self.current_char == '*':
                self.advance()
                return Token(AND, '*')

            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            self.error()

        return Token(EOF, None)


###############################################################################
#                                                                             #
#  PARSER                                                                     #
#                                                                             #
###############################################################################

class AST(object):
    def __init__(self, hash):
        self.parent_node = None
        self.hash = hash


class BinOp(AST):
    def __init__(self, left, op, right):
        super().__init__(hashlib.sha256((left.hash + right.hash).encode()).hexdigest())
        self.left = left
        self.token = self.op = op
        self.right = right


class Expr(AST):
    def __init__(self, token):
        super().__init__(hashlib.sha256(token.value.encode()).hexdigest())
        self.token = token
        self.value = token.value


class SuperNode:
    def __init__(self, hash_value):
        self.hash_value = hash_value


class Node(SuperNode):
    def __init__(self, parent_node, operator, left_hash, right_hash, hash_value):
        super().__init__(hash_value)
        self.parent_node = parent_node
        self.operator = operator
        self.left_hash = left_hash
        self.right_hash = right_hash


class LeafNode(SuperNode):
    def __init__(self, parent_node, expr, hash_value):
        super().__init__(hash_value)
        self.parent_node = parent_node
        self.expr = expr


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        token = self.current_token
        if token.type == EXPR:
            self.eat(EXPR)
            return Expr(token)
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node

    def term(self):
        node = self.factor()

        while self.current_token.type in AND:
            token = self.current_token
            if token.type == AND:
                self.eat(AND)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def expr(self):
        node = self.term()

        while self.current_token.type in OR:
            token = self.current_token
            if token.type == OR:
                self.eat(OR)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        return self.expr()


##############################################################################
#
# MAST BUILDER                                                               #
#
##############################################################################

class DoubleConnector:

    def set_parent(self, parent_node, node):
        node.parent_node = parent_node
        if isinstance(node, Expr):
            return
        else:
            self.set_parent(parent_node=node, node=node.left)
            self.set_parent(parent_node=node, node=node.right)

    def connect(self, tree):
        tree.parent_node = None
        self.set_parent(parent_node=tree, node=tree.left)
        self.set_parent(parent_node=tree, node=tree.right)


class NodeVisitor(object):
    def visit(self, node, parent_node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, parent_node)

    def generic_visit(self, node, parent_node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class MASTBuilder(NodeVisitor):
    def __init__(self, text):
        lexer = ASTLexer(text)
        parser = Parser(lexer)
        self.parser = parser
        self.connector = DoubleConnector()
        self.evidence_list = []

    def visit_BinOp(self, node, parent_node):
        mast_node = Node(parent_node=parent_node, operator=node.op, left_hash=node.left.hash,
                         right_hash=node.right.hash, hash_value=node.hash)
        self.visit(node.left, mast_node)
        self.visit(node.right, mast_node)

    def visit_Expr(self, node, parent_node):
        leaf_node = LeafNode(parent_node=parent_node, expr=node.value, hash_value=node.hash)
        self.evidence_list.append(leaf_node)

    def create_mast_object(self):
        tree = self.parser.parse()
        self.connector.connect(tree)
        self.visit(tree, None)
        return tree.hash, self.evidence_list


##############################################################################
#
# MAST VERIFICATION                                                          #
#
##############################################################################

class ExpressionLexer(Lexer):
    def __int__(self, text):
        super().__init__(text)

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return self.integer()

            if self.current_char in ('<', '>', '!', '='):
                return self.operator()

            self.error()

        return Token(EOF, None)


class MASTVerification:
    def __init__(self, root_hash, global_state, evidence_list):
        self.root_hash = root_hash
        self.global_state = global_state
        self.evidence_list = evidence_list
        self.and_nodes_lookup = {}

    def cmp(self, arg1, op, arg2):
        operation = ops.get(op)
        return operation(arg1, arg2)

    def evaluate_evidence(self, expression):
        for key, value in self.global_state.items():
            expression = expression.replace(key, value)
        lexer = ExpressionLexer(expression)
        arg1 = lexer.get_next_token()
        op = lexer.get_next_token()
        arg2 = lexer.get_next_token()
        return self.cmp(arg1, op, arg2)

    def is_child_of_parent_node(self, node):
        return node.hash_value == node.parent_node.left_hash or node.hash_value == node.parent_node.right_hash

    def has_parent_node_correct_children_hashes(self, parent_node):
        return parent_node.hash_value == calculate_hash(parent_node.left_hash, parent_node.right_hash)

    def evaluate_node_hashes(self, node):
        return self.is_child_of_parent_node(node) and self.has_parent_node_correct_children_hashes(node.parent_node)

    def check_leaf_node(self, leaf_node):
        if not (self.evaluate_node_hashes(leaf_node) and self.evaluate_evidence(leaf_node.expr)):
            raise LeafNodeNotValid('Leaf node is not valid')

    def check_root_node(self, root_node):
        if root_node.hash_value == self.root_hash:
            return True
        else:
            raise RootNodeHashDoesNotMatch('Root node hash does not match')

    def check_node(self, node):
        if not (self.has_parent_node_correct_children_hashes(node.parent_node) and self.is_child_of_parent_node(node)):
            raise NodeNotValid('Node is not valid')

    def add_to_queue_and_update_lookup_dict(self, queue, node):
        child_hashes = self.and_nodes_lookup.get(node.parent_node.hash_value)
        if child_hashes is None:
            self.and_nodes_lookup[node.parent_node.hash_value] = [node.hash_value]
            queue.append(node.parent_node)
        else:
            child_hashes.append(node.hash_value)
            self.and_nodes_lookup[node.parent_node.hash_value] = child_hashes

    def check_and_node(self, queue, node):
        child_hashes = self.and_nodes_lookup[node.hash_value]
        if self.is_and_node_validated_for_both_children(child_hashes, node):
            self.add_to_queue_and_update_lookup_dict(queue, node)
            return True
        else:
            queue.append(node)
            return False

    def is_and_node_validated_for_both_children(self, child_hashes, node):
        return len(child_hashes) == 2 and (node.hash_value == calculate_hash(child_hashes[0], child_hashes[
            1]) or node.hash_value == calculate_hash(child_hashes[1], child_hashes[0]))

    def check_root_and_node(self, queue, node):
        child_hashes = self.and_nodes_lookup[node.hash_value]
        if self.is_and_node_validated_for_both_children(child_hashes, node):
            return True
        else:
            queue.append(node)
            return False

    def verify_mast(self):
        queue = self.evidence_list.copy()
        counter = len(queue)
        new_node_inserted = False
        while len(queue) >= 0:
            if new_node_inserted:
                new_node_inserted = False
                counter = len(queue)
            elif counter <= 0:
                raise RootNotReachable('Tree root not possible to reach!')
            node = queue.pop(0)
            if isinstance(node, LeafNode):
                new_node_inserted = True
                self.check_leaf_node(node)
                self.add_to_queue_and_update_lookup_dict(queue, node)
            else:
                if node.parent_node is None:
                    if node.operator.type == OR:
                        return self.check_root_node(node)
                    elif node.operator.type == AND:
                        if self.check_root_and_node(queue, node):
                            return True
                else:
                    self.check_node(node)
                    if node.operator.type == OR:
                        new_node_inserted = True
                        self.add_to_queue_and_update_lookup_dict(queue, node)
                    elif node.operator.type == AND:
                        new_node_inserted = self.check_and_node(queue, node)
            counter -= 1
