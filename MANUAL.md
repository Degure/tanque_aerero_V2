# Manual do Sistema de Propostas Comerciais  
**Casa do Frentista · GP Company**

Este documento explica a estrutura do projeto, como cadastrar produtos, imagens e opcionais, como funcionam os cálculos e como manter o código no dia a dia.

---

## 1. Visão geral

O sistema gera orçamentos e propostas comerciais em PDF para tanques aéreos, bacias, bombas, filtros e itens opcionais.

| Arquivo / pasta | Função |
|-----------------|--------|
| `app.py` | Interface web (Streamlit): formulário, cálculos em tela, botão de PDF |
| `data.py` | **Cadastro central**: preços, medidas, pesos, opcionais, caminhos de imagens, textos da empresa |
| `pdf_generator.py` | Montagem do PDF (layout, tabelas, imagens, condições comerciais) |
| `vendedores.json` | Lista de vendedores (editável pela tela ou pelo arquivo) |
| `logo_casa.png` / `logo_gp.png` | Logos no cabeçalho do PDF |
| `imagens_produtos/` | Fotos dos produtos (tanques, bacias, bombas, filtros, opcionais) |
| `requirements.txt` | Dependências Python |
| `README.md` | Resumo de instalação e deploy |

**Regra de ouro:** quase tudo que é “dado de negócio” (preço, medida, nome de produto, foto) fica em **`data.py`**. A interface (`app.py`) e o PDF (`pdf_generator.py`) só leem esses dados.

---

## 2. Como rodar o sistema

### Local (Windows)
```cmd
cd "C:\Users\Usuario\Desktop\FINANCEIRO\PROJETOS\TANQUE AEREO"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud
1. Suba o projeto no GitHub (pastas + arquivos).  
2. Em [share.streamlit.io](https://share.streamlit.io) → New app → repositório → Main file: `app.py` → Deploy.

---

## 3. Cadastrar / alterar produtos

Tudo em **`data.py`**.

### 3.1 Tanques

Dicionário `TANQUES`. Cada chave é o nome que aparece no selectbox.

```python
TANQUES = {
    "10.000L": {
        "preco": 18590.0,       # preço padrão (R$)
        "diametro": "1.900mm",  # aparece na tela e no PDF
        "comprimento": "3.600mm",
        "chapa": "3.00mm",
        "peso": 950,            # kg
        "label": "10.000L",
    },
    # novo tanque:
    "8.000L": {
        "preco": 15000.0,
        "diametro": "1.700mm",
        "comprimento": "3.200mm",
        "chapa": "3.00mm",
        "peso": 850,
        "label": "8.000L",
    },
}
```

**O que fazer ao incluir um tanque novo**
1. Adicionar a entrada em `TANQUES` (como acima).  
2. (Opcional) Associar foto em `IMAGEM_POR_TANQUE` (ver seção 4).  
3. Salvar e reiniciar o Streamlit (ou esperar o Cloud atualizar).

Não é necessário alterar `app.py` nem `pdf_generator.py` para um tanque novo com a mesma estrutura.

### 3.2 Bacias

Dicionário `BACIAS` — mesmo padrão.

```python
BACIAS = {
    "SEM BACIA": {
        "preco": 0.0,
        "largura": "—", "altura": "—", "comprimento": "—",
        "chapa": "—", "peso": 0, "label": "SEM BACIA",
    },
    "10.000L": {
        "preco": 16485.0,
        "largura": "2.400mm",
        "altura": "1.180mm",
        "comprimento": "4.500mm",
        "chapa": "2.65mm",
        "peso": 900,
        "label": "10.000L",
    },
}
```

Sempre mantenha a opção `"SEM BACIA"` com preço 0.

### 3.3 Bombas

Dicionário simples nome → preço:

```python
BOMBAS = {
    "SEM BOMBA": 0.0,
    "BOMBA ABASTECIMENTO 60LPM - 220V": 2299.0,
    "NOVA BOMBA XYZ 80LPM": 4500.0,  # exemplo
}
```

O **nome da chave** é o que aparece no orçamento e no PDF. Use o texto completo e correto.

### 3.4 Filtros e elementos filtrantes

```python
FILTROS = {
    "SEM FILTRO": 0.0,
    "FOGUETINHO DESIDATRADOR 100LPM": 4190.0,
}

