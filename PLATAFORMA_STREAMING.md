# Plataforma de Streaming para Especialistas

## 1. Visão Geral do Projeto

### Conceito
Plataforma de streaming por assinatura (modelo “membership”) onde especialistas publicam conteúdo frequente (preferencialmente diário), combinando **aulas gravadas** com **encontros ao vivo** recorrentes. A mensalidade é acessível, com incentivo forte ao plano anual. A plataforma serve como produto âncora da esteira de vendas, com possibilidade de upsell de outros produtos.

### Proposta de Valor (one-liner)
**“Aprenda um método aplicável, com orientação contínua, para sair do zero e gerar resultado real no seu contexto — com conteúdo curto e direto + encontros ao vivo para destravar dúvidas.”**

### Princípios do Produto (inspirado em benchmark, sem copiar)
- **Transformação explícita**: promessa clara do “antes → depois” (o que o aluno passa a conseguir fazer).
- **Acessível a iniciantes**: trilha “do zero”, linguagem simples e quick wins na primeira semana.
- **Ao vivo + gravado**: rotina de lives (mentoria/Q&A) e biblioteca de replays organizada.
- **Oferta simples**: poucos planos, benefícios fáceis de entender, CTA e onboarding sem fricção.
- **Ritual e consistência**: calendário previsível (semanal/mensal) para criar hábito e reduzir churn.

### Jornada do Assinante (0–90 dias)
1. **Dia 0–1 (ativação)**: onboarding + diagnóstico rápido + “primeira vitória” em 30–60min.
2. **Semana 1 (fundação)**: trilha iniciante + checklist/roteiro + desafio simples com feedback.
3. **Semanas 2–4 (rotina)**: conteúdo curto recorrente + live semanal/quinzenal + plano de prática.
4. **Dias 30–90 (progresso)**: trilhas por nível + projetos/casos + certificação/selos de conclusão.

### Objetivos de Negócio
- **Receita Recorrente Previsível**: Contratos anuais garantem fluxo de caixa estável
- **Baixa Barreira de Entrada**: Mensalidade acessível para maximizar conversão
- **Engajamento Diário**: Conteúdo frequente aumenta retenção e valor percebido
- **Funil de Vendas**: Base de clientes engajados para produtos premium
- **Eficiência de Conversão**: Oferta clara, onboarding guiado e prova de valor rápida (primeiros 7 dias)

---

## 2. Modelo de Negócio

### 2.1 Estrutura de Receitas

#### Receita Primária - Assinatura
```
Mensalidade: R$ 69/mês
Plano Anual: R$ 597/ano (28% desconto vs mensal)
Plano Anual Lançamento: R$ 497/ano (40% desconto vs mensal)
Break-even: ~100-200 assinantes para cobrir custos operacionais
```

#### Receitas Secundárias
- **Cursos de Parceiros**: Comissão 50% em cursos de especialistas parceiros
- **Marketplace Interno**: Comissão 10-30% em produtos/cursos vendidos
- **Produtos Físicos**: Equipamentos, materiais didáticos
- **Mentorias/Consultorias**: Agendamento via plataforma
- **Eventos Presenciais**: Inscrições e acesso VIP
- **Licenciamento de Conteúdo**: Para outras plataformas/empresas

### 2.2 Estrutura de Custos

#### Custos Fixos Mensais
```
Infraestrutura:
├── Hospedagem de Vídeos (Bunny CDN/AWS): R$ 200-500
├── Servidor Backend (AWS/Digital Ocean): R$ 100-300
├── Banco de Dados: R$ 50-150
├── Email Marketing (Resend/SendGrid): R$ 50-100
├── Gateway de Pagamento (base): R$ 0-100
└── Total Infraestrutura: R$ 400-1.150/mês

Operacional:
├── Suporte ao Cliente (part-time): R$ 1.500-3.000
├── Editor de Vídeo (freelancer): R$ 2.000-4.000
├── Marketing Ads: R$ 2.000-5.000 (inicial)
└── Total Operacional: R$ 5.500-12.000/mês
```

#### Custos Variáveis
```
├── Gateway de Pagamento: 3-5% por transação
├── Armazenamento de Vídeo: ~R$ 0,01/GB/mês
├── Bandwidth: ~R$ 0,05/GB transferido
└── Estimativa: 10-15% da receita bruta
```

---

## 3. Análise de Viabilidade Financeira

### 3.1 Cenários de Rentabilidade

