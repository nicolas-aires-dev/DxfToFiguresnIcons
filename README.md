# DxfToFiguresnIcons  
Conversor que transforma polilinhas de arquivos DXF em imagens (ícones/figuras).  

## 🎯 Visão Geral  
Este projeto permite que você pegue entidades de polilinhas de um arquivo DXF (formato CAD) e converta para imagens raster (por exemplo PNG) ou ícones(BMP), facilitando a reutilização em interfaces, relatórios, ou outros contextos visuais.  

## ✅ Funcionalidades  
- Leitura de arquivos DXF que contêm polilinhas.  
- Conversão das polilinhas em imagem (PNG) com fundo transparente ou definido.  
- Interface gráfica simples (via `Tool_GUI.py`) para operar sem necessidade de linha de comando.  
- Configuração de parâmetros (tamanho da imagem, cor da linha, cor de fundo, espessura, escala) para personalização.  
- Saída de imagem para cada figura processada.

## 🛠️ Como usar  
### Pré-requisitos  
- Python 3.x  
- Dependências listadas em `requirements.txt` (por exemplo: ezdxf, pillow, numpy — adapte conforme seu environment)  

## 🧩 Requisitos para o arquivo DXF
Para que a conversão funcione corretamente, o arquivo DXF deve seguir as regras abaixo:

### 🔹 Estrutura e Layers
- Todos os objetos a serem convertidos devem estar na **layer `PERFIS`**.  
- Cada objeto (perfil) deve estar **consideravelmente separado dos demais**, para que o recorte automático consiga identificar os limites de cada figura sem sobreposição.  
  - Não é necessário um espaçamento ENORME, apenas o suficiente para evitar contato entre bordas.  

### 🔹 Nomes e Cotas
- O **nome do perfil** deve estar em **formato `SIMPLETEXT`**, posicionado **dentro do objeto** ou **muito próximo** dele.  
  - Isso garante que o nome seja incluído dentro do recorte gerado.  
- As **cotas** só são detectadas se forem algum tipo de **entidade `DIM` (Dimension)**.  
  - Outras entidades de texto ou anotação não são consideradas neste momento.  

### 🔹 Tipos de Entidades Suportadas
- O conversor trabalha apenas com **entidades vetoriais simples** (`LWPOLYLINE`, `POLYLINE`).  
- **Curvas** (`ARC`, `SPLINE`, `ELLIPSE`) ainda não são suportadas e terão o preenchimento ignorado.  

> ⚠️ **Importante:** Se os nomes, cotas e objetos estiverem distantes ou em layers diferentes, o aplicativo pode gerar imagens incompletas ou ignorar elementos.

> ⚠️ Caso as regras acima não sejam seguidas, o aplicativo pode ignorar certos elementos ou gerar recortes incorretos.


### ⚠️ Limitações Conhecidas
- Curvas (arcos, splines e elipses) ainda não são processadas.
- Apenas polilinhas são renderizadas corretamente.


### Instalação  
```bash
git clone https://github.com/nicolas-aires-dev/DxfToFiguresnIcons.git  
cd DxfToFiguresnIcons  
pip install -r requirements.txt  
```

## Uso

## Via GUI
```bash
python Tool_GUI.py
```

- Abra o arquivo DXF desejado.
- Ajuste parâmetros (escala, cores, espessura, tamanho da imagem).
- Execute a conversão.
- As imagens geradas serão salvas em uma pasta de saída (defina ou padrão).

## Via Script (Exemplo)
```bash
python main.py --input arquivo.dxf --output pasta_saida --scale 2.0 --line_color #FF0000 --bg_color transparent
```

## 📂 Estrutura do Projeto
```graphql
/DxfToFiguresnIcons
│  Tool_GUI.py        # Interface gráfica
│  main.py            # Script principal de conversão
│  requirements.txt   # Dependências do Python
│  .gitignore
└─ input/             # (opcional) arquivos DXF de exemplo
└─ output/            # (opcional) resultados de imagens geradas
```

## 🧪 Arquivo de Teste
O repositório já inclui um exemplo em `/input/ProfilesExample.dxf` para facilitar os testes.  
Basta abrir este arquivo na interface gráfica (`Tool_GUI.py`) ou usar via linha de comando:  

```bash
python main.py --input ./input/ProfilesExample.dxf--output ./output
```

## ⚠️ Limitações Conhecidas
Atualmente, o conversor possui algumas limitações que estão sendo trabalhadas:
- Perfis que contêm **curvas (arcos, splines, elipses)** podem não ser renderizados corretamente ou ser ignorados durante a conversão.
- Apenas **polilinhas** (LWPOLYLINE/POLYLINE) são tratadas de forma estável no momento.
- A escala automática para perfis muito inclinados ainda precisa de ajustes finos.

## 🚧 Próximos Passos / Planejamento
- [ ] Implementar suporte a **curvas (arcos e splines)**.
- [ ] Melhorar o cálculo automático de **zoom/escala** para perfis com ângulos extremos.
- [ ] Adicionar suporte a exportação em **SVG** e **ICO**.
- [ ] Criar sistema de logs para depuração.
- [ ] Adicionar testes automatizados e exemplos visuais.
- [ ] Adicionar scripts de adaptação de perfis/objetos fora do padrão conhecido pelo app.

## 📌 Por que usar este projeto?
- Automatiza a tarefa repetitiva de converter desenhos CAD (polilinhas) em iconografia ou figuras para sistemas ou relatórios.
- Ideal para engenheiros, desenhistas, desenvolvedores que precisam integrar imagens geradas a partir de diagramas CAD em sistemas Web ou mobile.
- Permite padronização visual (cores, espessura, tamanhos) para consistência de ícones/fíguras.

## 🤝 Contribuições
Contribuições são bem-vindas! Se você encontrar bugs, tiver sugestões de melhoria ou quiser adicionar novos formatos de saída (SVG, PDF, etc), fique à vontade para abrir issue ou pull request.

## 📄 Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🧑‍💻 Autor
Desenvolvido por [Nicolas Aires](https://www.linkedin.com/in/n%C3%ADcolas-aires-a498195b?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app).
Para dúvidas, sugestões ou colaborações, entre em contato pelo GitHub ou LinkedIN!
