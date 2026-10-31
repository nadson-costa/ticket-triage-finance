# Taxonomia de tickets: banco/fintech de pessoa física

> **Versão 1.0** (2026-10-31). Fonte de verdade para geração de dados, rotulagem e avaliação.
> Qualquer mudança nas categorias ou regras exige **regerar os conjuntos congelados** e registrar no histórico (seção 14).

## 1. Objetivo e escopo

O modelo recebe o texto de um ticket e prevê:

1. **Categoria** (multiclasse, 8 classes) para roteamento à equipe correta.
2. **Urgência** (binário: `alta` ou `normal`) para priorização.

**Domínio:** atendimento de um banco digital ou fintech de pessoa física no Brasil, em português (pt-BR).

**Fora de escopo:**

- Decisões sobre o cliente (conceder crédito, bloquear conta, confirmar fraude). O modelo apenas **sugere roteamento**.
- Atendimento a empresas (PJ), outros idiomas e canais de voz.
- Regras regulatórias específicas (prazos legais, mecanismos oficiais de devolução). Elas **não** são codificadas aqui; se forem citadas em tickets, é apenas como o cliente as mencionaria.

**Natureza dos dados:** 100% sintéticos, mais um conjunto escrito à mão. Nenhum dado real de clientes.

## 2. Rótulos de categoria

| Código | Nome | % alvo |
|---|---|---|
| `pix` | Pix e transferências | 22 |
| `cartoes` | Cartões | 18 |
| `conta_acesso` | Conta e acesso ao app | 15 |
| `cobrancas_tarifas` | Cobranças e tarifas | 12 |
| `credito` | Crédito e financiamento | 12 |
| `fraude_seguranca` | Fraude e segurança | 8 |
| `investimentos` | Investimentos | 8 |
| `duvidas_gerais` | Dúvidas gerais | 5 |

A distribuição é **desbalanceada de propósito**, como em dados reais. A tolerância na geração é de ±2 pontos percentuais por classe.

## 3. Descrição das categorias

### 3.1 `pix`: Pix e transferências

Problemas com envio, recebimento ou limites de Pix, TED e transferências, **incluindo erros do próprio cliente** (chave digitada errada).

- **Subtópicos:** Pix não chegou, Pix enviado para chave errada, limite do Pix, Pix agendado, TED atrasada, comprovante divergente.
- **Não é:** Pix feito sob golpe (vai para `fraude_seguranca`).
- **Exemplo:** "Mandei um Pix agora há pouco para a chave errada, o valor era alto. Dá para cancelar? Preciso desse dinheiro hoje." → `pix`, urgência `alta`.

### 3.2 `cartoes`: Cartões

Funcionamento e administração de cartões de crédito e débito.

- **Subtópicos:** compra recusada, fatura e fechamento, limite, segunda via, cartão não chegou, cartão virtual, parcelamento de fatura, extravio simples.
- **Não é:** compra não reconhecida ou cartão roubado (`fraude_seguranca`) e cobrança indevida (`cobrancas_tarifas`).
- **Exemplo:** "Meu cartão foi recusado no mercado, mas tenho limite disponível. Já aconteceu duas vezes essa semana." → `cartoes`, `normal`.

### 3.3 `conta_acesso`: Conta e acesso ao app

Entrar, manter e gerenciar a conta.

- **Subtópicos:** senha esquecida, biometria que não funciona, troca de celular, conta bloqueada, atualização cadastral, abertura de conta, problema com código de verificação.
- **Não é:** suspeita de que terceiros acessaram a conta (`fraude_seguranca`).
- **Exemplo:** "Troquei de celular e o app pede um código que chega no número antigo. Não consigo entrar na conta." → `conta_acesso`, `normal`.

### 3.4 `cobrancas_tarifas`: Cobranças e tarifas

Cliente considera que **um valor cobrado está errado ou indevido**.

