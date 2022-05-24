def criarFicheiro(nome):
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
      
def eDigito(palavra):
  res = True
  i = 0
  size = len(palavra)
  while res and i < size:
    if palavra[i] < "0" or palavra[i] > "9":
      res = False
    i += 1
  return res