#### Cenário Conservador
```
Assinantes: 300
Mensalidade Média: R$ 67
Receita Mensal Bruta: R$ 20.100
(-) Gateway (4%): R$ 804
(-) Custos Fixos: R$ 7.000
(-) Custos Variáveis: R$ 1.500
= Lucro Líquido: R$ 10.796 (54% margem)

+ Upsells (10% conv × R$ 297): R$ 8.910
= Total Mensal: R$ 19.706
```

#### Cenário Realista
```
Assinantes: 500
Mensalidade Média: R$ 67
Receita Mensal Bruta: R$ 33.500
(-) Gateway (4%): R$ 1.340
(-) Custos Fixos: R$ 8.500
(-) Custos Variáveis: R$ 2.500
= Lucro Líquido: R$ 21.160 (63% margem)

+ Upsells (15% conv × R$ 397): R$ 29.775
= Total Mensal: R$ 50.935
```

#### Cenário Otimista
```
Assinantes: 1.000
Mensalidade Média: R$ 77
Receita Mensal Bruta: R$ 77.000
(-) Gateway (4%): R$ 3.080
(-) Custos Fixos: R$ 12.000
(-) Custos Variáveis: R$ 5.000
= Lucro Líquido: R$ 56.920 (74% margem)

+ Upsells (20% conv × R$ 497): R$ 99.400
= Total Mensal: R$ 156.320
```

### 3.2 Projeção de Crescimento (12 meses)

| Mês | Assinantes | Receita Assinaturas | Upsells | Total | Lucro |
|-----|-----------|---------------------|---------|-------|-------|
| 1   | 50        | R$ 3.350           | R$ 0    | R$ 3.350  | -R$ 4.000 |
| 2   | 100       | R$ 6.700           | R$ 1.500| R$ 8.200  | -R$ 500 |
| 3   | 180       | R$ 12.060          | R$ 4.500| R$ 16.560 | R$ 4.500 |
| 6   | 400       | R$ 26.800          | R$ 18.000| R$ 44.800| R$ 28.000|
| 12  | 800       | R$ 53.600          | R$ 60.000| R$ 113.600| R$ 85.000|

**Break-even**: Mês 2-3 com 100-150 assinantes

---

## 4. Estratégia de Precificação

### 4.1 Planos e Preços

#### Preço de Lançamento (Fundadores)
```
Plano Anual - LANÇAMENTO
├── R$ 497/ano (equivale a R$ 41/mês)
├── Pagamento à vista ou 12x sem juros
├── 7 dias de garantia incondicional
├── Acesso completo a todo conteúdo
└── Preço exclusivo para os primeiros assinantes
```

#### Preço Regular (Pós-Lançamento)
```
Plano Anual
├── R$ 597/ano (equivale a R$ 50/mês)
├── Pagamento à vista ou 12x sem juros
├── 7 dias de garantia incondicional
└── Acesso completo a todo conteúdo

Plano Mensal
├── R$ 69/mês
├── Cobrança recorrente mensal
├── 7 dias de garantia incondicional
├── Acesso completo a todo conteúdo
└── Flexibilidade para cancelar quando quiser
```

**Economia no Plano Anual**:
- Mensal: R$ 69 × 12 = R$ 828/ano
- Anual: R$ 597/ano
- **Economia de R$ 231/ano (28% de desconto)**

**Vantagens do Plano Anual**:
- Simplicidade de gestão
- Maior compromisso do cliente
- Fluxo de caixa concentrado
- Menor churn
- Desconto significativo para o assinante

### 4.2 Estratégias de Conversão

#### Funil de Aquisição
```
1. Isca Digital Grátis (Lead Magnet)
   ↓
2. Série de Emails (5-7 dias)
   ↓
3. Webinar/Masterclass Gratuita
   ↓
4. Oferta Limitada - Desconto Fundadores
   ↓
5. Assinatura Plataforma
```

#### Oferta de Lançamento (Fundadores)
```
De: R$ 597/ano (preço regular)
Por: R$ 497/ano (R$ 41/mês) - LANÇAMENTO
+ Bônus: Preço de fundador garantido para sempre
+ Bônus: Curso X (valor R$ 297)
+ Bônus: Comunidade VIP
```

---

## 5. Arquitetura Técnica

### 5.1 Stack Recomendada

#### Backend
```typescript
Framework: Next.js 14+ (App Router)
├── API Routes para backend
├── Server Actions para mutations
├── React Server Components
└── TypeScript para type safety

Database: PostgreSQL (Supabase)
├── Auth nativo
├── Row Level Security
├── Real-time subscriptions
└── Storage para thumbnails

Video Hosting: Bunny Stream
├── R$ 0,005/GB armazenado
├── R$ 0,01/GB transmitido
├── Player integrado
├── DRM opcional
└── Analytics incluído
```