- **Subtópicos:** cobrança duplicada, tarifa não esperada, anuidade, assinatura recorrente, pedido de estorno, juros questionados, compra reconhecida mas produto não entregue.
- **Não é:** operação de crédito (contratar, renegociar, quitar), que vai para `credito`.
- **Exemplo:** "Apareceram duas cobranças iguais da mesma loja, no mesmo dia, na minha fatura." → `cobrancas_tarifas`, `normal`.

### 3.5 `credito`: Crédito e financiamento

**Operações** de crédito: contratar, simular, renegociar, quitar, antecipar ou pagar parcelas.

- **Subtópicos:** empréstimo pessoal, consignado, renegociação de dívida, simulação, boleto de parcela, antecipação de parcelas, limite de cheque especial.
- **Não é:** questionamento de valores cobrados (`cobrancas_tarifas`).
- **Exemplo:** "Meu boleto da parcela vence hoje e o código de barras não gera no app." → `credito`, `alta`.

### 3.6 `fraude_seguranca`: Fraude e segurança

Qualquer situação em que **um terceiro age sem autorização**, há golpe ou há suspeita de invasão.

- **Subtópicos:** golpe do falso atendente, boleto falso, compra não reconhecida, conta invadida, cartão clonado, roubo ou furto de cartão/celular, phishing, Pix feito sob golpe.
- **Exemplo:** "Chegou uma notificação de compra numa loja que eu nunca usei. Não fui eu." → `fraude_seguranca`, `alta`.

### 3.7 `investimentos`: Investimentos

Produtos de investimento do banco e seus problemas.

- **Subtópicos:** rendimento diferente do esperado, resgate que não caiu, aplicação que não aparece, informe de rendimentos, carência.
- **Não é:** pergunta pura de "como fazer" (`duvidas_gerais`).
- **Exemplo:** "Pedi o resgate do meu CDB há dois dias e o valor ainda não caiu na conta." → `investimentos`, `normal`.

### 3.8 `duvidas_gerais`: Dúvidas gerais

Perguntas **informativas**, sem falha e sem operação em andamento.

- **Subtópicos:** como fazer algo, horários e canais de atendimento, taxas, políticas, como emitir comprovante.
- **Exemplo:** "Como faço para tirar o comprovante de um Pix antigo?" → `duvidas_gerais`, `normal`.

## 4. Regras de rotulagem (em ordem de precedência)

Aplique as regras na ordem. A primeira que casar define o rótulo.

1. **Fraude tem precedência.** Se há terceiro agindo sem autorização, golpe ou suspeita de invasão, o rótulo é `fraude_seguranca`, seja qual for o produto envolvido.
2. **Roubo e furto vs. extravio:** roubo ou furto de cartão ou celular é `fraude_seguranca`. Extravio simples, sem suspeita de uso indevido, é `cartoes`.
3. **Falha vs. pedido:** algo que existia e parou de funcionar recebe a categoria do problema. Um pedido de algo novo (cartão adicional, empréstimo) recebe a categoria do produto.
4. **Valor questionado vs. operação:** cliente contesta um valor cobrado (inclusive juros) → `cobrancas_tarifas`. Cliente quer contratar, renegociar, quitar ou pagar → `credito`.
5. **Multi-assunto:** classifique pelo **primeiro problema que o suporte precisa resolver**.
6. **Dúvidas gerais** só quando **não há falha nem operação em andamento**. "Como faço X?" sobre qualquer produto é `duvidas_gerais`; "tentei X e deu erro" vai para a categoria do produto.
7. **Urgência nunca altera a categoria.** Ameaças de Procon, Banco Central ou Justiça afetam só a urgência.

## 5. Zonas de sobreposição (o que torna o dataset difícil)

Cada par abaixo deve aparecer em cerca de **10 a 15%** dos tickets das categorias envolvidas.

