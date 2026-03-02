# PLANO COMPLETO: FAKE NEWS REPORTING AGENT
## Agente de Empoderamento e Verificação de Desinformação para Minorias Interseccionais

---

## 1. VISÃO GERAL DO PROJETO

### 1.1 Objetivo Principal
Criar um agente digital que empodere minorias interseccionais (com foco inicial em mulheres negras) a questionar e analisar informações, promovendo literacia digital e protegendo-as da desinformação, através de uma abordagem pedagógica de "mais perguntas que respostas".

### 1.2 O Que Este Projeto NÃO É
- NÃO é um verificador de fatos tradicional que simplesmente diz "verdadeiro" ou "falso".
- NÃO é um sistema reativo que apenas reporta desinformação já espalhada.
- NÃO é uma ferramenta genérica para o público em geral.

### 1.3 O Que Este Projeto É
- Um mentor digital interativo que guia o usuário por um processo de auto-reflexão e investigação.
- Um agente proativo que constrói resiliência do usuário contra futuras desinformações.
- Um educador que capacita o indivíduo com pensamento crítico e literacia digital.
- Uma ferramenta com foco explícito na proteção de minorias interseccionais.

### 1.4 Proposta de Valor Única
"Nosso Fake News Reporting Agent redefine o conceito ao não apenas identificar e reportar a desinformação, mas ao empoderar o indivíduo a se tornar um agente ativo de verificação e reflexão. Focamos em educar sobre o porquê e o como da desinformação, especialmente seu impacto em minorias interseccionais, construindo resiliência e pensamento crítico. Assim, o reporting se torna uma ação consciente e informada, e não apenas uma denúncia reativa."

### 1.5 Diferenciais Competitivos
- **Público-alvo específico e sub-representado**: Foco em minorias interseccionais (ex: mulheres negras), frequentemente alvos de desinformação.
- **Abordagem pedagógica inovadora**: Não entrega respostas prontas; guia por questionamento e auto-reflexão.
- **Lente multidisciplinar**: Combina direitos humanos, compliance, cybersecurity e IA/ML.
- **Foco no empoderamento e resiliência**: Proativo, construindo defesas internas no usuário.
- **Análise de vieses algorítmicos e deepfakes**: Aborda como algoritmos amplificam desinformação contra minorias.

---

## 2. PÚBLICO-ALVO E PERSONAS

### 2.1 Público Primário
Minorias interseccionais, com foco inicial em mulheres negras brasileiras ativas em redes sociais e grupos de WhatsApp.

### 2.2 Persona Principal: Maria
- **Perfil**: Mulher negra, ativa em grupos de WhatsApp da sua comunidade.
- **Comportamento**: Preocupada com desinformação que circula, mas nem sempre sabe como verificar.
- **Necessidade**: Ferramentas adaptadas à sua realidade para questionar informações antes de compartilhá-las.
- **Motivação**: Proteger sua comunidade de informações prejudiciais.

### 2.3 Características do Público-Alvo
- Acesso predominante via smartphone e WhatsApp.
- Possíveis limitações de dados móveis ou dispositivos mais básicos.
- Forte presença em redes comunitárias e grupos de mensagens.
- Frequentemente alvo de narrativas de desinformação específicas.

---

## 3. ARQUITETURA DO SISTEMA

### 3.1 Modelo Híbrido: Bot + Plataforma Web

O sistema opera em duas camadas complementares:

#### Camada 1: Bot de WhatsApp/Telegram (Porta de Entrada)
- **Função**: Interface inicial e mais acessível; primeiro nível de mentoria.
- **Objetivo**: Iniciar a jornada de reflexão do usuário com 3-4 interações rápidas.
- **Processamento inicial**: Apenas texto e links (imagens/vídeos em fases posteriores).
- **Fluxo**: 5-7 perguntas-chave focadas em motivação, emoção e percepção da verdade.
- **Integração**: Não é um sistema isolado; é o ponto de contato que direciona para a plataforma web.