#### Alternativas por Custo
```
Baixo Custo (< 500 assinantes):
├── Backend: Vercel Free Tier
├── DB: Supabase Free Tier (500MB)
├── Video: Bunny Stream
└── Custo Total: ~R$ 300/mês

Médio Porte (500-2000):
├── Backend: Vercel Pro (R$ 100/mês)
├── DB: Supabase Pro (R$ 125/mês)
├── Video: Bunny Stream
└── Custo Total: ~R$ 700/mês

Escalável (2000+):
├── Backend: AWS/Railway
├── DB: RDS PostgreSQL
├── Video: AWS CloudFront + S3
└── Custo Total: ~R$ 2.000/mês
```

### 5.2 Funcionalidades Core (MVP)

#### Essenciais - Semana 1-2
- [ ] Sistema de autenticação (email/senha)
- [ ] Assinatura via Stripe/Hotmart
- [ ] Player de vídeo responsivo
- [ ] Lista de conteúdos (feed)
- [ ] Perfil do usuário
- [ ] Painel admin básico (upload vídeos)
- [ ] Biblioteca de replays (lives gravadas)

#### Importantes - Semana 3-4
- [ ] Busca e filtros
- [ ] Categorias/tags
- [ ] Progresso de visualização
- [ ] Notificações (email) de novo conteúdo
- [ ] FAQ/Suporte
- [ ] Analytics básico
- [ ] Capítulos/timestamps + velocidade de reprodução
- [ ] Materiais anexos por aula (PDF, templates)
- [ ] Trilha “iniciante” com checklist e sequenciamento

#### Nice-to-Have - Fase 2
- [ ] Comunidade/comentários
- [ ] Playlists/trilhas de aprendizado
- [ ] Certificados de conclusão
- [ ] App mobile (React Native)
- [ ] Download offline
- [ ] Lives integradas
- [ ] Transcrição/legendas (acessibilidade + SEO interno)
- [ ] Gamificação leve (streak, selos, desafios)
- [ ] Notificações push (mobile) e lembretes de live

---

## 6. Estratégia de Conteúdo

### 6.1 Calendário Editorial

#### Ritmo Sustentável
```
Segunda-Terça: Aula técnica (10-25min)
Quarta: Bastidores/processo (8-15min)
Quinta: Q&A/dúvidas comuns (20-40min) (ao vivo quando possível)
Sexta: Caso de sucesso/aplicação prática (15min)
Sábado: Conteúdo bônus/aprofundamento (opcional)
```

#### Treinos ao vivo + replays (ritual de comunidade)
```
1 live/semana (ou quinzenal) com pauta clara:
├── Q&A + correções ao vivo
├── análise de casos enviados
└── mini-aula “destravadora” (15-20min)

Replays:
├── publicados em até 24h
├── resumidos (tópicos + timestamps)
└── categorizados por tema e nível
```

#### Produção em Lote
```
1 dia de gravação/mês = 8-12 vídeos
├── Manhã: Setup + 4 vídeos
├── Tarde: 4-6 vídeos
└── Pós-produção: 2-3 dias (terceirizado)

Custo de Produção:
├── Editor freelancer: R$ 50-100/vídeo
├── Thumbnail designer: R$ 20/thumbnail
├── Total: R$ 70-120/vídeo → R$ 840-1.440/mês
```

### 6.2 Tipos de Conteúdo de Maior Valor

1. **Aulas Práticas** (80% do conteúdo)
   - Passo a passo executável
   - Screen share + webcam
   - Arquivos/templates downloadáveis

2. **Bastidores** (10%)
   - Processos reais do expert
   - Erros e aprendizados
   - Behind the scenes

3. **Interativo** (10%)
   - Q&A ao vivo recorrente (semanal/quinzenal)
   - Análise de casos enviados
   - Desafios/exercícios

### 6.3 Conteúdo “para iniciante” (reduz churn cedo)
- Trilha “Do Zero”: 5–7 aulas curtas + checklist + primeira prática guiada
- Diagnóstico/quiz inicial para direcionar conteúdo (nível, objetivos, contexto)
- Aula “erros comuns” + plano de 7 dias (quick win)

---

## 7. Estratégia de Marketplace Interno

### 7.1 Produtos Adequados

