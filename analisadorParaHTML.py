from lark import Lark,Token,Tree
from lark.tree import pydot__tree_to_png
from lark import Transformer
from lark.visitors import Interpreter
from lark import Discard

grammar = '''
linguagem: declaracoes instrucoes

declaracoes: comentario? declaracao PV comentario? (declaracao PV comentario?)*
declaracao: tipo VAR (ATRIB tipoatribuicao)?

tipoatribuicao: normal | estrutura
normal: logic
estrutura: VAR PER chave PDR

instrucoes: instrucao comentario? (instrucao comentario?)*
instrucao: READ PE conteudoread PD PV
| PRINT PE conteudoprint PD PV
| IF PE condicao PD CE instrucoes CD (ELSE CE instrucoes CD)?
| FOR PE atribuicao PV condicao PV atribuicao PD CE instrucoes CD
| WHILE PE condicao PD CE instrucoes CD
| REPEAT PE NUM PD CE instrucoes CD
| atribuicao PV

comentario: C_COMMENT

atribuicao: VAR (PER chave PDR)? ATRIB logic

condicao: logic

conteudoread: VAR (PER chave PDR)?
conteudoprint: logic | VAR PER chave PDR

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
| STRING
| NUMDOUBLE
| VAR (PER chave PDR)?
| PER conteudo? PDR
| CE conteudoespecial? CD
| PE conteudo? PD

conteudo: valor (VIR valor)*
conteudoespecial: conteudodicionario | conteudo
conteudodicionario: entrada (VIR entrada)*
entrada: STRING PP valor

tipo: INT | BOOL | STR | DOUBLE | LIST | SET | TUPLE | DICT
valor: NUM | BOOLEANO | NUMDOUBLE | STRING
chave: NUM | STRING | VAR

BOOLEANO: "True" | "False"
NUM: ("0".."9")+
NUMDOUBLE: ("0".."9")+"."("0".."9")+
STRING: ESCAPED_STRING
INT: "int"
STR: "string"
BOOL: "bool"
DOUBLE: "double"
LIST: "list"
SET: "set"
TUPLE: "tuple"
DICT: "dict"
VIR: ","
PE: "("
PD: ")"
PER: "["
PDR: "]"
CE: "{"
CD: "}"
PV: ";"
PP: ":"
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
ELSE: "else"
FOR: "for"
WHILE: "while"
REPEAT: "repeat"

%import common.WS
%import common.ESCAPED_STRING
%import common.C_COMMENT
%ignore WS
'''

""" def digito(s):
  resultado = True
  limite = len(s)
  i = 0
  while i < limite and resultado:
    if s[i] > "9" or s[i] < "0":
      resultado = False
    i += 1
  return resultado """