#### Camada 2: Plataforma Web (Aprofundamento)
- **Função**: Investigação aprofundada com ferramentas interativas.
- **Componentes principais**:
  - **Balança da Evidência**: Visualização comparando fontes que confirmam vs. contradizem o conteúdo.
  - **Guia de Análise de Fontes**: Checklist interativo para avaliar credibilidade de fontes.
  - **Radar de Tendências de Desinformação**: Alertas proativos sobre narrativas falsas direcionadas a comunidades específicas.
  - **Guia de Ação para Conteúdo Criminoso**: Passos para denunciar discurso de ódio e conteúdo ilegal.
  - **Módulos de Aprendizagem**: Quizzes e exemplos sobre viés de confirmação, bolhas de filtro, falácias.

#### Camada 3 (Futuro): Aplicativo Móvel
- **Quando**: Após consolidação do bot + web (Batch 7 ou posterior).
- **Justificativa**: Notificações push, acesso offline, experiência nativa.
- **Condição**: Só investir quando o core estiver validado e com impacto comprovado.

### 3.2 Stack Tecnológico Necessário

#### Desenvolvimento de Chatbot e Integração de APIs
- Plataformas: Dialogflow, Rasa, ou APIs específicas (Twilio para WhatsApp, Telegram Bot API).
- Gerenciamento do fluxo de perguntas e respostas.
- Processamento de mensagens (texto, links).

#### Desenvolvimento Web (Frontend e Backend)
- **Frontend**: Interface visual interativa, responsiva, acessível.
- **Backend**: Banco de dados, lógica de negócio, comunicação com serviços de análise.

#### Inteligência Artificial e Machine Learning
- **PLN (Processamento de Linguagem Natural)**: Análise de textos, padrões, sentimentos.
- **Visão Computacional**: Detecção de deepfakes, análise de imagens e vídeos.
- **Detecção de Vieses Algorítmicos**: Como algoritmos amplificam certas narrativas.
- **Modelos de Classificação**: Identificação de padrões de desinformação.

#### Arquitetura de Dados
- Banco de dados (SQL ou NoSQL) para conteúdo, fontes, análises, feedbacks.
- Garantia de integridade e segurança dos dados.
- Conformidade com LGPD.

#### Segurança da Informação e Privacidade
- Criptografia, segurança de redes, proteção contra malware.
- Anonimização de dados de uso.
- Conformidade com leis de proteção de dados.

---

## 4. JORNADA DO USUÁRIO (FLUXO COMPLETO)

### 4.1 Passo 1: O Primeiro Contato — Bot de WhatsApp/Telegram

#### Entrada do Conteúdo
O usuário copia e cola texto, link, imagem ou vídeo no bot.

**Bot**: "Obrigada por compartilhar! Para te ajudar a pensar um pouco mais sobre este conteúdo, tenho uma pergunta para você:"

#### Primeira Pergunta (Foco na Motivação)
**Bot**: "Qual o seu principal motivo para querer compartilhar este conteúdo?"

**Opções de Resposta (Menu)**:
1. "Para informar as pessoas."
2. "Para alertar sobre algo importante."
3. "Para expressar minha opinião/indignação."
4. "Porque me identifico com a mensagem/crença."
5. "Porque vi em vários lugares e parece importante."
6. "Outro motivo." (caixa de texto aberta)

#### Fluxo Interativo de Reflexão (Baseado na Resposta)

**Se responder "Para informar as pessoas"**:
- Bot: "Que bom que você quer informar! Para que a informação seja a mais precisa e útil possível, você já pensou de onde ela veio e quem a produziu?"
- Opções: "Confio na fonte" / "Não sei bem a fonte" / "Não pensei nisso"
  - Se "Confio na fonte": "Entendi. O que te faz confiar tanto nessa fonte? Ela costuma ser precisa? Já viu alguma correção ou desmentido dela antes?"
  - Se "Não sei bem" ou "Não pensei nisso": "É um bom ponto para pensar. O quanto a verdade importa para você na hora de compartilhar uma informação?"

**Se responder "Para expressar minha opinião/indignação"**:
- Bot: "Sua opinião é importante! Que emoção essa notícia te provoca? Raiva? Medo? Indignação? Por que essa emoção é tão forte? Essa emoção está te impedindo de pensar criticamente sobre o conteúdo?"

#### Pergunta de Fechamento (Certeza — Feita Apenas Uma Vez, ao Final)
**Bot**: "Agora, com base em tudo o que você pensou, você ainda tem certeza que quer compartilhar este conteúdo?"

**Opções**:
1. "Sim, ainda tenho certeza."
2. "Não, mudei de ideia."
3. "Quero aprofundar minha análise na plataforma web."