#### Alto Ticket (R$ 1.997 - R$ 9.997)
```
✅ Mentorias em grupo (12 semanas)
✅ Consultoria 1-on-1
✅ Eventos presenciais
✅ Certificação de Domador
✅ Acompanhamento personalizado
```

#### Médio Ticket (R$ 297 - R$ 997)
```
✅ Cursos aprofundados específicos
✅ Templates/ferramentas profissionais
✅ Kits de produtos físicos
✅ Workshops gravados
✅ Comunidade premium adicional
```

#### Baixo Ticket (R$ 47 - R$ 197)
```
✅ Ebooks/guias
✅ Checklists premium
✅ Aulas avulsas especializadas
✅ Produtos físicos unitários
✅ Acessórios/merchandising
```

### 7.2 Funil de Upsell Interno

```
Novo Assinante (Dia 0)
├── Bem-vindo + Orientação inicial
├── Consumo de 3-5 vídeos
│
Semana 2-3 (Engajamento)
├── Quiz/diagnóstico personalizado
├── Oferta produto específico para nível
│
Mês 2 (Aprofundamento)
├── Convite para live especial
├── Apresentação de mentoria/grupo
│
Mês 3+ (Fidelização)
├── Ofertas exclusivas para membros
├── Early access a lançamentos
└── Programa de indicação (desconto)
```

### 7.3 Cursos de Parceiros

A plataforma também hospedará cursos de especialistas parceiros, agregando valor e diversificando o catálogo.

#### Modelo de Parceria
```
Tipos de Parceiros:
├── Veterinários especializados em equinos
├── Especialistas em nutrição equina
├── Treinadores de modalidades específicas
├── Ferradores e casqueadores experientes
└── Outros profissionais do meio equestre

Formato de Comissionamento:
├── Parceiro recebe: 50% do valor do curso
├── Plataforma retém: 50% (hospedagem + audiência)
└── Modelo win-win: parceiro ganha alcance, plataforma ganha conteúdo
```

#### Benefícios para o Assinante
```
✅ Acesso a múltiplos especialistas em um só lugar
✅ Conteúdo complementar e diversificado
✅ Diferentes perspectivas e metodologias
✅ Formação mais completa no mundo equestre
🔜 Descontos na loja de produtos (futuro)
```

#### Benefícios para a Plataforma
```
✅ Aumento do catálogo sem custo de produção próprio
✅ Atração de novas audiências (seguidores dos parceiros)
✅ Maior valor percebido da assinatura
✅ Diferenciação competitiva
✅ Redução de churn (mais razões para ficar)
```

#### Critérios para Seleção de Parceiros
```
├── Expertise comprovada na área
├── Conteúdo complementar (não concorrente direto)
├── Qualidade de produção mínima aceitável
├── Alinhamento com valores da plataforma
└── Audiência própria (desejável, não obrigatório)
```

---

## 8. Métricas de Sucesso (KPIs)

### 8.1 Métricas de Assinatura

```
MRR (Monthly Recurring Revenue): Receita recorrente mensal
Churn Rate: < 5%/mês (< 40%/ano é saudável)
LTV (Lifetime Value): R$ 1.500+ (meta)
CAC (Custo de Aquisição): < R$ 200
LTV/CAC Ratio: > 3:1 (ideal: 5:1)
```

### 8.2 Métricas de Engajamento

```
DAU/MAU (Daily/Monthly Active Users): > 30%
Tempo médio de visualização: > 15min/sessão
Taxa de conclusão de vídeos: > 60%
NPS (Net Promoter Score): > 50
Frequência de acesso: > 3x/semana
```

### 8.3 Métricas de Monetização

```
Taxa de upsell: 10-20% dos assinantes/ano
Ticket médio do marketplace: R$ 397
Receita por assinante/mês: R$ 100-150 (assinatura + upsells)
```

---

## 9. Plano de Ação (Roadmap)

### Fase 1 - MVP (Mês 1-2) | Custo: R$ 15.000-25.000
```
Semana 1-2: Setup técnico
├── Configurar infraestrutura
├── Implementar autenticação
├── Integrar gateway de pagamento
└── Player de vídeo básico

Semana 3-4: Conteúdo e lançamento
├── Gravar 20 vídeos iniciais
├── Criar página de vendas
├── Setup email marketing
└── Preparar oferta de fundadores

Semana 5-6: Soft launch
├── Beta com 20-30 pessoas
├── Coletar feedback
├── Ajustes finais
└── Preparar lançamento oficial
```