class LinguagemProgramacao(Interpreter):

  def __init__(self):
    self.decls = {}
    self.naoInicializadas = set()
    self.utilizadas = set()
    self.erros = {}
    self.erros['1: Não-declaração'] = set()
    self.erros['2: Redeclaração'] = set()
    self.erros['3: Usado mas não inicializado'] = set()
    self.erros['4: Declarado mas nunca mencionado'] = set()
    self.dicinstrucoes = {}
    self.dicinstrucoes['total'] = 0
    self.dicinstrucoes['atribuicoes'] = 0
    self.dicinstrucoes['leitura'] = 0
    self.dicinstrucoes['escrita'] = 0
    self.dicinstrucoes['condicionais'] = 0
    self.dicinstrucoes['ciclicas'] = 0
    self.niveisIfs = list()
    self.nivelIf = -1
    self.situacoesAninhamentoIf = 0
    self.nasInstrucoes = False
    self.output = {}

  def linguagem(self, tree):
    # print('A visitar todos os filhos da linguagem...')
    self.visit(tree.children[0])
    self.nasInstrucoes = True
    self.visit(tree.children[1])
    #Verificar as variáveis declaradas mas nunca mencionadas
    declaradas = set(self.decls.keys())
    self.erros['4: Declarado mas nunca mencionado'] = declaradas - self.utilizadas
    #Criar o output
    self.output['decls'] = self.decls
    self.output['naoInicializadas'] = self.naoInicializadas
    self.output['erros'] = self.erros
    self.output['niveisIf'] = self.niveisIfs
    self.output['utilizadas'] = self.utilizadas
    self.output['instrucoes'] = self.dicinstrucoes
    self.output['situacoesAninhamentoIf'] = self.situacoesAninhamentoIf
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
      if isinstance(child, Token) and child.type == 'VAR': #Visita o variável declarada
        # print('Variável declarada: ', child.value)
        var = child.value
      elif isinstance(child, Tree) and child.data == 'tipo': #Visita o tipo da declaração
        tipo = self.visit(child)
        # print('Tipo: ', tipo)
      elif isinstance(child, Token) and child.type == 'ATRIB': #Se houver atribuição visita o valor que está a ser declarado
        valor = self.visit(tree.children[3])
        # print('Valor atribuído: ', valor)

    if var in self.decls.keys(): #Verificar se há redeclaração
      self.erros['2: Redeclaração'].add(var)
    elif valor == None: #Verificar se foi atribuído algum valor à variável
      self.naoInicializadas.add(var)
      self.decls[var] = tipo
    elif isinstance(valor,str) and valor[0] != '"': #Verificar se o valor é uma variável (string sem "")
      if '-' in valor: #O valor resulta de um acesso a uma estrutura, a variável e a chave são separados por '-'
        infoEstrutura = valor.split('-')
        variavel = infoEstrutura[0]
        if variavel not in self.decls.keys(): #Se a variável não tiver sido declarada antes é gerado um erro
          self.erros['1: Não-declaração'].add(variavel)
      elif valor not in self.decls.keys(): #Verificar se a variável atómica já existe
        self.erros['1: Não-declaração'].add(valor)
      else:
        self.decls[var] = self.decls[valor]
    else: 
      self.decls[var] = tipo
    #Transformar a declaração num parágrafo em HTML
    if valor != None:
      print(tipo + ' ' + var + ' = ' + str(valor) + ';')
    else:
      print(tipo + ' ' + var + ';')
    print('</p>')
    
  def tipoatribuicao(self,tree):
    r = self.visit(tree.children[0])
    return r
  
  def normal(self,tree):
    return self.visit(tree.children[0])
  
  def estrutura(self,tree):
    variavel = tree.children[0].value
    chave = self.visit(tree.children[2])
    return str(variavel) + "-" + str(chave)

  def instrucoes(self, tree):
    # print('Entrei nas instruções...')
    self.visit_children(tree)

  def instrucao(self, tree):
    # print('Entrei numa instrução...')
    nivelAtual = self.nivelIf
    tipoInstrucao = ""
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'IF' and self.nivelIf == -1: #Deteção do primeiro if
        tipoInstrucao = "if"
        self.dicinstrucoes['condicionais'] += 1
        self.dicinstrucoes['total'] += 1
        self.nivelIf = 0
        nivelAtual = self.nivelIf
        self.niveisIfs.append(nivelAtual)
      elif isinstance(child, Token) and child.type == 'IF':
        tipoInstrucao = "if"
        self.dicinstrucoes['condicionais'] += 1
        self.dicinstrucoes['total'] += 1
        self.niveisIfs.append(self.nivelIf)
      elif isinstance(child, Token) and (child.type == 'FOR' or child.type == 'WHILE' or child.type == 'REPEAT'):
        self.dicinstrucoes['ciclicas'] += 1
        self.dicinstrucoes['total'] += 1
        tipoInstrucao = "ciclo"
      elif isinstance(child, Token) and child.type == 'READ':
        self.dicinstrucoes['leitura'] += 1
        self.dicinstrucoes['total'] += 1
      elif isinstance(child, Token) and child.type == 'PRINT':
        self.dicinstrucoes['escrita'] += 1
        self.dicinstrucoes['total'] += 1
      elif isinstance(child, Tree) and child.data == 'atribuicao':
        self.dicinstrucoes['atribuicoes'] += 1
        self.dicinstrucoes['total'] += 1
      elif isinstance(child, Tree):
        if child.data == 'instrucoes' and tipoInstrucao == "ciclo":
          self.nivelIf = 0
          self.situacoesAninhamentoIf = 0
          self.visit(child)
          self.nivelIf = nivelAtual
        elif child.data == 'instrucoes' and tipoInstrucao == "if":
          self.nivelIf += 1
          self.visit(child)
          self.nivelIf = nivelAtual
          if self.nivelIf == 0: #Se já tiver visitado todos os filhos e este for o if de nível 0 então estamos presente uma situação de aninhamento
            self.situacoesAninhamentoIf += 1
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
    variavel = tree.children[0].value
    if isinstance(tree.children[0], Token) and tree.children[0].type == 'VAR': #Adicionar a variável à lista das utilizadas
      self.utilizadas.add(variavel)
    if self.nasInstrucoes and isinstance(tree.children[0], Token) and tree.children[0].type == 'VAR':
      variavel = tree.children[0].value
      if variavel not in self.decls.keys(): #Se não estiver declarado
        self.erros['1: Não-declaração'].add(variavel)
      elif variavel in self.naoInicializadas: #Se não estiver inicializado
        self.erros['3: Usado mas não inicializado'].add(variavel)
    else:
      child = tree.children[0]
      if isinstance(child, Token) and child.type == 'NUM':
        return int(child.value)
      elif isinstance(child, Token) and child.type == 'BOOLEANO':
        if child.value == "False":
          return False
        elif child.value == "True":
          return True
      elif isinstance(child, Token) and child.type == 'STRING':
        return str(child.value)
      elif isinstance(child, Token) and child.type == 'NUMDOUBLE':
        return float(child.value)
      elif isinstance(child, Token) and child.type == 'VAR':
        return str(child.value)
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'PDR':
        return list()
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Tree):
        lista = self.visit(tree.children[1])
        return lista
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'CD':
        return {}
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Tree):
        estrutura = self.visit(tree.children[1])
        if isinstance(estrutura, dict):
          return estrutura
        else:
          return set(estrutura)
      elif isinstance(child, Token) and child.type == 'PE' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'PD':
        return tuple()
      elif isinstance(child, Token) and child.type == 'PE' and isinstance(tree.children[1], Tree):
        tuplo = self.visit(tree.children[1])
        return tuple(tuplo)
      
  def conteudoespecial(self,tree):
    r = self.visit(tree.children[0])
    return r
  
  def conteudodicionario(self,tree):
    estrutura = dict()
    for child in tree.children:
      if isinstance(child, Tree):
        entrada = self.visit(child)
        chave = entrada[0][1:-1]
        estrutura[chave] = entrada[2]
    return estrutura

  def conteudo(self, tree):
    # print('Entrei no conteúdo de uma estrutura...')
    res = list()
    for child in tree.children:
      if isinstance(child, Tree):
        r = self.visit(child)
        res.append(r)
    return res

  def chave(self,tree):
    if tree.children[0].type == 'NUM':
      return int(tree.children[0].value)
    elif tree.children[0].type == 'STRING':
      r = (tree.children[0].value)[1:-1]
      return r
    else: #Variável
      return str(tree.children[0].value)

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
    elif isinstance(child,Token) and child.type == 'NUMDOUBLE':
      return float(child.value)
    elif isinstance(child,Token) and child.type == 'STRING':
      return str(child.value)
    
l = Lark(grammar, start='linguagem')

f = open('codigoFonte.txt', 'r')
input = f.read()

tree = l.parse(input)
#print(tree.pretty())

data = LinguagemProgramacao().visit(tree)
print('-'*100)
print('Output: ', data)
print('-'*100)