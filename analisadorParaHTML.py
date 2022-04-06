from lark import Lark,Token,Tree
from lark.tree import pydot__tree_to_png
from lark import Transformer
from lark.visitors import Interpreter
from lark import Discard

grammar = '''
linguagem: declaracoes instrucoes

declaracoes: declaracao PV (declaracao PV)*
declaracao: tipo VAR (ATRIB logic)?

instrucoes: instrucao instrucao*
instrucao: READ PE conteudoread PD PV
| PRINT PE conteudoprint PD PV
| IF PE condicao PD CE instrucoes CD (ELSE CE instrucoes CD)?
| FOR PE atribuicao PV condicao PV atribuicao PD CE instrucoes CD
| atribuicao PV

atribuicao: VAR (PER indice PDR)? ATRIB logic

condicao: logic

conteudoread: VAR (PER indice PDR)?
conteudoprint: logic | VAR PER indice PDR

logic: PE? logicnot AND logic PD? | PE? logicnot OR logic PD? | PE? logicnot PD?
logicnot: PE? NOT logic PD? | PE? relac PD?

relac: PE? logic EQ exp PD?
|  PE? logic DIFF exp PD?
|  PE? logic GRT exp PD?
|  PE? logic GEQ exp PD?
|  PE? logic LWR exp PD?
|  PE? logic LEQ exp PD?
|  PE? exp PD?

exp: PE? exp ADD termo PD?
| PE? exp SUB termo PD?
| PE? termo PD?

termo: PE? exp MUL termo PD?
| PE? exp DIV termo PD?
| PE? exp MOD termo PD?
| PE? factor PD?

factor: PE? logic PD?
| NUM
| BOOLEANO
| VAR
| PER content? PDR
| CE content? CD

content: valor (VIR valor)*

tipo: INT | BOOL
indice: NUM | VAR
valor: NUM | BOOLEANO

BOOLEANO: "True" | "False"
NUM: ("0".."9")+
INT: "int"i
BOOL: "bool"i
VIR: ","
PE: "("
PD: ")"
PER: "["
PDR: "]"
CE: "{"
CD: "}"
PV: ";"
ADD: "+"
SUB: "-"
DIV: "/"
MUL: "*"
MOD: "%"
EQ: "=="
DIFF: "!="
GRT: ">"
GEQ: ">="
LWR: "<"
LEQ: "<="
AND: "and"
OR: "or"
NOT: "not"
READ: "input"
PRINT: "print"
ATRIB: "="
VAR: ("a".."z" | "A".."Z" | "_")+
IF: "if"
FOR: "for"
ELSE: "else"

%import common.WS
%ignore WS
'''

class LinguagemProgramacao(Interpreter):

  def __init__(self):
    self.decls = {}
    self.naoInicializadas = list()
    self.erros = list()
    self.contadorIf = 0
    self.niveisIfs = list()
    self.nivelIf = 0
    self.nasInstrucoes = False
    self.output = {}

  def linguagem(self, tree):
    # print('A visitar todos os filhos da linguagem...')
    self.visit(tree.children[0])
    self.nasInstrucoes = True
    self.visit(tree.children[1])
    #Criar o output
    self.output['decls'] = self.decls
    self.output['naoInicializadas'] = self.naoInicializadas
    self.output['erros'] = self.erros
    self.output['contadorIf'] = self.contadorIf
    self.output['niveisIf'] = self.niveisIfs
    return self.output

  def declaracoes(self, tree):
    # print('Entrei nas declarações...')
    # print('A visitar todos os filhos da regra declarações...')
    for decl in tree.children:
      if isinstance(decl, Tree):
        self.visit(decl)

  def declaracao(self, tree):
    # print('Entrei numa declaração...')
    #print(tree.children)
    print('<p class="code">')
    var = None
    tipo = None
    valor = None
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'VAR':
        # print('Variável declarada: ', child.value)
        var = child.value
      elif isinstance(child, Tree) and child.data == 'tipo':
        tipo = self.visit(child)
        # print('Tipo: ', tipo)
      elif isinstance(child, Token) and child.type == 'ATRIB':
        #Se houver atribuição visita o valor que está a ser atribuido
        valor = self.visit(tree.children[3])
        # print('Valor atribuído: ', valor)

    #Verificar se o valor existe, se é booleano, ou se é uma variável
    if valor == None:
      self.naoInicializadas.append(var)
    elif isinstance(valor,str):
      if valor in self.decls.keys():
        self.decls[var] = self.decls[valor]
      else:
        self.erros.append(('1: Variável não declarada',valor))
    else:
      #É um int ou array de ints, ou bool ou array de bools
      self.decls[var] = (tipo, valor)
    #Transformar a declaração num parágrafo em HTML
    if valor != None:
      print(tipo + ' ' + var + ' = ' + str(valor) + ';')
    else:
      print(tipo + ' ' + var + ';')
    print('</p>')

  def instrucoes(self, tree):
    # print('Entrei nas instruções...')
    self.visit_children(tree)

  def instrucao(self, tree):
    # print('Entrei numa instrução...')
    nivelAtual = self.nivelIf
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'IF':
        self.niveisIfs.append(nivelAtual)
        self.contadorIf += 1
      elif isinstance(child, Tree):
        if child.data == 'instrucoes':
          self.nivelIf += 1
          self.visit(child)
          self.nivelIf = nivelAtual
        else:
          self.visit(child)

  def tipo(self, tree):
    return str(tree.children[0])

  def logic(self,tree):
    r = self.visit_children(tree)
    return r[0]

  def logicnot(self,tree):
    r = self.visit_children(tree)
    return r[0]

  def relac(self,tree):
    r = self.visit_children(tree)
    return r[0]

  def exp(self,tree):
    r = self.visit_children(tree)
    return r[0]

  def termo(self,tree):
    r = self.visit_children(tree)
    return r[0]

  def factor(self, tree):
    # print('Entrei num factor...')
    if self.nasInstrucoes and isinstance(tree.children[0], Token) and tree.children[0].type == 'VAR' and tree.children[0].value not in self.decls.keys():
      self.erros.append(('1: Variável não declarada', tree.children[0].value))
    else:
      child = tree.children[0]
      if isinstance(child, Token) and child.type == 'NUM':
        return int(child.value)
      elif isinstance(child, Token) and child.type == 'BOOLEANO':
        if child.value == "False":
          return False
        elif child.value == "True":
          return True
      elif isinstance(child, Token) and child.type == 'VAR':
        return str(child.value)
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'PDR':
        return list()
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Tree):
        lista = self.visit(tree.children[1])
        return lista
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'CD':
        return set()
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Tree):
        conjunto = self.visit(tree.children[1])
        return set(conjunto)

  def content(self, tree):
    # print('Entrei no conteúdo de uma estrutura...')
    res = list()
    for child in tree.children:
      if isinstance(child, Tree):
        r = self.visit(child)
        res.append(r)
    return res

  def valor(self, tree):
    # print('Entrei num valor...')
    child = tree.children[0]
    if isinstance(child,Token) and child.type == 'NUM':
      return int(child.value)
    elif isinstance(child,Token) and child.type == 'BOOLEANO':
      if child.value == 'False':
        return False
      else:
        return True
    
l = Lark(grammar, start='linguagem')

f = open('inputCode.txt', 'r')
input = f.read()

tree = l.parse(input)
#print(tree.pretty())

data = LinguagemProgramacao().visit(tree)
print('-'*100)
print('Output: ', data)
print('-'*100)