| Par | Ticket A (rótulo) | Ticket B (rótulo) |
|---|---|---|
| Fraude × Cartões | "Não reconheço essa compra no meu cartão." (`fraude_seguranca`) | "Meu cartão foi recusado sem motivo." (`cartoes`) |
| Fraude × Pix | "Um suposto atendente pediu um Pix para proteger minha conta. Fiz e era golpe." (`fraude_seguranca`) | "Digitei uma chave errada e mandei o Pix para outra pessoa." (`pix`) |
| Fraude × Conta | "Não entro no app e vi que o e-mail cadastrado mudou. Não fui eu." (`fraude_seguranca`) | "Esqueci minha senha." (`conta_acesso`) |
| Cobranças × Cartões | "Cobraram anuidade que eu não esperava." (`cobrancas_tarifas`) | "A fatura fechou em data diferente da que eu esperava." (`cartoes`) |
| Cobranças × Crédito | "Os juros do meu empréstimo estão acima do contratado." (`cobrancas_tarifas`) | "Quero renegociar as parcelas do meu empréstimo." (`credito`) |
| Investimentos × Dúvidas | "Resgatei meu CDB e o dinheiro não caiu." (`investimentos`) | "Como faço para resgatar meu CDB?" (`duvidas_gerais`) |
| Multi-assunto | "O Pix não chegou e depois meu cartão foi recusado." (`pix`, pela regra 5) | |

Complementos obrigatórios:

- **Tickets vagos (3 a 5%):** por exemplo "preciso de ajuda" ou "deu problema". Eles têm categoria verdadeira definida pelo gerador, mas o texto não a revela. Isso impõe um **teto de acurácia** e justifica o limiar de confiança.
- **Tickets multi-assunto (cerca de 5%):** rotulados pela regra 5.

## 6. Urgência

Um ticket é `alta` se atender a **pelo menos um** critério:

1. **Prazo curto com consequência:** vencimento hoje ou amanhã (boleto, parcela, pagamento essencial).
2. **Perda em andamento:** golpe ou uso indevido acontecendo agora ou nas últimas horas.
3. **Operação irreversível a tempo:** o cliente precisa que uma ação seja interrompida ou cancelada rapidamente (Pix para destino errado, por exemplo).
4. **Acesso totalmente impedido com necessidade imediata declarada** (por exemplo, não consegue pagar algo hoje).
5. **Ameaça formal:** menciona Procon, Banco Central ou ação judicial.

Caso contrário, é `normal`.

**Pontos importantes:**

- A palavra "urgente" no texto **não** define a urgência. O gerador deve produzir tickets com "urgente" e urgência `normal`, e tickets `alta` sem a palavra. Isso evita que o modelo aprenda um atalho lexical.
- A urgência segue **estes critérios**, não a intuição do gerador. O prompt de geração recebe o rótulo e o critério aplicável.

**Prior de urgência `alta` por categoria** (alvo, total ≈ 22%):

| Categoria | % alta |
|---|---|
| `fraude_seguranca` | 80 |
| `pix` | 25 |
| `cartoes` | 20 |
| `conta_acesso` | 20 |
| `credito` | 15 |
| `cobrancas_tarifas` | 10 |
| `investimentos` | 10 |
| `duvidas_gerais` | 2 |

## 7. Política de dados e privacidade

- **Nenhum dado pessoal real**, nem em testes.
- Identificadores sensíveis aparecem **somente como marcadores**: `<CPF>`, `<CHAVE_PIX>`, `<NUMERO_CARTAO>`, `<TELEFONE>`, `<EMAIL>`, `<NOME>`.
- Valores em reais e datas podem aparecer em texto natural (são fictícios).
- **Sem nomes de bancos, empresas ou pessoas reais.** Use "o banco" ou "o app".
- O validador do gerador **rejeita** tickets com sequências numéricas que lembrem CPF (11 dígitos) ou cartão (16 dígitos).
- Na etapa de features, números são mascarados (`<NUM>`), para o modelo não aprender atalhos numéricos.

## 8. Estilos de escrita

Cada ticket é gerado a partir de uma **ficha** sorteada (categoria, subtópico, urgência, persona, tom, tamanho, ruído, gerador).

### 8.1 Gerador A (treino e validação)