#### Transição para a Plataforma Web
**Bot**: "Suas reflexões são muito valiosas! Para te ajudar a ir ainda mais fundo e a desenvolver seu 'superpoder' de questionar, preparei um guia interativo. Gostaria de continuar essa jornada de descoberta na nossa plataforma web?"

### 4.2 Passo 2: Investigação Aprofundada — Plataforma Web

#### Chegada à Plataforma
O conteúdo enviado ao bot já está em destaque na plataforma.

**Agente (web)**: "Bem-vinda ao seu espaço de investigação! Vamos explorar juntas este conteúdo, fazendo perguntas importantes para entender melhor o que está por trás dele."

#### Balança da Evidência
Visualização com:
- **Fontes que Confirmam**: 2-3 links de apoio.
- **Fontes que Contradizem**: 2-3 links de questionamento.

**Agente**: "Ao observar essa 'balança', o que você conclui sobre as evidências a favor ou contra o conteúdo?"

#### Guia de Análise de Fontes
Checklist interativo: autor, especialidade, existência de "Sobre Nós", idade do domínio.

**Agente**: "Vamos usar nosso checklist para avaliar esta fonte. Quem é o autor? Ele é especialista no assunto?"

#### Radar de Tendências de Desinformação (Proativo)
Painel com alertas em tempo real.

**Agente**: "Alerta: Narrativas falsas sobre [tema] estão sendo direcionadas a comunidades [minorias]. Fique atenta!"

#### Guia de Ação para Conteúdo Criminoso
Quando o conteúdo incita ódio ou é ilegal.

**Agente**: "Entenda o que é discurso de ódio e como ele é crime. Aqui estão os passos para denunciar este conteúdo nas plataformas e às autoridades, e como documentar as provas."

- Links diretos para formulários de denúncia.
- Passo a passo baseado em direitos e compliance.

#### Módulos de Aprendizagem
Quizzes e exemplos interativos sobre:
- Viés de confirmação
- Bolhas de filtro
- Táticas comuns de desinformação
- Falácias lógicas

### 4.3 Passo 3: Decisão Empoderada — Feedback Final

**Agente**: "Você explorou o conteúdo, analisou as fontes e refletiu sobre o impacto. Com base em tudo o que você investigou, qual é a sua conclusão sobre este conteúdo?"

**Opções**:
- "Não, mudei de ideia. Decidi não compartilhar."
- "Sim, vou compartilhar com ressalvas."
- "Preciso investigar mais."

**Agente (reforço)**: "Sua capacidade de questionar e investigar é poderosa! Você acaba de proteger sua comunidade de uma informação prejudicial. Continue usando essas ferramentas para navegar no mundo da informação."

---

## 5. LÓGICA DE QUESTIONAMENTO

### 5.1 Categorias de Perguntas
As perguntas do agente são organizadas em 7 categorias:

1. **Motivação**: Por que o usuário quer compartilhar o conteúdo.
2. **Percepção da Verdade**: O que o usuário acredita ser verdade e por quê.
3. **Fonte**: De onde veio a informação e quem a produziu.
4. **Conteúdo**: Análise do texto/mídia em si.
5. **Impacto**: Como o conteúdo afeta a comunidade do usuário e minorias.
6. **Contexto Digital**: Vieses algorítmicos, bolhas de filtro, manipulação.
7. **Ação Pessoal**: O que o usuário fará com a informação.

### 5.2 Princípios da Linguagem
- Sempre acolhedora e não acusatória.
- Neutra em gênero.
- Acessível, sem jargões técnicos.
- Guia sem julgar.
- Ressonante com as experiências de vida do público-alvo.

### 5.3 Regras de Fluxo
- Máximo 3-4 interações no bot antes de sugerir a plataforma web.
- A pergunta sobre "certeza de compartilhar" aparece apenas UMA vez, ao final do fluxo do bot.
- O motivo do compartilhamento é sempre a primeira pergunta.
- As perguntas se adaptam com base na resposta anterior do usuário.

---

## 6. CONTEÚDO E CURADORIA

### 6.1 Fontes de Checagem de Fatos
Identificar 3-5 fontes nacionais e internacionais de checagem confiáveis que o agente poderá citar ou utilizar como referência.