ELEMENTOS = {
    "SEM ELEMENTO": 0.0,
    "ELEMENTO FILTRANTE 1'' DESIDATRADOR - 4UN": 190.0,
}
```

### 3.5 Produtos opcionais (checkbox)

Dicionário `OPCIONAIS`:

```python
OPCIONAIS = {
    "DESCARGA SELADA 4''": {
        "preco": 3500.0,
        "descricao": (
            "Abastecimento do combustível no tanque realizado por baixo, "
            "pela válvula. Caso não opte por esta forma, o abastecimento "
            "será pela parte superior do tanque."
        ),
        # Preferir nome de arquivo SEM espaços e SEM aspas:
        "imagem": "imagens_produtos/opcionais/descarga_selada_4.jpg",
    },
    "ESCADA EXTERNA": {
        "preco": 1200.0,
        "descricao": "Escada metálica externa para acesso ao topo do tanque.",
        "imagem": None,  # ou caminho da foto
    },
}
```

- Cada item vira um **checkbox** na tela.  
- A `descricao` sai **completa** no PDF.  
- `imagem` é opcional; se o arquivo existir, entra no preview e no PDF.

---

## 4. Imagens

### 4.1 Estrutura de pastas

```
imagens_produtos/
├── tanques/      ← fotos dos tanques
├── bacias/       ← fotos das bacias
├── bombas/       ← fotos das bombas
├── filtros/      ← fotos dos filtros
└── opcionais/    ← fotos dos itens opcionais
```

Formatos: **PNG** ou **JPG/JPEG**.

### 4.2 Associar foto ao produto

Em `data.py`:

```python
IMAGEM_POR_TANQUE = {
    "10.000L": "imagens_produtos/tanques/tanque_horizontal_1.png",
    "20.000L": "imagens_produtos/tanques/tanque_bacia_1.png",
}

IMAGEM_POR_BACIA = {
    "SEM BACIA": None,
    "10.000L": "imagens_produtos/bacias/bacia_com_tanque.png",
}

IMAGEM_POR_BOMBA = {
    "SEM BOMBA": None,
    "BOMBA ABASTECIMENTO 60LPM - 220V": "imagens_produtos/bombas/bomba_60lpm.jpg",
}

IMAGEM_POR_FILTRO = {
    "SEM FILTRO": None,
    "FOGUETINHO DESIDATRADOR 100LPM": "imagens_produtos/filtros/foguetinho_100.jpg",
}
```

**A chave do dicionário deve ser idêntica** à chave de `TANQUES` / `BOMBAS` / etc.

### 4.3 Dicas de arquivo

| Evite | Prefira |
|-------|---------|
| `opcional-descarga selada 4''.jpeg` | `descarga_selada_4.jpg` |
| Espaços e aspas no nome | Underscore `_` e letras/números |

Se a imagem não aparecer, a tela mostra:  
`⚠️ Imagem não encontrada: caminho...`  
Confira se o caminho no `data.py` é igual ao caminho real do arquivo.

### 4.4 Logos

- `logo_casa.png` — Casa do Frentista  
- `logo_gp.png` — GP Company  

Coloque na **raiz** do projeto (mesmo nível do `app.py`).

---

## 5. Cálculos e dimensionamento

### 5.1 O que o sistema calcula automaticamente

| Cálculo | Fórmula / origem |
|---------|------------------|
| Preço unitário | Valor do cadastro em `data.py` (editável na tela) |
| Total de cada item | `qtd × unitário` |
| Total produtos | Soma de todos os itens (tanque, bacia, bomba, filtro, elemento, opcionais, avulso) |
| Desconto à vista | `total_produtos × (desconto_% / 100)` — % padrão 5, editável |
| Valor à vista | `total_produtos − desconto` |
| Total com frete | `valor_à_vista + frete` (frete não entra no desconto) |
| Peso aproximado | `peso_tanque + peso_bacia` (campos `peso` em `data.py`) |
| Parcelas | Cada etapa: `base × (pct / 100)` |

**Base das parcelas** (escolha na tela):
- Valor **à prazo** (sem desconto) + frete, ou  
- Valor **à vista** (com desconto) + frete  

### 5.2 Dimensionamento (medidas e peso)

As medidas **não são calculadas por fórmula** no código atual. Elas vêm cadastradas em `data.py`:

- Tanque: `diametro`, `comprimento`, `chapa`, `peso`  
- Bacia: `largura`, `altura`, `comprimento`, `chapa`, `peso`  

Ao selecionar o volume, a tela e o PDF leem esses campos.

Se no futuro houver fórmula de dimensionamento (ex.: volume a partir de diâmetro × comprimento), o lugar natural é:

1. Função em `data.py` ou em um novo `calculos.py`  
2. Chamada no `app.py` ao montar o resumo / itens  
3. Uso dos resultados no `pdf_generator.py` nas especificações técnicas  

Exemplo de estrutura futura:

```python
# calculos.py (ideia para evolução)
def volume_cilindro_litros(diametro_mm: float, comprimento_mm: float) -> float:
    import math
    r = diametro_mm / 2 / 1000  # metros
    h = comprimento_mm / 1000
    return math.pi * r * r * h * 1000  # litros
