from lark import Lark,Token,Tree
from lark.tree import pydot__tree_to_png
from lark import Transformer
from lark.visitors import Interpreter
from lark import Discard

grammar = '''
linguagem: declaracoes instrucoes

declaracoes: comentario? declaracao PV comentario? (declaracao PV comentario?)*
declaracao: tipo VAR (ATRIB logic)?

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

conteudo: factor (VIR factor)*
conteudoespecial: conteudodicionario | conteudo
conteudodicionario: entrada (VIR entrada)*
entrada: STRING PP factor

tipo: INT | BOOL | STR | DOUBLE | LIST | SET | TUPLE | DICT
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
  
def criarFicheiroHtml(nome):
  try:
    f = open(nome, 'r+', encoding='utf-8')
    f.truncate(0)
    return f
  except:
    f = open(nome, 'a', encoding='utf-8')
    return f
  
def preencherInicio(ficheiro):
  conteudo = '''
<!DOCTYPE html>
<html>
  <style>
    .error {
      position: relative;
      display: inline-block;
      border-bottom: 1px dotted black;
      color: red;
    }
    .code {
      position: relative;
      display: inline-block;
    }
    .error .errortext {
      visibility: hidden;
      width: 200px;
      background-color: #555;
      color: #fff;
      text-align: center;
      border-radius: 6px;
      padding: 5px 0;
      position: absolute;
      z-index: 1;
      bottom: 125%;
      left: 50%;
      margin-left: -40px;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .error .errortext::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 20%;
      margin-left: -5px;
      border-width: 5px;
      border-style: solid;
      border-color: #555 transparent transparent transparent;
    }
    .error:hover .errortext {
      visibility: visible;
      opacity: 1;
    }
  </style>
  <body>
    <h2>Análise de código</h2>
    <pre><code>'''
  ficheiro.write(conteudo + '\n')
  
def preencherFim(ficheiro):
  conteudo = '''
    </code></pre>
  </body>