### 6.2 Exemplos de Notícias para Teste
Selecionar 3-5 exemplos representativos:
1. Uma notícia claramente falsa (boato comum com impacto emocional).
2. Uma notícia ambígua ou com viés (título sensacionalista para fato real).
3. Uma notícia verdadeira mas que pode gerar forte emoção ou reforçar preconceito.

**Requisito**: Pelo menos um exemplo deve ser diretamente relevante para minorias interseccionais.

### 6.3 Contextualização
Em vez de apenas dizer "isso é falso", o agente explica:
- POR QUE é falso.
- QUEM se beneficia da disseminação.
- QUAIS as consequências para minorias interseccionais.

---

## 7. ANÁLISE AVANÇADA

### 7.1 Vieses Algorítmicos
- Como os algoritmos de plataformas amplificam certos conteúdos e silenciam outros.
- Como vieses algorítmicos afetam a visibilidade de vozes de minorias.
- Como estereótipos negativos são amplificados algoritmicamente.
- Análise não apenas do "o que é falso" mas do "como o falso é promovido e quem é afetado".

### 7.2 Deepfakes
- Detecção de manipulação em imagens e vídeos.
- Foco em como deepfakes são usados para atacar mulheres e minorias.
- Proteção contra campanhas de desinformação visuais e auditivas.

### 7.3 Lente Interseccional
- Narrativas específicas construídas para atacar ou marginalizar grupos.
- Vulnerabilidades digitais de grupos específicos.
- Impacto real: consequências na saúde, segurança, reputação e participação cívica.

---

## 8. PLANO DE EXECUÇÃO EM BATCHES

### Batch 0: Fundação Estratégica

**Objetivo**: Solidificar a visão, missão e estratégia antes de qualquer desenvolvimento.

**Atividades**:
- Criar Documento de Visão e Missão.
- Elaborar Planilha Mestra de Perguntas e Fluxos (todas as perguntas categorizadas com opções de resposta e transições).
- Definir Perfil do Usuário Ideal (Persona detalhada).
- Redigir Declaração de Proposta de Valor Única.

**Entregáveis**: Documento de Visão e Missão; Planilha de Perguntas; Persona; Proposta de Valor.

**Métrica de Sucesso**: Capacidade de articular o projeto em um pitch de 1 minuto.

---

### Batch 1: MVP do Bot — Prototipagem e Validação Inicial

**Objetivo**: Testar a eficácia da abordagem de "mais perguntas que respostas" e a receptividade do público-alvo.

**Atividades**:

#### 1.1 Definição do Escopo do Bot MVP
- Processar apenas texto e links.
- Selecionar 5-7 perguntas-chave (motivação, emoção, percepção da verdade).
- Escrever mensagem de transição para a plataforma web.
- Escrever script completo da primeira interação.

#### 1.2 Criação do Script Detalhado
- Cada frase, opção de menu e transição documentada.
- Linguagem acolhedora, neutra e não acusatória.
- Fluxograma visual (Lucidchart/Miro).
- Máximo 3-4 interações antes da sugestão da web.

#### 1.3 Estratégia de Conteúdo para Teste
- Identificar 3-5 fontes confiáveis de checagem.
- Selecionar 3-5 notícias-exemplo (falsa, ambígua, verdadeira com viés).
- Garantir relevância para minorias interseccionais em pelo menos 1 exemplo.

#### 1.4 Protótipo de Baixa Fidelidade ("Bot Humano")
- Simular a experiência manualmente via WhatsApp/Telegram.
- Uma pessoa segue o script e interage como se fosse o bot.
- Alternativa: ferramentas de prototipagem (ManyChat, Chatfuel).

#### 1.5 Recrutamento de Testadores Iniciais
- Identificar 5-10 pessoas do público-alvo.
- Contatar 1-2 líderes comunitários para indicações.
- Preparar Termo de Consentimento (objetivo do teste, anonimato, privacidade).

#### 1.6 Testes de Usabilidade e Entrevistas Qualitativas
- Sessões individuais de teste.
- Roteiro de perguntas abertas: "Como se sentiu?", "As perguntas fizeram pensar diferente?", "A linguagem foi acolhedora?", "O que mudaria?"
- Gravar ou anotar detalhadamente (com consentimento).

#### 1.7 Análise de Feedback e Iteração
- Compilar feedback positivo, negativo e sugestões.
- Identificar padrões e pontos de melhoria.
- Priorizar 2-3 mudanças mais impactantes.