- **Personas:** cliente comum no app, usuário iniciante, colaborador técnico, executivo com pressa.
- **Tom:** formal, informal, educado, irritado.
- **Formato:** chat curto ou e-mail com assunto e corpo.
- **Ruído:** abreviações ("vc", "pq"), falta de acentos, erros de digitação leves.

### 8.2 Gerador B (teste independente)

- **Personas diferentes:** cliente idoso pouco digital, microempreendedor, cliente que descreve só o sintoma, cliente em tom de reclamação pública.
- **Formatos diferentes:** transcrição de áudio sem pontuação, e-mail encaminhado com assinatura e histórico, texto que descreve um print de erro.
- **Ruído diferente:** mistura de português e inglês técnico, gírias regionais, contexto irrelevante em textos longos.
- **Modelo e prompts diferentes** dos usados no gerador A.

## 9. Ruído e qualidade

- **Ruído de rótulo no treino:** 5 a 10% dos tickets de treino têm a categoria trocada por uma categoria **confundível** (usando os pares da seção 5, não aleatória). O campo `label_noisy` marca esses casos.
- **Validação e testes têm rótulos limpos.**
- **Quase-duplicatas:** removidas dentro de cada conjunto e **entre** conjuntos (similaridade de cosseno no TF-IDF acima de 0,9).
- **Revisão manual** de uma amostra de cerca de 100 tickets gerados, para estimar a taxa de rótulos discutíveis.

## 10. Conjuntos de dados

| Arquivo | Tamanho | Origem | Uso |
|---|---|---|---|
| `train.jsonl` | ~8.000 | Gerador A | Ajustar pesos |
| `val.jsonl` | ~1.000 | Gerador A (separado do treino) | Ajustar λ, limiar e parada |
| `test_gen_b.jsonl` | ~1.000 | Gerador B | Generalização entre geradores |
| `test_manual.jsonl` | 100 a 200 | Escrito à mão | Número final, mais próximo do real |

Regras:

- Os testes são **congelados**: gerados uma vez e não alterados. Mudar o gerador após ver erros no teste o transforma em validação.
- A análise de erros usa **somente a validação**.
- O teste manual é escrito **sem consultar** os tickets gerados.
- Todos os arquivos são versionados no Git (são pequenos) e a geração usa seed fixa.

## 11. Esquema dos registros (JSONL)

Um objeto JSON por linha:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | string | Identificador único |
| `text` | string | Texto do ticket |
| `category` | string | Código da categoria (seção 2) usado como rótulo |
| `urgency` | string | `alta` ou `normal` |
| `subtopic` | string | Subtópico sorteado |
| `generator` | string | `A`, `B` ou `manual` |
| `persona` | string | Persona sorteada |
| `tone` | string | Tom sorteado |
| `style_noise` | list | Tipos de ruído de escrita aplicados |
| `overlap_with` | string ou null | Categoria com a qual o ticket foi desenhado para se confundir |
| `is_vague` | bool | Ticket deliberadamente vago |
| `label_noisy` | bool | Categoria trocada para simular erro de rótulo (apenas treino) |

## 12. Métricas de avaliação (planejadas)

- **Categoria:** F1 por classe, F1 macro e ponderado, matriz de confusão. A acurácia é reportada, mas não é a métrica principal.
- **Urgência:** precision, recall e F1 da classe `alta`, curva precision-recall e limiar escolhido pelo custo de errar.
- **Limiar de confiança:** fração de tickets enviados a um humano vs. acurácia no restante.
- **Comparação entre conjuntos:** validação vs. `test_gen_b` vs. `test_manual`.

## 13. Limitações conhecidas

- Dados **sintéticos**: o desempenho no conjunto de treino mede o quanto o modelo aprende o gerador, não a realidade.
- O vocabulário e os cenários **não foram validados por profissionais do setor**.
- As proporções de categorias e de urgência são **estimativas de projeto**, não medições de dados reais.
- A urgência segue regras definidas aqui, **sem validação humana externa**.
- O modelo é um estudo e **não deve ser usado para decisões sobre clientes**.

## 14. Histórico de versões

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 2026-10-31 | Versão inicial |