</html>'''
  ficheiro.write(conteudo)

class LinguagemProgramacao(Interpreter):

  def __init__(self):
    self.fHtml = criarFicheiroHtml('outputHtml.html')
    preencherInicio(self.fHtml)
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
    self.niveisIfs = {}
    self.nivelIf = -1
    self.nivelProfundidade = 0
    self.totalSituacoesAn = 0
    self.nasInstrucoes = False
    self.instrucaoAtual = ""
    self.output = {}

  def linguagem(self, tree):
    # print('A visitar todos os filhos da linguagem...')
    self.visit(tree.children[0])
    self.nasInstrucoes = True
    self.visit(tree.children[1])
    preencherFim(self.fHtml)
    self.fHtml.close()
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
    self.output['totalSituacoesAn'] = self.totalSituacoesAn
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
    self.fHtml.write('\t\t<p class="code">\n')
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
      if '[' or ']' in valor: #O valor resulta de um acesso a uma estrutura
        infoEstrutura = valor.split('[')
        variavel = infoEstrutura[0]
        if variavel not in self.decls.keys(): #Se a variável não tiver sido declarada antes é gerado um erro
          self.erros['1: Não-declaração'].add(variavel)
      elif valor not in self.decls.keys(): #Verificar se a variável atómica já existe
        self.erros['1: Não-declaração'].add(valor)
    self.decls[var] = tipo
    #Transformar a declaração num parágrafo em HTML
    if valor != None:
      self.fHtml.write('\t\t' + tipo + ' ' + var + ' = ' + str(valor) + ';\n')
    else:
      self.fHtml.write('\t\t' + tipo + ' ' + var + ';\n')
    self.fHtml.write('\t\t</p>\n')

  def instrucoes(self, tree):
    # print('Entrei nas instruções...')
    self.visit_children(tree)

  def instrucao(self, tree):
    # print('Entrei numa instrução...')
    nivelIf = self.nivelIf
    nivelProfundidade = self.nivelProfundidade
    self.fHtml.write('\t\t<p class="code">\n\t\t')
    for child in tree.children:
      if isinstance(child,Token) and child.type == 'CE':
        #O \n é necessário porque a seguir a este token chegam instruções aninhadas
        self.fHtml.write(child.value)
        self.fHtml.write('\n')
      elif isinstance(child,Token): 
        #Escreve qualquer token no html
        self.fHtml.write(child.value)
      if isinstance(child, Token) and (child.type == 'IF' or child.type == 'FOR' or child.type == 'WHILE' or child.type == 'REPEAT') and self.nivelProfundidade > 0:
        self.totalSituacoesAn += 1
      if isinstance(child, Token) and child.type == 'IF' and self.nivelIf == -1: #Deteção do primeiro if
        self.instrucaoAtual = "condicional"
        self.dicinstrucoes['condicionais'] += 1
        self.dicinstrucoes['total'] += 1
        self.nivelIf = 0
        nivelIf = self.nivelIf
        self.niveisIfs.setdefault(nivelIf, list())
        self.niveisIfs[nivelIf].append(self.dicinstrucoes['condicionais'])
      elif isinstance(child, Token) and child.type == 'IF':
        self.instrucaoAtual = "condicional"
        self.dicinstrucoes['condicionais'] += 1
        self.dicinstrucoes['total'] += 1
        self.niveisIfs.setdefault(nivelIf, list())
        self.niveisIfs[nivelIf].append(self.dicinstrucoes['condicionais'])
      elif isinstance(child, Token) and (child.type == 'FOR' or child.type == 'WHILE' or child.type == 'REPEAT'):
        self.dicinstrucoes['ciclicas'] += 1
        self.dicinstrucoes['total'] += 1
        self.instrucaoAtual = "ciclo"
      elif isinstance(child, Token) and child.type == 'READ':
        self.instrucaoAtual = "leitura"
        self.dicinstrucoes['leitura'] += 1
        self.dicinstrucoes['total'] += 1
      elif isinstance(child, Token) and child.type == 'PRINT':
        self.instrucaoAtual = "escrita"
        self.dicinstrucoes['escrita'] += 1
        self.dicinstrucoes['total'] += 1
      elif isinstance(child, Tree) and child.data == 'atribuicao':
        self.instrucaoAtual = "atribuicao"
        self.dicinstrucoes['atribuicoes'] += 1
        self.dicinstrucoes['total'] += 1
        self.visit(child)
      elif isinstance(child, Tree):
        if child.data == 'conteudoread':
          self.visit(child)
        elif child.data == 'conteudoprint':
          self.visit(child)
        elif child.data == 'condicao':
          r = self.visit(child)
        elif child.data == 'instrucoes' and self.instrucaoAtual == "ciclo":
          self.nivelProfundidade += 1
          self.nivelIf = 0
          self.visit(child)
          self.nivelIf = nivelIf
          self.nivelProfundidade = nivelProfundidade
        elif child.data == 'instrucoes' and self.instrucaoAtual == "condicional":
          self.nivelProfundidade += 1
          self.nivelIf += 1
          self.visit(child)
          self.nivelIf = nivelIf
          self.nivelProfundidade = nivelProfundidade
    self.fHtml.write('\n\t\t</p>\n')
    
  def condicao(self,tree):
    r = self.visit(tree.children[0])
    #print('CONDICAO: ', r)
    
  def atribuicao(self,tree):
    #Se for feita uma atribuiçao a uma var não inicializada, já passa a estar inicializada
    if (isinstance(tree.children[0],Token) and tree.children[0].type == 'VAR') and tree.children[0].value in self.naoInicializadas:
      self.fHtml.write(tree.children[0].value)
      self.naoInicializadas.remove(tree.children[0].value)
    elif isinstance(tree.children[0],Token) and tree.children[0].type == 'VAR':
      self.fHtml.write(tree.children[0].value)
    for child in tree.children[1:]:
      if isinstance(child,Token) and child.type == 'ATRIB':
        self.fHtml.write(' ' + child.value + ' ')
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
  
  def conteudoread(self,tree):
    for child in tree.children:
      if isinstance(child,Token) and child.type == 'VAR' and child.value in self.naoInicializadas:
        self.fHtml.write(child.value)
        self.naoInicializadas.remove(child.value)
        self.utilizadas.add(child.value)
      elif isinstance(child,Token) and child.type == 'VAR' and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
      elif isinstance(child,Tree) and child.data == 'chave':
        chave = str(self.visit(child))
        self.fHtml.write(chave)
        
  def conteudoprint(self,tree):
    for child in tree.children:
      if isinstance(child,Tree) and child.data == 'chave':
        chave = str(self.visit(child))
        self.fHtml.write(chave)
      elif isinstance(child,Tree):
        self.visit(child)
      elif isinstance(child,Token) and child.type == 'VAR' and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
      elif isinstance(child,Token) and child.type == 'VAR' and child.value in self.naoInicializadas:
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não inicializada</span></div>')
      elif isinstance(child,Token):
        self.fHtml.write(child.value)

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
    """ termo: PE? exp MUL termo PD?
    | PE? exp DIV termo PD?
    | PE? exp MOD termo PD?
    | PE? factor PD? """
    r = self.visit_children(tree)
    print('TERMO: ',r)
    return r[0]

  def factor(self, tree):
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'VAR' and len(tree.children) > 1:
        if child.value not in self.decls.keys():
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
          self.erros['1: Não-declaração'].add(child.value)
        elif child.value in self.naoInicializadas:
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não inicializada</span></div>')
          self.erros['3: Usado mas não inicializado'].add(child.value)
        else:
          self.fHtml.write(child.value)
        self.utilizadas.add(child.value)
        chave = self.visit(tree.children[2])
        return str(child.value) + '[' + str(chave) + ']'
      elif isinstance(child, Token) and child.type == 'VAR':
        if child.value not in self.decls.keys():
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
          self.erros['1: Não-declaração'].add(child.value)
        elif child.value in self.naoInicializadas:
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não inicializada</span></div>')
          self.erros['3: Usado mas não inicializado'].add(child.value)
        else:
          self.fHtml.write(child.value)
        #Adicionar a variável à lista das utilizadas
        self.utilizadas.add(child.value)
        return str(child.value)
      elif isinstance(child, Tree) and child.data == 'chave':
        #Obter o índice da estrutura se existir
        chave = self.visit(child)
      elif isinstance(child, Token) and child.type == 'NUM':
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
    elif self.nasInstrucoes and tree.children[0].type == 'STRING':
      r = (tree.children[0].value)
      return r
    elif tree.children[0].type == 'STRING':
      r = (tree.children[0].value)[1:-1]
      return r
    elif tree.children[0].type == 'VAR':
      return str(tree.children[0].value)
    
l = Lark(grammar, start='linguagem')

f = open('codigoFonte.txt', 'r')
input = f.read()

tree = l.parse(input)
#print(tree.pretty())

data = LinguagemProgramacao().visit(tree)
print('-'*100)
print('Output: ', data)
print('-'*100)