```

### 5.3 Preços editáveis na tela

Mesmo com preço cadastrado, o vendedor pode alterar o valor nos campos numéricos (desconto por item, promoção etc.). O que vale para o PDF é o valor **final da tela**, não o de `data.py`.

---

## 6. Forma de pagamento (parcelas)

Na tela (seção 3):

1. Quantidade de etapas (1 a 8)  
2. Nome de cada etapa (ex.: Entrada, Embarque, Faturado)  
3. Percentual de cada uma  
4. Escolha: calcular sobre à prazo ou à vista  

O resumo mostra em tempo real o R$ de cada parcela.  
O PDF, no modo completo / condições, monta a tabela de pagamento com esses dados.

**Padrão sugerido:** 30% + 30% + 40%. A soma deve ser 100% (há aviso se não for).

---

## 7. Vendedores

- Arquivo: `vendedores.json`  
- Também gerenciável na **sidebar** da tela (Adicionar / Remover)  

**Local:** alterações ficam no arquivo da pasta do projeto.  
**Streamlit Cloud:** a lista é compartilhada enquanto o app está no ar, mas gravações podem se perder no reinício. Para lista fixa e permanente no Cloud, edite `vendedores.json` no GitHub e faça deploy, ou use uma planilha/banco externo no futuro.

Lista inicial também está em `VENDEDORES_INICIAL` em `data.py` (fallback se o JSON não existir).

---

## 8. Dados da empresa e textos fixos

Em `data.py`:

```python
EMPRESA = {
    "nome": "Casa do Frentista",
    "marca_equipamentos": "GP Company",
    "endereco": "Estrada Porto Grande, 1771",
    "cep": "89245-000",
    "cidade": "Araquari - SC",
    "cnpj": "21.463.174/0002-41",
    "ncm": "7309.90.00",
    "norma": "NBR 15.461",
    "garantia_meses": 6,
    "prazo_fabricacao": "15 à 30 dias",
}

TEXTOS = {
    "acompanha": "Data book; ART; Desenho orientativo; ...",
    "tratamento_interno_tanque": "Limpeza Mecânica",
    "tratamento_externo": "Fundo Primer ...",
    # etc.
}
```

Alterar aqui reflete no cabeçalho, rodapé e especificações do PDF (quando o gerador usa esses campos).

---

## 9. PDF — modos e formatação de texto

### 9.1 Modos

| Modo na tela | Conteúdo |
|--------------|----------|
| Orçamento resumido | 1 página: cliente, imagens, itens, totais |
| Proposta completa | Valores + especificações técnicas + condições/garantia/cláusulas |
| Somente condições | Só condições comerciais, garantias e cláusulas |

### 9.2 Negrito, tamanho e cor no PDF

Arquivo: `pdf_generator.py`. Textos usam `Paragraph` com tags parecidas com HTML:

```python
# Negrito
story.append(Paragraph("<b>Do Comprador:</b>", styles["CorpoPequeno"]))

# Tamanho
story.append(Paragraph("<font size='11'><b>Título</b></font>", styles["Corpo"]))

# Cor
story.append(Paragraph("<font color='#1a365d'><b>Destaque</b></font>", styles["Corpo"]))