### Fase 2 - Crescimento (Mês 3-6) | Foco: 500 assinantes
```
├── Tráfego pago estruturado (R$ 5.000/mês)
├── Parcerias e afiliados (20% comissão)
├── Conteúdo orgânico (YouTube, Instagram)
├── Implementar funcionalidades de engajamento
└── Primeiro produto de upsell no marketplace
```

### Fase 3 - Escala (Mês 7-12) | Foco: 1.000+ assinantes
```
├── Otimização de conversão (A/B tests)
├── Expansão do marketplace (3-5 produtos)
├── App mobile nativo
├── Comunidade robusta
└── Eventos presenciais
```

---

## 10. Riscos e Mitigações

### 10.1 Riscos Principais

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Churn alto** | Média | Alto | Conteúdo diário consistente, comunidade ativa, onboarding robusto |
| **Custo de aquisição alto** | Alta | Alto | Orgânico primeiro, afiliados, conteúdo gratuito de qualidade |
| **Falta de conteúdo** | Baixa | Crítico | Banco de 30 vídeos antes do launch, produção em lote |
| **Problemas técnicos** | Média | Médio | Testes extensivos, monitoramento, suporte rápido |
| **Concorrência** | Média | Médio | Diferenciação por nicho específico e personalidade do expert |

### 10.2 Plano de Contingência

```
Se churn > 8%/mês:
├── Pesquisa urgente com cancelados
├── Implementar win-back campaigns
├── Revisar qualidade do conteúdo
└── Adicionar incentivos de permanência

Se CAC > R$ 300:
├── Pausar tráfego pago
├── Focar em orgânico e parcerias
├── Otimizar funil de conversão
└── Implementar programa de indicação

Se MRR estagnar:
├── Revisar pricing
├── Lançar campanha de reativação
├── Criar oferta limitada
└── Aumentar upsells internos
```

---

## 11. Recomendações Finais

### ✅ Fazer
1. **Lançar com preço promocional** (R$ 497/ano) - captura fundadores
2. **Produzir 30 vídeos antes do lançamento** - prova de conceito
3. **Migrar para preço regular** (R$ 597/ano ou R$ 69/mês) - após lançamento
4. **Foco em engajamento vs. volume** - qualidade > quantidade
5. **Implementar upsells desde o início** - maximiza LTV
6. **Construir comunidade forte** - reduz churn drasticamente

### ❌ Evitar
1. **Múltiplos planos no início** - confunde e complica
2. **Lançar sem conteúdo suficiente** - frustra early adopters
3. **Depender só de tráfego pago** - CAC insustentável
4. **Adicionar features sem validação** - desperdício de recursos
5. **Subestimar custo de produção** - burnout do expert
6. **Ignorar métricas de engajamento** - churn silencioso

### 🎯 Próximos Passos Imediatos

1. **Validar demanda** (Semana 1)
   - Criar página de captura
   - Rodar tráfego pago teste (R$ 500)
   - Meta: 100 leads interessados

2. **Desenvolver MVP** (Semana 2-6)
   - Contratar desenvolvedor/usar template
   - Setup infraestrutura
   - Gravar primeiros 30 vídeos

3. **Soft Launch** (Semana 7-8)
   - Oferta para lista de email
   - Meta: 30-50 fundadores
   - Coletar feedback intensivo

4. **Lançamento Oficial** (Semana 9-10)
   - Campanha estruturada
   - Meta: 200 assinantes
   - Ativar afiliados/parceiros

---

## 12. Conclusão e Viabilidade

### Veredito: ✅ PROJETO VIÁVEL E RENTÁVEL

**Justificativa**:
- Margens de 50-70% após escala
- Break-even em 2-3 meses com 100-150 assinantes
- LTV alto com contratos anuais e upsells
- Modelo comprovado (Netflix, Masterclass, etc.)
- Baixo risco técnico com stack moderna
- Escalável sem aumento proporcional de custos

**Investimento Inicial Recomendado**: R$ 25.000-40.000
```
├── Desenvolvimento MVP: R$ 15.000-25.000
├── Produção inicial conteúdo: R$ 3.000-5.000
├── Marketing lançamento: R$ 5.000-10.000
└── Reserva operacional (3 meses): R$ 2.000
```

**Retorno Esperado**:
- Mês 6: R$ 30.000-50.000/mês (líquido)
- Mês 12: R$ 80.000-150.000/mês (líquido)
- ROI: 300-500% no primeiro ano

**Próximo Passo**: Definir nicho específico do expert e validar demanda com tráfego pago teste.
