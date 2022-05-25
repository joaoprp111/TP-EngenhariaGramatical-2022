from errno import ESOCKTNOSUPPORT
from lark import Lark,Token,Tree
from lark.tree import pydot__tree_to_png
from lark import Transformer
from lark.visitors import Interpreter
from lark import Discard
from funcoesUteis import *
import graphviz 

grammar = '''
linguagem: declaracoes instrucoes

declaracoes: comentario? declaracao PV comentario? (declaracao PV comentario?)*
declaracao: tipo VAR (ATRIB logic)?

instrucoes: instrucao comentario? (instrucao comentario?)*
instrucao: READ PE conteudoread PD PV
| PRINT PE logic PD PV
| IF PE condicao PD CE instrucoes CD (ELSE CE instrucoes CD)?
| FOR PE atribuicao PV condicao PV atribuicao PD CE instrucoes CD
| WHILE PE condicao PD CE instrucoes CD
| REPEAT PE NUM PD CE instrucoes CD
| atribuicao PV

comentario: C_COMMENT

atribuicao: VAR (PER chave PDR)? ATRIB logic

condicao: logic

conteudoread: VAR (PER chave PDR)?

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

factor: NUM
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

class LinguagemProgramacao(Interpreter):

  def __init__(self):
    self.dot = graphviz.Digraph('cfg')
    self.nodeStatement = ''
    self.lastStatement = ''
    self.statementCount = 0
    self.fHtml = criarFicheiro('codigoAnotado.html')
    self.f2Html = criarFicheiro('informacoesAdicionais.html')
    self.fCfg = criarFicheiro('cfg.dot')
    preencherInicio(self.fHtml)
    self.decls = {}
    self.naoInicializadas = set()
    self.utilizadas = set()
    self.erros = {
      '1: Não-declaração' : set(),
      '2: Redeclaração' : set(),
      '3: Usado mas não inicializado' : set(),
      '4: Declarado mas nunca mencionado' : set() 
    }
    self.dicinstrucoes = {
      'total' : 0,
      'atribuicoes' : 0,
      'leitura' : 0,
      'escrita' : 0,
      'condicionais' :0,
      'ciclicas' : 0
    }
    self.condicoesIfs = []
    self.alternativasIfs = []
    self.niveisIfs = {}
    self.nivelIf = -1
    self.nivelProfundidade = 0
    self.totalSituacoesAn = 0
    self.nasInstrucoes = False
    self.instrucaoAtual = ''
    self.output = {}

  def linguagem(self, tree):
    self.dot.node(str(self.statementCount), label='inicio')
    self.lastStatement = str(self.statementCount)
    self.statementCount += 1
    self.visit(tree.children[0]) #Declarações
    self.nasInstrucoes = True
    self.fHtml.write(' '*10 + '<div class="instrucoes">\n')
    self.visit(tree.children[1]) #Instruções
    self.dot.node(str(self.statementCount), label='fim')
    self.dot.edge(self.lastStatement,str(self.statementCount))
    self.fHtml.write(' '*10 + '</div>\n')
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
    self.output['condicoesIf'] = self.condicoesIfs
    self.output['alternativasIfs'] = self.alternativasIfs
    #Preencher a segunda página com informações adicionais
    criarSegundaPagina(self.output, self.f2Html)
    #Visualizar o grafo CFG gerado
    self.fCfg.write(self.dot.source)
    return self.output

  def declaracoes(self, tree):
    #Visita todas as declarações e cada uma processa a sua parte
    self.fHtml.write(' '*10 + '<div class="declaracoes">\n')
    for decl in tree.children:
      if isinstance(decl, Tree):
        self.visit(decl)
    self.fHtml.write(' '*10 + '</div>\n')

  def declaracao(self, tree):
    self.fHtml.write('\t')
    #Inicialização de variáveis
    var = None
    tipo = None
    valor = None
    #É preciso percorrer cada filho e processar de acordo com as situações
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'VAR' and child.value in self.decls.keys(): #Visita a variável declarada
        var = child.value
        self.erros['2: Redeclaração'].add(var)
        self.fHtml.write('<div class="error">' + var + '<span class="errortext">Variável redeclarada</span></div>')
        self.nodeStatement += ' ' + var
      elif  isinstance(child, Token) and child.type == 'VAR':
        var = child.value
        self.fHtml.write(var)
        self.nodeStatement += ' ' + var
      elif isinstance(child, Tree) and child.data == 'tipo': #Visita o tipo da declaração
        tipo = self.visit(child)
        self.fHtml.write(tipo + ' ')
        self.nodeStatement += tipo
      elif isinstance(child, Token) and child.type == 'ATRIB': #Se houver atribuição visita o valor que está a ser declarado
        valor = self.visit(tree.children[3])
        if valor != None and eDigito(valor):
          valor = int(valor)
        if valor == None:
          self.naoInicializadas.add(var)
          self.decls[var] = tipo
          self.fHtml.write(';\n')
        elif isinstance(valor,str) and valor[0] != '"':
          self.fHtml.write(' = ')
          self.nodeStatement += ' = '
          if ('[' or ']') in valor: #O valor resulta de um acesso a uma estrutura
            infoEstrutura = valor.split('[')
            variavel = infoEstrutura[0]
            if variavel not in self.decls.keys(): #Se a variável não tiver sido declarada antes é gerado um erro
              if variavel != '':
                self.erros['1: Não-declaração'].add(variavel)
              self.fHtml.write('<div class="error">' + variavel + '<span class="errortext">Variável redeclarada</span></div>' + '[' + infoEstrutura[1] + ';\n')
            elif variavel in self.naoInicializadas:
              self.fHtml.write('<div class="error">' + variavel + '<span class="errortext">Variável não inicializada</span></div>' + '[' + infoEstrutura[1] + ';\n')
            else:
              self.fHtml.write(variavel + '[' + infoEstrutura[1] + ';\n')
            self.nodeStatement += variavel + '[' + infoEstrutura[1]
          elif('{' or '}') in valor:
            self.fHtml.write(valor + ';\n')
            self.nodeStatement += str(valor)
          elif valor not in self.decls.keys(): #Verificar se a variável atómica já existe
            self.erros['1: Não-declaração'].add(valor)
            self.fHtml.write('<div class="error">' + valor + '<span class="errortext">Variável redeclarada</span></div>;\n')
            self.nodeStatement += valor
        else:
          self.fHtml.write(' = ')
          self.fHtml.write(str(valor) + ';\n')
          self.nodeStatement += ' = ' + str(valor)
          
    if valor == None: #Caso nunca tenha existido atribuição na declaração
      self.naoInicializadas.add(var)
      self.decls[var] = tipo
      self.fHtml.write(';\n')
      
    self.decls[var] = tipo
    self.dot.node(str(self.statementCount), label=self.nodeStatement)
    self.dot.edge(self.lastStatement,str(self.statementCount))
    self.lastStatement = str(self.statementCount)
    self.statementCount += 1
    self.nodeStatement = ''

  def instrucoes(self, tree):
    r = self.visit_children(tree)
    return r

  def instrucao(self, tree):
    localLastStatement = self.lastStatement
    estruturaCiclica = False
    isFor = False
    #Utilizado para saber quais as atribuições do for
    contadorAtribuicoes = 0
    incrementNode = ''
    initialAtribForNode = ''
    cicleNode = ''
    ifNode = ''
    endifNode = ''
    nivelIf = self.nivelIf
    nivelProfundidade = self.nivelProfundidade
    numTabs = (nivelProfundidade * '\t') + '\t'
    self.fHtml.write(numTabs)
    condicoesParaAninhar = []
    corpo = ''
    sairDoCiclo = False
    resultado = ''
    for child in tree.children:
        if not sairDoCiclo: 
            if isinstance(child,Token) and child.type == 'IF':
                existeElse = False
                self.instrucaoAtual = "condicional"
                self.dicinstrucoes['condicionais'] += 1
                self.dicinstrucoes['total'] += 1
                
                if self.nivelIf == -1: #Primeiro if do código
                    nivelIf = self.nivelIf = 0
                elif nivelProfundidade > 0:
                    self.totalSituacoesAn += 1
                
                self.niveisIfs.setdefault(nivelIf, list())
                self.niveisIfs[nivelIf].append(self.dicinstrucoes['condicionais'])
                
                self.fHtml.write('<div class="info">' + child.value + '<span class="infotext">Nível de aninhamento: ' + str(nivelIf) + '</span></div>')
                self.fHtml.write('(')
                condicaoIfAtual = self.visit(tree.children[2])[0]
                self.fHtml.write('){\n')

                #Criação do nó para o grafo
                ifNode = str(self.statementCount)
                self.dot.node(ifNode,label='if ' + condicaoIfAtual, shape='diamond')
                self.lastStatement = ifNode
                self.statementCount += 1
                self.nodeStatement = ''

                if len(tree.children[5].children) > 0: #Se existirem instruções dentro do if
                    #Criar o nó then
                    self.dot.node(str(self.statementCount),label='then')
                    self.dot.edge(ifNode,str(self.statementCount))
                    self.lastStatement = str(self.statementCount)
                    self.statementCount += 1

                    #Criar o nó para fim do if
                    endifNode = str(self.statementCount)
                    self.dot.node(endifNode,label='fimIf' + str(self.dicinstrucoes['condicionais']))
                    self.statementCount += 1

                    existeElse = 'else' in tree.children[5].children[0].children
                    proxInstrucao = str(tree.children[5].children[0].children[0])
                    if proxInstrucao != 'if' or existeElse or len(tree.children[5].children) > 1:
                        self.condicoesIfs.append(condicaoIfAtual)
                        condicoesParaAninhar = self.condicoesIfs
                        self.condicoesIfs = []
                        self.nivelProfundidade += 1
                        self.nivelIf += 1
                        res = self.visit(tree.children[5])
                        self.nivelIf = nivelIf
                        self.nivelProfundidade = nivelProfundidade
                        numTabs = (self.nivelProfundidade * '\t') + '\t'
                        self.fHtml.write(numTabs + '}')
                        corpo = res[0]
                        for r in res[1:]:
                            corpo += '\n' + r

                        #Ligar ao fim do if
                        self.dot.edge(self.lastStatement,endifNode)
                        self.lastStatement = endifNode

                        if 'else' in tree.children:
                            existeElse = True
                            #Criar o nó else
                            self.dot.node(str(self.statementCount),label='else')
                            self.dot.edge(ifNode,str(self.statementCount))
                            self.lastStatement = str(self.statementCount)
                            self.statementCount += 1

                            self.fHtml.write('else{\n')
                            self.nivelProfundidade += 1
                            self.nivelIf += 1
                            resElse = self.visit(tree.children[9])
                            self.nivelIf = nivelIf
                            self.nivelProfundidade = nivelProfundidade
                            numTabs = (self.nivelProfundidade * '\t') + '\t'
                            self.fHtml.write(numTabs + '}')
                            resultado += child.value + '(' + condicaoIfAtual + '){\n' + str(res) + '}else{\n' + str(resElse) + '}'

                            #Ligar ao fim do if
                            self.dot.edge(self.lastStatement,endifNode)
                            self.lastStatement = endifNode
                        else:               
                            resultado += child.value + '(' + condicaoIfAtual + '){\n' + str(res) + '}'
                    else:
                        self.condicoesIfs.append(condicaoIfAtual)
                        self.nivelProfundidade += 1
                        self.nivelIf += 1
                        res = self.visit(tree.children[5])
                        self.nivelIf = nivelIf
                        self.nivelProfundidade = nivelProfundidade
                        numTabs = (self.nivelProfundidade * '\t') + '\t'
                        self.fHtml.write(numTabs + '}')
                        corpo = res[0]
                        for r in res[1:]:
                            corpo += '\n' + r
                        if 'else' in tree.children:
                            self.fHtml.write('else{\n')
                            self.nivelProfundidade += 1
                            self.nivelIf += 1
                            resElse = self.visit(tree.children[9])
                            self.nivelIf = nivelIf
                            self.nivelProfundidade = nivelProfundidade
                            numTabs = (self.nivelProfundidade * '\t') + '\t'
                            self.fHtml.write(numTabs + '}')
                            resultado += child.value + '(' + condicaoIfAtual + '){\n' + str(res) + '}else{\n' + str(resElse) + '}'
                        else:               
                            resultado += child.value + '(' + condicaoIfAtual + '){\n' + str(res) + '}'
                sairDoCiclo = True
            elif isinstance(child,Token) and child.type == 'CE':
                #O \n é necessário porque a seguir a este token chegam instruções aninhadas
                self.fHtml.write(child.value)
                self.fHtml.write('\n')
                resultado += '{\n' + numTabs
            elif isinstance(child,Token) and child.type == 'CD':
                self.fHtml.write(numTabs + child.value)
                resultado += numTabs + '}'
            elif isinstance(child, Token) and (child.type == 'FOR' or child.type == 'WHILE' or child.type == 'REPEAT'):
                estruturaCiclica = True
                if child.type == 'FOR':
                  isFor = True
                if self.nivelProfundidade > 0:
                    self.totalSituacoesAn += 1
                self.fHtml.write(child.value)
                self.dicinstrucoes['ciclicas'] += 1
                self.dicinstrucoes['total'] += 1
                self.instrucaoAtual = "ciclo"
                resultado += child.value
                if not isFor:
                  self.nodeStatement += child.value + ' '
            elif isinstance(child, Token) and child.type == 'READ':
                self.fHtml.write(child.value)
                self.instrucaoAtual = "leitura"
                self.dicinstrucoes['leitura'] += 1
                self.dicinstrucoes['total'] += 1
                resultado += child.value
                self.nodeStatement += child.value + ' '
            elif isinstance(child, Token) and child.type == 'PRINT':
                self.fHtml.write(child.value)
                self.instrucaoAtual = "escrita"
                self.dicinstrucoes['escrita'] += 1
                self.dicinstrucoes['total'] += 1
                resultado += child.value
                self.nodeStatement += child.value + ' '
            elif isinstance(child,Token): 
                self.fHtml.write(child.value)
                resultado += child.value
                if child.value not in [';','(',')','{','}']:
                  self.nodeStatement += child.value
                  if child.type == 'NUM' and estruturaCiclica:
                    cicleNode = str(self.statementCount)
                    self.dot.node(cicleNode,label=self.nodeStatement)
                    self.dot.edge(self.lastStatement,cicleNode)
                    self.lastStatement = str(self.statementCount)
                    self.statementCount += 1
                    self.nodeStatement = ''
            elif isinstance(child, Tree) and child.data == 'atribuicao':
                self.instrucaoAtual = "atribuicao"
                self.dicinstrucoes['atribuicoes'] += 1
                self.dicinstrucoes['total'] += 1
                res = str(self.visit(child))
                resultado += res
                if isFor and contadorAtribuicoes == 0:
                  #Atribuição do for
                  self.dot.node(str(self.statementCount),label=self.nodeStatement)
                  initialAtribForNode = str(self.statementCount)
                  self.statementCount += 1
                  self.nodeStatement = ''
                elif isFor and contadorAtribuicoes == 1:
                  #Incrementação do for
                  self.dot.node(str(self.statementCount),label=self.nodeStatement)
                  incrementNode = str(self.statementCount)
                  self.statementCount += 1
                  self.nodeStatement = ''
                contadorAtribuicoes += 1
            elif isinstance(child, Tree):
                if child.data == 'conteudoread':
                    res = str(self.visit(child))
                    resultado += res
                elif child.data == 'logic':
                    res = str(self.visit(child))
                    resultado += res
                    self.nodeStatement += res
                elif child.data == 'condicao':
                    res = str(self.visit(child))
                    resultado += res
                    if estruturaCiclica:
                      if isFor:
                        #Ligar a última instrução antes do for à primeira atrib do for
                        self.dot.edge(self.lastStatement,initialAtribForNode)
                        #Ligar a primeir atrib ao for
                        cicleNode = str(self.statementCount)
                        self.nodeStatement = 'for ' + self.nodeStatement
                        self.dot.node(cicleNode,label=self.nodeStatement)
                        self.dot.edge(initialAtribForNode,cicleNode)
                        self.lastStatement = str(self.statementCount)
                        self.statementCount += 1
                        self.nodeStatement = ''
                      else:
                        cicleNode = str(self.statementCount)
                        self.dot.node(cicleNode,label=self.nodeStatement)
                        self.dot.edge(self.lastStatement,cicleNode)
                        self.lastStatement = str(self.statementCount)
                        self.statementCount += 1
                        self.nodeStatement = ''
                elif child.data == 'instrucoes':
                    self.nivelProfundidade += 1
                    self.nivelIf = 0
                    res = str(self.visit(child))
                    resultado += res
                    self.nivelIf = nivelIf
                    self.nivelProfundidade = nivelProfundidade
                    #self.nodeStatement += res

    #Se a lista de condições tiver mais do que um elemento então podemos aninhar os ifs
    if len(condicoesParaAninhar) > 1:
      alternativaIf = 'if(' + condicoesParaAninhar[0]
      for cond in condicoesParaAninhar[1:]:
        alternativaIf += ' && ' + cond
      alternativaIf += '){\n' + numTabs + '\t\t'
      alternativaIf += corpo
      alternativaIf += '\n' + numTabs + '}'
      #print('ALTERNATIVA PARA O IF: ', alternativaIf)
      self.alternativasIfs.append(alternativaIf)
    self.fHtml.write('\n')

    #Verificar se há um novo statement para adicionar ao grafo
    #Se existir um ciclo...
    if cicleNode != '':
        if isFor:
          #Ligar a última instrução dentro do ciclo à atribuição de incrementação
          self.dot.edge(self.lastStatement, incrementNode)
          #Ligar a incrementação ao for
          self.dot.edge(incrementNode,cicleNode)
        else:
          #Ligar a última instrução dentro do ciclo ao próprio ciclo
          self.dot.edge(self.lastStatement,cicleNode)
        #Ligar o ciclo ao fim de ciclo
        self.dot.node(str(self.statementCount),label='fimCiclo' + str(self.dicinstrucoes['ciclicas']))
        self.dot.edge(cicleNode,str(self.statementCount))
        self.lastStatement = str(self.statementCount)
        self.nodeStatement = ''
        self.statementCount += 1

    #Se não existir um if e houver um statement para escrever...
    if self.nodeStatement != '' and ifNode == '':
      self.dot.node(str(self.statementCount),label=self.nodeStatement)
      self.dot.edge(self.lastStatement,str(self.statementCount))
      self.lastStatement = str(self.statementCount)
      self.nodeStatement = ''
      self.statementCount += 1
    #Se existir um if...
    elif ifNode != '':
      self.dot.edge(localLastStatement,ifNode)
      self.lastStatement = endifNode
      self.nodeStatement = ''
      if not existeElse:
        self.dot.edge(ifNode,endifNode)
    return resultado
    
  def condicao(self,tree):
    r = self.visit_children(tree)
    self.nodeStatement += str(r[0])
    return r
    #print('CONDICAO: ', r)
    
  def atribuicao(self,tree):
    res = ''
    for child in tree.children:
      if (isinstance(child,Token) and child.type == 'VAR') and child.value in self.naoInicializadas:
        self.fHtml.write(child.value)
        self.naoInicializadas.remove(child.value)
        res += child.value
        self.nodeStatement += child.value
      elif (isinstance(child,Token) and child.type == 'VAR') and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
        res += '<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>'
        self.nodeStatement += child.value
      elif (isinstance(child,Token) and child.type == 'VAR'):
        self.fHtml.write(child.value)
        res += child.value
        self.nodeStatement += child.value
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
        res += str(child.value)
        self.nodeStatement += child.value
      elif isinstance(child,Tree) and child.data == 'chave':
        chave = self.visit(child)
        self.fHtml.write(str(chave))
        res += str(chave)
        self.nodeStatement += str(chave)
      elif isinstance(child,Tree):
        r = str(self.visit(child))
        res += r
        self.nodeStatement += r
    return res
  
  def conteudoread(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and child.type == 'VAR' and child.value in self.naoInicializadas:
        self.fHtml.write(child.value)
        self.naoInicializadas.remove(child.value)
        self.utilizadas.add(child.value)
        res += child.value
        self.nodeStatement += child.value
      elif isinstance(child,Token) and child.type == 'VAR' and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
        res += '<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>'
        self.nodeStatement += child.value
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
        res += str(child.value)
        self.nodeStatement += str(child.value)
      elif isinstance(child,Tree) and child.data == 'chave':
        chave = str(self.visit(child))
        self.fHtml.write(chave)
        res += chave
        self.nodeStatement += chave
    return res

  def tipo(self, tree):
    return str(tree.children[0])

  def logic(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'logicnot':
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
      elif isinstance(child,Tree):
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
    return res

  def logicnot(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'relac':
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
      elif isinstance(child,Tree):
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
    return res

  def relac(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and (child.value == '<' or child.value == '>' or child.value == '<=' or child.value == '>=' or child.value == '==') and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(' ' + child.value + ' ')
      elif isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'exp':
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
      elif isinstance(child,Tree):
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
    return res

  def exp(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'termo':
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
      elif isinstance(child,Tree):
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
    return res

  def termo(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'factor':
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
      elif isinstance(child,Tree):
        visit = self.visit(child)
        if visit != None:
          res += str(visit)
    return res

  def factor(self, tree):
    for child in tree.children:
      if isinstance(child, Token) and child.type == 'VAR' and len(tree.children) > 1:
        self.utilizadas.add(child.value)
        chave = self.visit(tree.children[2])
        if self.nasInstrucoes and child.value not in self.decls.keys():
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span>\</div>' + '[' + str(chave) + ']')
          self.erros['1: Não-declaração'].add(child.value)
        elif self.nasInstrucoes and child.value in self.naoInicializadas:
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não inicializada</span></div>' + '[' + str(chave) + ']')
          self.erros['3: Usado mas não inicializado'].add(child.value)
        elif self.nasInstrucoes:
          self.fHtml.write(child.value)
          self.fHtml.write('[' + str(chave) + ']')
        return str(child.value) + '[' + str(chave) + ']'
      elif isinstance(child, Token) and child.type == 'VAR':
        if self.nasInstrucoes and child.value not in self.decls.keys():
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
          self.erros['1: Não-declaração'].add(child.value)
        elif self.nasInstrucoes and child.value in self.naoInicializadas:
          self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não inicializada</span></div>')
          self.erros['3: Usado mas não inicializado'].add(child.value)
        elif self.nasInstrucoes:
          self.fHtml.write(child.value)
        #Adicionar a variável à lista das utilizadas
        self.utilizadas.add(child.value)
        return str(child.value)
      elif isinstance(child, Tree) and child.data == 'chave':
        #Obter o índice da estrutura se existir
        chave = self.visit(child)
        if self.nasInstrucoes:
          self.fHtml.write(chave)
      elif isinstance(child, Token) and child.type == 'NUM':
        if self.nasInstrucoes:
          self.fHtml.write(child.value)
        return int(child.value)
      elif isinstance(child, Token) and child.type == 'BOOLEANO':
        if self.nasInstrucoes:
          self.fHtml.write(child.value)
        if child.value == "False":
          return False
        elif child.value == "True":
          return True
      elif isinstance(child, Token) and child.type == 'STRING':
        if self.nasInstrucoes:
          self.fHtml.write(child.value)
        return str(child.value)
      elif isinstance(child, Token) and child.type == 'NUMDOUBLE':
        if self.nasInstrucoes:
          self.fHtml.write(child.value)
        return float(child.value)
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'PDR':
        if self.nasInstrucoes:
          self.fHtml.write('[]')
        return list()
      elif isinstance(child, Token) and child.type == 'PER' and isinstance(tree.children[1], Tree):
        lista = None
        if self.nasInstrucoes:
          self.fHtml.write('[')
          lista = self.visit(tree.children[1])
          self.fHtml.write(']')
        else:
          lista = self.visit(tree.children[1])
        return lista
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'CD':
        if self.nasInstrucoes:
          self.fHtml.write("{}")
        return {}
      elif isinstance(child, Token) and child.type == 'CE' and isinstance(tree.children[1], Tree):
        estrutura = None
        if self.nasInstrucoes:
          self.fHtml.write('{')
          estrutura = self.visit(tree.children[1])
          self.fHtml.write('}')
        else:
          estrutura = self.visit(tree.children[1])
        if isinstance(estrutura,dict):
          return estrutura
        else:
          return set(estrutura)
      elif isinstance(child, Token) and child.type == 'PE' and isinstance(tree.children[1], Token) and (tree.children[1]).type == 'PD':
        if self.nasInstrucoes:
          self.fHtml.write('()')
        return tuple()
      elif isinstance(child, Token) and child.type == 'PE' and isinstance(tree.children[1], Tree):
        tuplo = None
        if self.nasInstrucoes:
          self.fHtml.write('(')
          tuplo = self.visit(tree.children[1])
          self.fHtml.write(')')
        else:
          tuplo = self.visit(tree.children[1])
        return tuple(tuplo)
      elif isinstance(child,Token) and self.nasInstrucoes:
        self.fHtml.write(child.value)
      
  def conteudoespecial(self,tree):
    r = self.visit(tree.children[0])
    return r
  
  def conteudodicionario(self,tree):
    estrutura = dict()
    i = 0
    for child in tree.children:
      if i == 0 and isinstance(child, Tree):
        entrada = self.visit(child)
        chave = entrada[0][1:-1]
        estrutura[chave] = entrada[2]
      elif isinstance(child, Tree):
        if self.nasInstrucoes:
          self.fHtml.write(',')
          entrada = self.visit(child)
          chave = entrada[0][1:-1]
          estrutura[chave] = entrada[2]
        else:
          entrada = self.visit(child)
          chave = entrada[0][1:-1]
          estrutura[chave] = entrada[2]
      i += 1
    return estrutura

  def entrada(self,tree):
    res = []
    for child in tree.children:
      if self.nasInstrucoes and isinstance(child,Token):
        self.fHtml.write(child.value)
        res.append(child.value)
      elif isinstance(child,Token):
        res.append(child.value)
      elif isinstance(child,Tree):
        r = self.visit(child)
        res.append(r)
    return res
        
  def conteudo(self, tree):
    # print('Entrei no conteúdo de uma estrutura...')
    res = list()
    i = 0
    for child in tree.children:
      if i == 0 and isinstance(child, Tree):
        r = self.visit(child)
        res.append(r)
      elif isinstance(child, Tree):
        r = None
        if self.nasInstrucoes:
          self.fHtml.write(',')
          r = self.visit(child)
        else:
          r = self.visit(child)
        res.append(r)
      i += 1
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

data = LinguagemProgramacao().visit(tree)
print('-'*100)
print('Output: ', data)
print('-'*100)