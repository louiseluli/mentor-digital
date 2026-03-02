"""
database/seed_modules.py — Seed learning module content into the database

Run: python -m src.database.seed_modules
"""

import json
import logging
import sys

from src.database.engine import init_db
from src.database.repository import Repository

logger = logging.getLogger(__name__)

LEARNING_MODULES = [
    {
        "slug": "vies-de-confirmacao",
        "title": "Por que acreditamos no que já pensamos?",
        "description": "Entenda o viés de confirmação — como nosso cérebro nos engana ao preferir informações que já acreditamos.",
        "topic": "bias",
        "difficulty": "beginner",
        "estimated_minutes": 5,
        "order_index": 0,
        "sections": [
            {
                "type": "explanation",
                "title": "O que é viés de confirmação?",
                "content": "Nosso cérebro tem um atalho: ele prefere informações que confirmam o que já acreditamos. Isso se chama viés de confirmação. Não é falta de inteligência — é como o cérebro funciona para economizar energia.",
            },
            {
                "type": "example",
                "title": "Como funciona na prática",
                "scenario": "Imagine que você acredita que um certo alimento faz mal. Quando vê uma notícia dizendo que faz mal, você pensa 'eu sabia!'. Mas quando vê uma pesquisa dizendo que é seguro, você pensa 'deve ser propaganda'. Nos dois casos, o viés está agindo.",
                "question": "Você já sentiu isso com algum tema?",
                "reflection": True,
            },
            {
                "type": "quiz",
                "title": "Teste seus conhecimentos",
                "question": "O viés de confirmação acontece porque:",
                "options": [
                    {
                        "id": "a",
                        "text": "Somos ignorantes",
                        "correct": False,
                        "feedback": "Não! Acontece com todas as pessoas, independente de educação.",
                    },
                    {
                        "id": "b",
                        "text": "Nosso cérebro busca atalhos",
                        "correct": True,
                        "feedback": "Isso! É um mecanismo natural do cérebro. Reconhecer isso é o primeiro passo.",
                    },
                    {
                        "id": "c",
                        "text": "As redes sociais nos manipulam",
                        "correct": False,
                        "feedback": "As redes amplificam o viés, mas ele existe naturalmente em nós.",
                    },
                ],
            },
            {
                "type": "practical_tip",
                "title": "Dica prática",
                "tip": "Quando uma notícia confirmar exatamente o que você já pensa, isso é um sinal para investigar MAIS, não menos. Tente buscar uma fonte que diga o contrário e compare.",
            },
        ],
    },
    {
        "slug": "como-avaliar-fontes",
        "title": "Essa fonte é confiável?",
        "description": "Aprenda a avaliar se uma fonte de informação é confiável usando critérios simples e práticos.",
        "topic": "sources",
        "difficulty": "beginner",
        "estimated_minutes": 7,
        "order_index": 1,
        "sections": [
            {
                "type": "explanation",
                "title": "Nem toda fonte é igual",
                "content": "Na internet, qualquer pessoa pode publicar qualquer coisa. Por isso, é fundamental saber diferenciar fontes confiáveis de fontes duvidosas. Não existe fonte 100% perfeita, mas existem sinais que ajudam a avaliar.",
            },
            {
                "type": "explanation",
                "title": "Os 5 sinais de uma fonte confiável",
                "content": "1. **Autoria clara**: Tem autor identificável e equipe jornalística.\n2. **Histórico**: Existe há anos e corrige erros publicamente.\n3. **Fontes citadas**: Cita de onde vem a informação (dados, estudos, entrevistas).\n4. **Separação de opinião e notícia**: Distingue claramente o que é fato e o que é opinião.\n5. **Múltiplas perspectivas**: Ouve diferentes lados de uma história.",
            },
            {
                "type": "example",
                "title": "Comparando fontes",
                "scenario": "Você recebe uma mensagem no WhatsApp dizendo que um alimento cura uma doença. A mensagem não tem autor, não cita nenhum estudo e pede para 'compartilhar antes que apaguem'. Compare com uma reportagem de um jornal que entrevista médicos e cita a pesquisa original. Qual te parece mais confiável?",
                "question": "O que você olha primeiro ao avaliar uma notícia?",
                "reflection": True,
            },
            {
                "type": "quiz",
                "title": "Teste seus conhecimentos",
                "question": "Qual destes NÃO é um sinal de fonte confiável?",
                "options": [
                    {
                        "id": "a",
                        "text": "Pede para compartilhar urgentemente",
                        "correct": True,
                        "feedback": "Correto! Urgência artificial é uma técnica de manipulação. Fontes sérias não pressionam você a compartilhar.",
                    },
                    {
                        "id": "b",
                        "text": "Cita a origem dos dados",
                        "correct": False,
                        "feedback": "Citar fontes é sinal de credibilidade. Isso permite que você verifique por conta própria.",
                    },
                    {
                        "id": "c",
                        "text": "Tem equipe editorial identificável",
                        "correct": False,
                        "feedback": "Ter autores e editores identificáveis é sinal de responsabilidade e transparência.",
                    },
                ],
            },
            {
                "type": "practical_tip",
                "title": "Dica prática",
                "tip": "Antes de compartilhar uma informação, pergunte: 'Quem escreveu isso? De onde vem essa informação? Posso verificar em outro lugar?'. Se não tiver resposta para nenhuma dessas perguntas, espere antes de compartilhar.",
            },
        ],
    },
    {
        "slug": "deepfakes-como-identificar",
        "title": "Quando o vídeo mente: deepfakes",
        "description": "Reconheça vídeos e áudios manipulados por inteligência artificial e proteja-se de fraudes digitais.",
        "topic": "deepfakes",
        "difficulty": "intermediate",
        "estimated_minutes": 8,
        "order_index": 2,
        "sections": [
            {
                "type": "explanation",
                "title": "O que são deepfakes?",
                "content": "Deepfakes são vídeos, áudios ou imagens manipulados por inteligência artificial para parecer reais. A tecnologia pode colocar palavras na boca de qualquer pessoa, criar rostos que não existem, ou simular a voz de alguém.",
            },
            {
                "type": "explanation",
                "title": "Sinais de um deepfake",
                "content": "Fique atento a estes sinais:\n• **Movimentos estranhos**: Piscadas irregulares, expressões faciais rígidas\n• **Bordas borradas**: Contorno do rosto ou cabelo com falhas\n• **Iluminação inconsistente**: Sombras que não batem\n• **Áudio dessincronizado**: Lábios não combinam com a fala\n• **Contexto improvável**: A pessoa nunca falaria aquilo, ou o cenário não faz sentido",
            },
            {
                "type": "example",
                "title": "No mundo real",
                "scenario": "Em 2022, um deepfake do presidente da Ucrânia circulou nas redes pedindo rendição. O vídeo tinha movimentos faciais estranhos e a voz era ligeiramente diferente. Em época de eleição no Brasil, deepfakes de candidatos são usados para confundir eleitores.",
                "question": "Você já recebeu um vídeo que parecia \"bom demais para ser verdade\"?",
                "reflection": True,
            },
            {
                "type": "quiz",
                "title": "Teste seus conhecimentos",
                "question": "Se você receber um vídeo de um político dizendo algo absurdo, qual é a melhor atitude?",
                "options": [
                    {
                        "id": "a",
                        "text": "Compartilhar para alertar outras pessoas",
                        "correct": False,
                        "feedback": "Compartilhar sem verificar é exatamente o que quem criou o deepfake quer. Você estaria ajudando a espalhar desinformação.",
                    },
                    {
                        "id": "b",
                        "text": "Procurar a declaração original em fontes confiáveis",
                        "correct": True,
                        "feedback": "Isso! Se a declaração for real, será coberta por múltiplas fontes jornalísticas. Se só existir naquele vídeo, desconfie.",
                    },
                    {
                        "id": "c",
                        "text": "Ignorar completamente",
                        "correct": False,
                        "feedback": "Ignorar não ajuda a combater a desinformação. É melhor investigar e, se for falso, ajudar a alertar as pessoas.",
                    },
                ],
            },
            {
                "type": "practical_tip",
                "title": "Dica prática",
                "tip": "Regra de ouro: se um vídeo provoca uma emoção MUITO forte (raiva, medo, indignação), espere 5 minutos antes de compartilhar. Depois, busque o assunto em sites de checagem como Aos Fatos, Lupa ou Fato ou Fake.",
            },
        ],
    },
    {
        "slug": "algoritmos-e-bolhas",
        "title": "Por que você só vê o que já gosta?",
        "description": "Entenda como os algoritmos das redes sociais criam bolhas de informação e como sair delas.",
        "topic": "algorithms",
        "difficulty": "intermediate",
        "estimated_minutes": 6,
        "order_index": 3,
        "sections": [
            {
                "type": "explanation",
                "title": "O que são bolhas de informação?",
                "content": "As redes sociais usam algoritmos para mostrar conteúdo que você provavelmente vai curtir, comentar ou compartilhar. Parece bom, mas criou um efeito colateral: você só vê informações que reforçam o que já pensa. Isso se chama 'bolha de informação' ou 'câmara de eco'.",
            },
            {
                "type": "explanation",
                "title": "Como os algoritmos funcionam",
                "content": "Quando você curte um post sobre saúde alternativa, o algoritmo te mostra MAIS conteúdo parecido. Quando você para de ver notícias de um jornal, ele para de mostrar. Com o tempo, você vive em um mundo digital onde todo mundo parece concordar com você — mas é só porque o algoritmo escondeu quem discorda.",
            },
            {
                "type": "example",
                "title": "Redes sociais e polarização",
                "scenario": "Maria e João são vizinhos, mas no WhatsApp vivem em mundos diferentes. Maria está em 8 grupos que compartilham remédios caseiros e desconfia de vacinas. João está em grupos de ciência e acha absurdo quem desconfia. Nenhum dos dois vê o que o outro recebe. Os dois acham que 'todo mundo pensa como eu'.",
                "question": "Quantos dos seus grupos de WhatsApp têm pessoas que pensam diferente de você?",
                "reflection": True,
            },
            {
                "type": "quiz",
                "title": "Teste seus conhecimentos",
                "question": "Como você pode \"furar\" sua bolha de informação?",
                "options": [
                    {
                        "id": "a",
                        "text": "Seguir apenas amigos e família",
                        "correct": False,
                        "feedback": "Amigos e família tendem a pensar parecido com você. Isso reforça a bolha.",
                    },
                    {
                        "id": "b",
                        "text": "Buscar ativamente fontes diferentes das que você costuma ver",
                        "correct": True,
                        "feedback": "Isso! Diversificar fontes é o melhor antídoto contra a bolha. Não precisa concordar — basta se expor a perspectivas diferentes.",
                    },
                    {
                        "id": "c",
                        "text": "Sair de todas as redes sociais",
                        "correct": False,
                        "feedback": "Sair de tudo não é prático nem necessário. O importante é usar com consciência.",
                    },
                ],
            },
            {
                "type": "practical_tip",
                "title": "Dica prática",
                "tip": "Uma vez por semana, visite deliberadamente um site ou canal que você normalmente não acessaria. Não para concordar — mas para entender como outras pessoas veem o mundo. Isso exercita o pensamento crítico.",
            },
        ],
    },
    {
        "slug": "seus-direitos-digitais",
        "title": "Conteúdo criminoso: como denunciar e se proteger",
        "description": "Saiba identificar conteúdo criminoso online (discurso de ódio, ameaças, exploração) e como agir para se proteger e denunciar.",
        "topic": "rights",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "order_index": 4,
        "sections": [
            {
                "type": "explanation",
                "title": "Nem tudo é 'opinião'",
                "content": "Na internet, muitas pessoas confundem liberdade de expressão com permissão para tudo. Mas existem conteúdos que são CRIMES no Brasil: discurso de ódio (racismo, homofobia, intolerância religiosa), ameaças, assédio, exposição de menores, e divulgação de imagens íntimas sem consentimento.",
            },
            {
                "type": "explanation",
                "title": "Como identificar conteúdo criminoso",
                "content": "Conteúdo criminoso geralmente:\n• **Ataca grupos específicos** por raça, religião, orientação sexual, gênero\n• **Faz ameaças** diretas ou indiretas de violência\n• **Expõe pessoas** sem consentimento (fotos íntimas, dados pessoais)\n• **Incentiva violência** contra grupos vulneráveis\n• **Explora menores** de qualquer forma",
            },
            {
                "type": "explanation",
                "title": "Onde denunciar",
                "content": "No Brasil, você pode denunciar em:\n\n🔹 **SaferNet**: denuncie.org.br — canal oficial para crimes cibernéticos\n🔹 **Disque 100**: para violações de direitos humanos\n🔹 **Disque 180**: violência contra mulheres\n🔹 **Delegacia de Crimes Cibernéticos**: presencialmente ou online (varia por estado)\n🔹 **Dentro da plataforma**: WhatsApp, Instagram, Facebook, X (Twitter) — todos têm botão de denúncia",
            },
            {
                "type": "example",
                "title": "Situação real",
                "scenario": "Você está em um grupo de WhatsApp e alguém compartilha uma mensagem com xingamentos racistas contra uma pessoa pública. Outros membros riem com emojis. Isso é crime de racismo (Lei 7.716/89, alterada pela Lei 14.532/2023). Você pode sair do grupo, denunciar dentro do WhatsApp, E registrar ocorrência na delegacia.",
                "question": "Você já presenciou algo assim em algum grupo?",
                "reflection": True,
            },
            {
                "type": "quiz",
                "title": "Teste seus conhecimentos",
                "question": "Qual atitude é MAIS efetiva ao encontrar conteúdo criminoso online?",
                "options": [
                    {
                        "id": "a",
                        "text": "Responder com raiva nos comentários",
                        "correct": False,
                        "feedback": "Responder com raiva dá visibilidade ao conteúdo criminoso e pode te colocar em risco.",
                    },
                    {
                        "id": "b",
                        "text": "Salvar evidências (print), denunciar na plataforma e em órgão oficial",
                        "correct": True,
                        "feedback": "Isso! Fazer print é essencial como prova. Denunciar nos dois canais (plataforma + órgão oficial) maximiza a chance de ação.",
                    },
                    {
                        "id": "c",
                        "text": "Compartilhar para mostrar como é absurdo",
                        "correct": False,
                        "feedback": "Ao compartilhar, mesmo que por indignação, você amplifica o alcance do conteúdo criminoso. Denuncie, não divulgue.",
                    },
                ],
            },
            {
                "type": "practical_tip",
                "title": "Dica prática",
                "tip": "Se vir conteúdo criminoso: 1) Faça print/screenshot com data e hora visíveis. 2) Anote o perfil de quem postou. 3) Denuncie dentro da plataforma. 4) Se for grave (ameaça, exploração de menor), denuncie em denuncie.org.br ou na delegacia. Você não precisa enfrentar isso sozinha.",
            },
        ],
    },
]


def seed_modules():
    """Seed all learning modules into the database."""
    init_db()
    repo = Repository()
    try:
        count = repo.seed_learning_modules(LEARNING_MODULES)
        print(f"✅ {count} módulos de aprendizagem inseridos/atualizados")
    finally:
        repo.close()


if __name__ == "__main__":
    seed_modules()
