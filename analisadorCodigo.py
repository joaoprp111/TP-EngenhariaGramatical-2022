from errno import ESOCKTNOSUPPORT
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
  <head>
    <meta charset="UTF-8">
    <title>Análise Estática</title>
  </head>
  <style>
    .info {
      position: relative;
      display: inline-block;
      border-bottom: 1px dotted black;
      color: rgb(142, 142, 248);
    }
    .info .infotext {
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
    .info .infotext::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 20%;
      margin-left: -5px;
      border-width: 5px;
      border-style: solid;
      border-color: #555 transparent transparent transparent;
    }
    .info:hover .infotext {
      visibility: visible;
      opacity: 1;
    }
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
    <pre>
        <code>'''
  ficheiro.write(conteudo + '\n')
  
def preencherFim(ficheiro):
  conteudo = '''
      </code>
    </pre>
  </body>
</html>'''
  ficheiro.write(conteudo)
  
def criarSegundaPagina(dicionario,ficheiro):
  inicio = '''
  <!DOCTYPE html>
  <html lang="pt">
  <head>
    <link rel="stylesheet" href="w3.css">
    <meta charset="UTF-8">
    <title>Informações</title>
  </head>
  <body class="w3-container">
  '''
  
  #Variáveis e os tipos
  ficheiro.write(inicio)
  ficheiro.write('\t<h2>Variáveis declaradas e os seus tipos</h2>\n')
  ficheiro.write('\t<table class="w3-table-all">\n\t\t<tr>\n')
  ficheiro.write('\t\t\t<th>Variável</th>\n')
  ficheiro.write('\t\t\t<th>Tipo</th>\n')
  ficheiro.write('\t\t</tr>\n')
  for k,v in dicionario['decls'].items():
    ficheiro.write('\t\t<tr>\n')
    ficheiro.write('\t\t\t<td>' + k + '</td>\n')
    ficheiro.write('\t\t\t<td>' + v + '</td>\n')
    ficheiro.write('\t\t</tr>\n')
  ficheiro.write('\t</table>\n')
  
  ficheiro.write('\t<h2>Outras informações sobre as variáveis</h2>\n')
  ficheiro.write('\t<ul class="w3-ul">\n')
  
  naoInicializadas = dicionario['naoInicializadas']
  if len(naoInicializadas) > 0:
    ficheiro.write('\t\t<li><b>Variáveis sem inicialização: </b>' + str(naoInicializadas) + '</li>\n')
  else:
    ficheiro.write('\t\t<li><b>Variáveis sem inicialização: </b>Nenhuma</li>\n')
    
  naoDeclaradas = dicionario['erros']['1: Não-declaração']
  if len(naoDeclaradas) > 0:
    ficheiro.write('\t\t<li><b>Variáveis não declaradas: </b>' + str(naoDeclaradas) + '</li>\n')
  else:
    ficheiro.write('\t\t<li><b>Variáveis não declaradas: </b>Nenhuma</li>\n')
    
  redeclaradas = dicionario['erros']['2: Redeclaração']
  if len(redeclaradas) > 0:
    ficheiro.write('\t\t<li><b>Variáveis redeclaradas: </b>' + str(redeclaradas) + '</li>\n')
  else:
    ficheiro.write('\t\t<li><b>Variáveis redeclaradas: </b>Nenhuma</li>\n')
    
  usadasNaoInicializadas = dicionario['erros']['3: Usado mas não inicializado']
  if len(usadasNaoInicializadas) > 0:
    ficheiro.write('\t\t<li><b>Variáveis usadas e não inicializadas: </b>' + str(usadasNaoInicializadas) + '</li>\n')
  else:
    ficheiro.write('\t\t<li><b>Variáveis usadas e não inicializadas: </b>Nenhuma</li>\n')
    
  nuncaMencionadas = dicionario['erros']['4: Declarado mas nunca mencionado']
  if len(nuncaMencionadas) > 0:
    ficheiro.write('\t\t<li><b>Variáveis declaradas mas nunca mencionadas: </b>' + str(nuncaMencionadas) + '</li>\n')
  else:
    ficheiro.write('\t\t<li><b>Variáveis declaradas mas nunca mencionadas: </b>Nenhuma</li>\n')
  ficheiro.write('\t</ul>\n')
    
  ficheiro.write('\t<h2>Informações sobre as instruções</h2>\n')
  ficheiro.write('\t<ul class="w3-ul">\n')
  ficheiro.write('\t\t<li><b>Total de instruções: </b>' + str(dicionario['instrucoes']['total']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de atribuições: </b>' + str(dicionario['instrucoes']['atribuicoes']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de leituras: </b>' + str(dicionario['instrucoes']['leitura']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de escritas: </b>' + str(dicionario['instrucoes']['escrita']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de instruções condicionais: </b>' + str(dicionario['instrucoes']['condicionais']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de instruções cíclicas: </b>' + str(dicionario['instrucoes']['ciclicas']) + '</li>\n')
  ficheiro.write('\t\t<li><b>Total de situações de aninhamento: </b>' + str(dicionario['totalSituacoesAn']) + '</li>\n')
  ficheiro.write('\t</ul>\n')
  
  ficheiro.write('\t<h2>Informações sobre os ifs e os seus aninhamentos</h2>\n')
  ficheiro.write('\t<h4>Níveis de aninhamento dos ifs</h4>\n')
  ficheiro.write('\t<ul class="w3-ul">\n')
  niveis = dicionario['niveisIf']
  for k, v in niveis.items():
    ficheiro.write('\t\t<li><b>Nível ' + str(k) + ': </b>Ifs pela ordem em que aparecem no código - ' + str(v) + '</li>\n')
  ficheiro.write('\t</ul>\n')
  
  alternativas = dicionario['alternativasIfs']
  if len(alternativas) > 0:
    ficheiro.write('\t<h4>Alternativa para os ifs aninhados</h4>\n')
    for a in alternativas:
      ficheiro.write('\t<p>' + str(a) + '</p>\n')
  
    
  

class LinguagemProgramacao(Interpreter):

  def __init__(self):
    self.fHtml = criarFicheiroHtml('codigoAnotado.html')
    self.f2Html = criarFicheiroHtml('informacoesAdicionais.html')
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
    self.visit(tree.children[0]) #Declarações
    self.nasInstrucoes = True
    self.fHtml.write(' '*10 + '<div class="instrucoes">\n')
    self.visit(tree.children[1]) #Instruções
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
      elif  isinstance(child, Token) and child.type == 'VAR':
        var = child.value
        self.fHtml.write(var)
      elif isinstance(child, Tree) and child.data == 'tipo': #Visita o tipo da declaração
        tipo = self.visit(child)
        self.fHtml.write(tipo + ' ')
      elif isinstance(child, Token) and child.type == 'ATRIB': #Se houver atribuição visita o valor que está a ser declarado
        valor = self.visit(tree.children[3])
        if valor == None:
          self.naoInicializadas.add(var)
          self.decls[var] = tipo
          self.fHtml.write(';\n')
        elif isinstance(valor,str) and valor[0] != '"':
          self.fHtml.write(' = ')
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
          elif valor not in self.decls.keys(): #Verificar se a variável atómica já existe
            self.erros['1: Não-declaração'].add(valor)
            self.fHtml.write('<div class="error">' + valor + '<span class="errortext">Variável redeclarada</span></div>;\n')
        else:
          self.fHtml.write(' = ')
          self.fHtml.write(str(valor) + ';\n')
          
    if valor == None: #Caso nunca tenha existido atribuição na declaração
      self.naoInicializadas.add(var)
      self.decls[var] = tipo
      self.fHtml.write(';\n')
      
    self.decls[var] = tipo

  def instrucoes(self, tree):
    r = self.visit_children(tree)
    return r

  def instrucao(self, tree):
    instrucaoAtual = self.instrucaoAtual
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
                if len(tree.children[5].children) > 0: #Se existirem instruções dentro do if
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
                if self.nivelProfundidade > 0:
                    self.totalSituacoesAn += 1
                self.fHtml.write(child.value)
                self.dicinstrucoes['ciclicas'] += 1
                self.dicinstrucoes['total'] += 1
                self.instrucaoAtual = "ciclo"
                resultado += child.value
            elif isinstance(child, Token) and child.type == 'READ':
                self.fHtml.write(child.value)
                self.instrucaoAtual = "leitura"
                self.dicinstrucoes['leitura'] += 1
                self.dicinstrucoes['total'] += 1
                resultado += child.value
            elif isinstance(child, Token) and child.type == 'PRINT':
                self.fHtml.write(child.value)
                instrucaoAtual = self.instrucaoAtual = "escrita"
                self.dicinstrucoes['escrita'] += 1
                self.dicinstrucoes['total'] += 1
                resultado += child.value
            elif isinstance(child,Token): 
                self.fHtml.write(child.value)
                resultado += child.value
            elif isinstance(child, Tree) and child.data == 'atribuicao':
                instrucaoAtual = self.instrucaoAtual = "atribuicao"
                self.dicinstrucoes['atribuicoes'] += 1
                self.dicinstrucoes['total'] += 1
                resultado += str(self.visit(child))
            elif isinstance(child, Tree):
                if child.data == 'conteudoread':
                    resultado += str(self.visit(child))
                elif child.data == 'logic':
                    resultado += str(self.visit(child))
                elif child.data == 'condicao':
                    resultado += str(self.visit(child))
                elif child.data == 'instrucoes':
                    self.nivelProfundidade += 1
                    self.nivelIf = 0
                    resultado += str(self.visit(child))
                    self.nivelIf = nivelIf
                    self.nivelProfundidade = nivelProfundidade

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
    return resultado
    
  def condicao(self,tree):
    r = self.visit_children(tree)
    return r
    #print('CONDICAO: ', r)
    
  def atribuicao(self,tree):
    res = ''
    for child in tree.children:
      if (isinstance(child,Token) and child.type == 'VAR') and child.value in self.naoInicializadas:
        self.fHtml.write(child.value)
        self.naoInicializadas.remove(child.value)
        res += child.value
      elif (isinstance(child,Token) and child.type == 'VAR') and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
        res += '<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>'
      elif (isinstance(child,Token) and child.type == 'VAR'):
        self.fHtml.write(child.value)
        res += child.value
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'chave':
        chave = self.visit(child)
        self.fHtml.write(str(chave))
        res += str(chave)
      elif isinstance(child,Tree):
        res += str(self.visit(child))
    return res
  
  def conteudoread(self,tree):
    res = ''
    for child in tree.children:
      if isinstance(child,Token) and child.type == 'VAR' and child.value in self.naoInicializadas:
        self.fHtml.write(child.value)
        self.naoInicializadas.remove(child.value)
        self.utilizadas.add(child.value)
        res += child.value
      elif isinstance(child,Token) and child.type == 'VAR' and child.value not in self.decls.keys():
        self.fHtml.write('<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>')
        res += '<div class="error">' + child.value + '<span class="errortext">Variável não declarada</span></div>'
      elif isinstance(child,Token):
        self.fHtml.write(child.value)
        res += str(child.value)
      elif isinstance(child,Tree) and child.data == 'chave':
        chave = str(self.visit(child))
        self.fHtml.write(chave)
        res += chave
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
#print(tree.pretty())

data = LinguagemProgramacao().visit(tree)
print('-'*100)
print('Output: ', data)
print('-'*100)