# Mistura
story.append(Paragraph(
    "Valor à vista: <b>R$ 33.321,25</b> com <i>5% de desconto</i>.",
    styles["Corpo"]
))
```

Estilos nomeados (`TituloPrincipal`, `Subtitulo`, `Corpo`, `CorpoPequeno`, `ItemLista`, etc.) são criados em `criar_estilos()`. Para um padrão novo (ex.: título de seção sempre igual), adicione um `ParagraphStyle` em `criar_estilos()` e use `styles["NomeDoEstilo"]`.

### 9.3 Imagens no PDF

A função `_grade_imagens` monta 1 a 5 fotos de forma proporcional (responsiva).  
A lista vem de `dados["imagens"]` montada no `app.py` (produtos + opcionais marcados).

---

## 10. Checklist: incluir um produto novo do zero

Exemplo: novo tanque **9.000L** com foto e opcional de escada.

1. **`data.py` → `TANQUES`**  
   - Incluir `"9.000L": { preco, diametro, comprimento, chapa, peso, label }`

2. **`data.py` → `IMAGEM_POR_TANQUE`**  
   - `"9.000L": "imagens_produtos/tanques/tanque_9000.jpg"`

3. **Arquivo de imagem**  
   - Salvar em `imagens_produtos/tanques/tanque_9000.jpg`

4. **(Opcional) Opcional escada** em `OPCIONAIS`  
   - Nome, preço, descrição, imagem em `imagens_produtos/opcionais/`

5. **Reiniciar** o Streamlit ou fazer push no GitHub (Cloud)

6. **Testar** na tela: selecionar 9.000L, ver preço/medidas/foto, gerar PDF

---

## 11. Manutenção e boas práticas

| Prática | Motivo |
|---------|--------|
| Preferir editar `data.py` em vez de hardcode em `app.py` | Um único lugar para preços e medidas |
| Nomes de produto iguais em todos os dicionários | A chave do selectbox é a chave da imagem e do preço |
| Arquivos de imagem sem espaços/acentos estranhos | Evita “imagem não encontrada” |
| Testar PDF nos 3 modos após mudanças grandes | Resumo, completa e só condições |
| Versionar no GitHub | Histórico e deploy no Cloud |
| Não colocar senhas/tokens no código | Segurança |

### Onde mexer para cada tipo de melhoria

| Melhoria | Arquivo principal |
|----------|-------------------|
| Novo preço / medida / produto | `data.py` |
| Nova categoria de opcional | `data.py` (`OPCIONAIS`) + pasta de imagem |
| Layout do PDF, textos legais | `pdf_generator.py` |
| Novos campos na tela, parcelas, UX | `app.py` |
| Fórmula de volume/peso | Novo `calculos.py` + chamadas em `app.py` |
| Lista fixa de vendedores | `vendedores.json` ou `VENDEDORES_INICIAL` |

---

## 12. Dependências

Arquivo `requirements.txt`:

```
streamlit>=1.28.0
reportlab>=4.0.0
pandas>=2.0.0
Pillow>=10.0.0
```

Instalação: `pip install -r requirements.txt`

---

## 13. Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Preço não muda ao trocar o tanque | Versão antiga do `app.py` (key fixa) | Usar versão com `key=f"p_tanque_{tanque_key}"` |
| Imagem não aparece | Caminho errado ou arquivo inexistente | Conferir pasta + nome em `data.py`; ver aviso na tela |
| Descrição cortada no PDF | Truncamento no código | Já removido; usar versão atual |
| Vendedor some no Cloud | Disco efêmero | Editar `vendedores.json` no GitHub |
| Soma das parcelas ≠ 100% | Percentuais incompletos | Ajustar % até a soma ser 100 |
| Erro ao gerar PDF | Imagem corrompida ou path inválido | O gerador ignora imagem com falha; conferir arquivo |

---

## 14. Evoluções sugeridas (futuro)

1. **Fórmulas de dimensionamento** (volume, peso estimado) em módulo `calculos.py`  
2. **Histórico de propostas** (salvar JSON/PDF por cotação)  
3. **Lista de vendedores permanente no Cloud** (Google Sheet ou banco)  
4. **Fotos por modelo de bomba/filtro** (hoje muitos usam a mesma imagem padrão)  
5. **Envio por e-mail** do PDF direto da tela  
6. **Assinatura digital** ou campo de aceite no PDF  

---

## 15. Contato da estrutura comercial (referência)

Dados padrão no sistema (editáveis em `EMPRESA`):

- **Casa do Frentista**  
- Equipamentos **GP Company**  
- Estrada Porto Grande, 1771 — CEP 89245-000 — Araquari/SC  
- CNPJ 21.463.174/0002-41  
- NCM 7309.90.00 · Norma NBR 15.461 · Garantia 6 meses  

---

*Manual gerado para uso interno. Mantenha este arquivo junto ao código para facilitar a manutenção por qualquer pessoa do time.*