**Entregáveis**: Script Final do Bot MVP; Roteiro de Teste; Relatório de Feedback; Fluxograma Atualizado.

**Métricas**: Feedback positivo sobre linguagem e reflexão; alta taxa de conclusão do fluxo.

---

### Batch 2: MVP da Plataforma Web — Prototipagem e Validação

**Objetivo**: Validar a experiência de aprofundamento na web.

**Atividades**:

#### 2.1 Definição do Escopo Web
- Exibição do conteúdo enviado pelo bot.
- Implementação da "Balança da Evidência" com fontes de exemplo.

#### 2.2 Criação de Wireframes e Mockups
- Protótipo interativo (Figma, Adobe XD).
- Navegação simulada para testes.

#### 2.3 Curadoria de Conteúdo
- Critérios de seleção de fontes confiáveis.
- Fontes nacionais e internacionais relevantes para temas de minorias.

#### 2.4 Protótipo Clicável
- Protótipo interativo que simula navegação e interação completa.

#### 2.5 Testes de Usabilidade
- 5-10 novos testadores do público-alvo.
- Foco: clareza da interface, utilidade da Balança, fluidez da transição bot-web.

#### 2.6 Análise e Iteração
- Ajustar design, fluxo e conteúdo com base no feedback.

**Entregáveis**: Wireframes e Mockups; Guia de Curadoria de Conteúdo v1.0; Relatório de Feedback.

**Métricas**: Clareza da interface; utilidade da Balança; facilidade de navegação.

---

### Batch 3: Desenvolvimento e Validação Ampliada do MVP Integrado

**Objetivo**: Construir a primeira versão funcional (bot + web) e validar com grupo maior.

**Atividades**:

#### 3.1 Desenvolvimento Técnico do Bot MVP
- Seleção de tecnologia (Dialogflow, Rasa, Twilio, Telegram Bot API).
- Implementação do script (versão 2.0 validada).
- Integração com plataforma de mensageria.
- Testes unitários e de integração.

#### 3.2 Desenvolvimento Técnico da Plataforma Web MVP
- Frontend e backend baseados nos mockups aprovados.

#### 3.3 Integração Bot-Web
- Transição fluida entre bot e plataforma web.
- Passagem correta de informações (conteúdo analisado).

#### 3.4 Estratégia de Validação Ampliada
- Surveys pré e pós-uso para medir mudança de hábito.
- Configurar analytics para KPIs:
  - Taxa de conclusão do fluxo (bot)
  - Taxa de transição bot → web
  - Tempo médio na plataforma web
  - Cliques em fontes na Balança da Evidência
  - Distribuição das respostas finais
  - Taxa de retorno de usuários
- Roteiros para 2-3 grupos focais.

#### 3.5 Recrutamento Ampliado
- 20-50 pessoas do público-alvo.
- Guia de boas-vindas para testadores.

#### 3.6 Teste Beta e Coleta de Dados
- Período de 2-4 semanas.
- Monitoramento ativo do sistema.
- Coleta quantitativa (analytics, surveys) e qualitativa (grupos focais).

#### 3.7 Análise e Relatório de Impacto Inicial
- Análise quantitativa e qualitativa.
- Relatório de impacto: % empoderados, % que mudaram de ideia.
- Plano de melhorias priorizadas.

**Entregáveis**: Bot Funcional MVP; Plataforma Web Funcional; Relatório de Validação; Plano de Melhorias.

**Métricas**: Alta taxa de conclusão; feedback positivo sobre impacto na reflexão; dados promissores de mudança de comportamento.

---

### Batch 4: Funcionalidades Avançadas — Parte 1

**Objetivo**: Implementar Guia de Análise de Fontes e Radar de Tendências.

**Atividades**:
- Desenvolver o Guia de Análise de Fontes interativo.
- Implementar o Radar de Tendências de Desinformação.
- Testar e validar com usuários.

---

### Batch 5: Funcionalidades Avançadas — Parte 2

**Objetivo**: Implementar Guia de Ação para Conteúdo Criminoso e Módulos de Aprendizagem.

**Atividades**:
- Desenvolver o Guia de Ação (denúncia, documentação de provas).
- Criar Módulos de Aprendizagem interativos (viés de confirmação, bolhas, falácias).
- Testar e validar com usuários.

---

### Batch 6: Lançamento e Crescimento (Go-to-Market)

**Objetivo**: Lançar publicamente e iniciar aquisição de usuários.

**Atividades**:

#### 6.1 Preparação para Lançamento
- Revisão final de todas as funcionalidades.
- Testes de performance e segurança (carga, vulnerabilidades).
- Otimização SEO e acessibilidade.
- Documentação interna.

#### 6.2 Estratégia de Marketing e Comunicação
- Site institucional, perfis em redes sociais, press kit.
- Narrativa de impacto clara e inspiradora.
- Campanhas nos canais onde o público-alvo está presente.

#### 6.3 Estratégia de Parcerias
- Formalizar parcerias com ONGs, coletivos e líderes comunitários.
- Parcerias com veículos de mídia e instituições de ensino.

#### 6.4 Lançamento Público
- Evento de lançamento (online ou presencial).
- Ativação de parcerias para amplificação.

#### 6.5 Monitoramento Pós-Lançamento
- Acompanhamento de KPIs em tempo real.
- Coleta de feedback contínuo.
- Resolução rápida de bugs e problemas.

**Entregáveis**: Projeto Lançado; Plano de Marketing; Acordos de Parceria; Relatório de Desempenho.

**Métricas**: Usuários ativos; crescimento da base; menções na mídia; parcerias ativas.

---

### Batch 7: Sustentabilidade e Otimização Contínua

**Objetivo**: Garantir longevidade, otimizar impacto, explorar crescimento.

**Atividades**:

#### 7.1 Estratégia de Financiamento
- Editais e fundos de inovação social.
- Parcerias corporativas com responsabilidade social.
- Modelos de receita sustentáveis:
  - Licenciamento da metodologia para escolas/universidades/empresas.
  - Consultoria sobre literacia digital.
  - Versão premium para instituições (mídia, ONGs).
- Crowdfunding e doações.

#### 7.2 Otimização Contínua do Produto
- Ciclos de desenvolvimento ágil (Scrum/Kanban).
- Análise regular de dados e feedback.

#### 7.3 Medição e Relato de Impacto
- Relatórios de impacto periódicos.
- Histórias de sucesso e depoimentos.
- Documentação da metodologia para publicação acadêmica.

#### 7.4 Expansão de Funcionalidades
- Detecção de deepfakes mais sofisticada.
- IA para Radar de Tendências.
- Extensão de navegador.
- App móvel (se validado).

#### 7.5 Construção de Comunidade
- Fóruns, eventos, grupos de discussão.
- Conteúdo educativo contínuo.

**Entregáveis**: Plano de Sustentabilidade; Relatórios de Impacto; Roadmap de Longo Prazo.

**Métricas**: Estabilidade financeira; crescimento de impacto; satisfação do usuário; inovação contínua.

---

## 9. EQUIPE E GOVERNANÇA

### 9.1 Perfil da Líder/Co-Fundadora
- **Expertise**: Direitos humanos, compliance, cybersecurity, compreensão de IA/ML.
- **Papel**: Visão estratégica, articulação do problema, liderança de equipe, decisões éticas.
- **NÃO precisa**: Programar ou executar todas as áreas técnicas.

### 9.2 Perfis Técnicos Necessários
- Especialistas em comunicação.
- Designers de UX/UI.
- Cientistas de dados.
- Desenvolvedores (chatbot, web, backend).
- Advogados em direitos digitais.
- Educadores.

### 9.3 Conselho Consultivo
Grupo de especialistas em: direitos humanos, mídia, tecnologia, comunidades minoritárias.

### 9.4 Estrutura Legal
Definir formato jurídico (ONG, startup social, etc.) para facilitar financiamento e parcerias.

---

## 10. MÉTRICAS E KPIs

### 10.1 Métricas de Produto
- Taxa de conclusão do fluxo do bot.
- Taxa de transição bot → web.
- Tempo médio na plataforma web.
- Cliques em fontes na Balança da Evidência.
- Distribuição das respostas finais (% que decidiu não compartilhar).
- Taxa de retorno de usuários.

### 10.2 Métricas de Impacto Social
- Aumento da literacia digital (medido por surveys pré/pós).
- Redução do compartilhamento de desinformação.
- Aumento da confiança em fontes verificadas.
- Denúncias de phishing evitadas.
- Sentimento do usuário (empoderado, confiante, protegido).

### 10.3 Métricas de Crescimento
- Número de usuários ativos.
- Crescimento da base de usuários.
- Menções na mídia.
- Parcerias ativas.

---

## 11. MODELO DE SUSTENTABILIDADE

### 11.1 Fontes de Financiamento
- Editais e fundos de inovação social.
- Parcerias corporativas (responsabilidade social).
- Doações e crowdfunding.

### 11.2 Modelos de Receita
- Licenciamento da metodologia de questionamento para escolas, universidades e empresas.
- Consultoria sobre literacia digital e combate à desinformação.
- Versão premium para instituições (veículos de mídia, ONGs).
- Versão para o cidadão comum permanece gratuita.

---

## 12. RISCOS E MITIGAÇÕES

### 12.1 Riscos Técnicos
- **Escalabilidade**: Testes de carga antes do lançamento.
- **Segurança**: Varreduras de vulnerabilidade, conformidade LGPD, criptografia.
- **Integração bot-web**: Testes rigorosos de integração.

### 12.2 Riscos de Adoção
- **Barreira de acesso**: Priorizar WhatsApp (maior ubiquidade).
- **Engajamento**: Linguagem acolhedora e experiência não sobrecarregada.
- **Confiança**: Parcerias com líderes comunitários e ONGs estabelecidas.

### 12.3 Riscos Éticos
- **Vieses no sistema**: Revisão constante por conselho consultivo.
- **Privacidade**: Anonimização de dados, termos claros.
- **Impacto não intencional**: Testes contínuos com público-alvo real.

---

## 13. PLATAFORMAS E CANAIS

### 13.1 Canais de Distribuição Prioritários
- WhatsApp (acesso primário — maior ubiquidade no público-alvo).
- Telegram (alternativa).
- Plataforma Web dedicada.

### 13.2 Canais de Alcance
- Parcerias com ONGs de minorias interseccionais.
- Associações comunitárias.
- Influenciadores digitais engajados em causas sociais.
- Escolas e universidades.

### 13.3 Futuras Integrações
- Extensão de navegador.
- Widgets incorporáveis em sites de notícias e blogs.
- App móvel nativo.
- Potencial integração com Facebook, Instagram, TikTok via APIs.

---

## 14. GLOSSÁRIO DE TERMOS DO PROJETO

- **Agente**: O sistema completo (bot + web) que atua como mentor digital do usuário.
- **Balança da Evidência**: Ferramenta visual que compara fontes a favor e contra um conteúdo.
- **Bot Humano**: Protótipo de baixa fidelidade onde uma pessoa simula o bot manualmente.
- **Radar de Tendências**: Sistema proativo que alerta sobre narrativas de desinformação direcionadas a comunidades.
- **Guia de Ação**: Módulo que orienta sobre como denunciar conteúdo criminoso/ilegal.
- **Literacia Digital**: Capacidade de compreender, avaliar e usar informação digital de forma crítica.
- **Minorias Interseccionais**: Pessoas que pertencem a múltiplos grupos marginalizados simultaneamente.
- **MVP**: Produto Mínimo Viável — versão mais simples possível para teste e validação.

---

## 15. INSTRUÇÕES PARA USO DESTE PLANO POR LLMs

Este documento foi projetado para ser consumido por modelos de linguagem (LLMs) como referência completa do projeto. Ao utilizar este plano:

1. **Priorize a seção relevante**: Use o índice para navegar diretamente à seção necessária.
2. **Respeite os princípios de linguagem**: Toda comunicação gerada deve ser acolhedora, neutra em gênero e não acusatória.
3. **Mantenha o foco no público-alvo**: Minorias interseccionais, com ênfase em mulheres negras brasileiras.
4. **Siga a abordagem pedagógica**: Mais perguntas que respostas. Nunca entregue vereditos prontos.
5. **Considere o contexto de batch**: Identifique em qual fase do desenvolvimento o projeto se encontra.
6. **Respeite a expertise da fundadora**: Direitos humanos, compliance, cybersecurity e IA/ML.
7. **Use as métricas definidas**: Para avaliação de progresso e impacto.

---

*Documento gerado com base no plano completo do projeto "Fake News Reporting Agent" — Fevereiro 2026*
