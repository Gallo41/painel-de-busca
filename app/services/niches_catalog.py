from typing import Any, Dict, List

DEFAULT_NICHES: List[Dict[str, Any]] = [
    {
        "slug": "clinicas-odontologicas",
        "name": "Clínicas Odontológicas e Dentistas",
        "category_group": "Saúde & Estética",
        "search_terms": ["clínica odontológica", "dentista", "implante dentário"],
        "cnae_codes": ["8630-5/04"],
        "recommended_offer": "SISTEMA_COMPLEXO",
        "description": "Alto ticket médio. Precisam de Landing Pages para implantes/estética e sistemas de agendamento + confirmação no WhatsApp.",
    },
    {
        "slug": "clinicas-medicas-estetica",
        "name": "Clínicas de Estética, Dermatologia e Harmonização",
        "category_group": "Saúde & Estética",
        "search_terms": ["clínica de estética", "harmonização facial", "clínica dermatológica"],
        "cnae_codes": ["9602-5/02", "8630-5/03"],
        "recommended_offer": "SITE_NOVO",
        "description": "Dependem muito do Instagram/Linktree, mas perdem clientes no Google por não terem site próprio nem catálogo de procedimentos.",
    },
    {
        "slug": "psicologia-fisioterapia",
        "name": "Psicólogos, Fisioterapia e Nutrição",
        "category_group": "Saúde & Estética",
        "search_terms": ["clínica de psicologia", "clínica de fisioterapia", "nutricionista"],
        "cnae_codes": ["8650-0/03", "8650-0/04", "8650-0/02"],
        "recommended_offer": "SITE_NOVO",
        "description": "Profissionais liberais que raramente têm site próprio ou possuem domínio .com.br livre.",
    },
    {
        "slug": "clinicas-veterinarias-pet",
        "name": "Clínicas Veterinárias e Pet Shops",
        "category_group": "Saúde & Estética",
        "search_terms": ["clínica veterinária", "hospital veterinário", "pet shop banho e tosa"],
        "cnae_codes": ["7500-1/00", "4789-0/04"],
        "recommended_offer": "SISTEMA_COMPLEXO",
        "description": "Excelente nicho tanto para site de emergência 24h quanto para sistema de agendamento de banho/tosa e carteira de vacinação.",
    },
    {
        "slug": "escritorios-advocacia",
        "name": "Escritórios de Advocacia",
        "category_group": "Jurídico, Contábil & B2B",
        "search_terms": ["escritório de advocacia", "advogado trabalhista", "advogado previdenciário"],
        "cnae_codes": ["6911-7/01"],
        "recommended_offer": "REFORMA_SITE",
        "description": "Muitos têm sites antigos sem HTTPS ou fora do ar, e escritórios maiores precisam de portal do cliente / triagem automatizada.",
    },
    {
        "slug": "contabilidade-consultoria",
        "name": "Escritórios de Contabilidade e Consultoria",
        "category_group": "Jurídico, Contábil & B2B",
        "search_terms": ["escritório de contabilidade", "contador", "consultoria empresarial"],
        "cnae_codes": ["6920-6/01", "7020-4/00"],
        "recommended_offer": "SISTEMA_COMPLEXO",
        "description": "Sites desatualizados dos anos 2010; ótima oportunidade de modernização + área do cliente ou integradores.",
    },
    {
        "slug": "imobiliarias-corretores",
        "name": "Imobiliárias e Construtoras Locais",
        "category_group": "Imobiliário & Construção",
        "search_terms": ["imobiliária", "construtora", "corretor de imóveis"],
        "cnae_codes": ["6821-8/01", "4120-4/00"],
        "recommended_offer": "SISTEMA_COMPLEXO",
        "description": "Nicho perfeito para sistemas mais complexos: portal de imóveis, filtros avançados, integração de CRM e captação de leads.",
    },
    {
        "slug": "arquitetura-engenharia-solar",
        "name": "Arquitetura, Engenharia e Energia Solar",
        "category_group": "Imobiliário & Construção",
        "search_terms": ["escritório de arquitetura", "empresa de energia solar", "engenharia civil"],
        "cnae_codes": ["7111-1/00", "4321-5/00"],
        "recommended_offer": "SITE_NOVO",
        "description": "Projetos de alto valor que precisam de portfólio visual rápido e simulador de orçamento online.",
    },
    {
        "slug": "oficinas-estetica-automotiva",
        "name": "Oficinas Mecânicas e Estética Automotiva",
        "category_group": "Serviços Locais & Automotivo",
        "search_terms": ["oficina mecânica", "centro automotivo", "estética automotiva"],
        "cnae_codes": ["4520-0/01", "4520-0/05"],
        "recommended_offer": "SITE_NOVO",
        "description": "Alto volume de buscas locais no Google Maps; a maioria não tem site ou tem domínio livre, e oficinas grandes buscam sistema de ordem de serviço.",
    },
    {
        "slug": "climatizacao-dedetizacao-reparos",
        "name": "Climatização, Dedetização e Assistência Técnica",
        "category_group": "Serviços Locais & Automotivo",
        "search_terms": ["instalação de ar condicionado", "dedetizadora", "assistência técnica eletrodomésticos"],
        "cnae_codes": ["4322-3/02", "8122-2/00"],
        "recommended_offer": "SITE_NOVO",
        "description": "Clientes de urgência que pesquisam no Google e clicam direto no primeiro site com botão de WhatsApp.",
    },
    {
        "slug": "academias-studios-pilates",
        "name": "Academias, Studios de Pilates e Crossfit",
        "category_group": "Gastronomia, Fitness & Eventos",
        "search_terms": ["studio de pilates", "academia", "box crossfit"],
        "cnae_codes": ["9313-1/00"],
        "recommended_offer": "SITE_NOVO",
        "description": "Costumam ter apenas Instagram; excelente conversão para Landing Pages de aula experimental e sistemas de agendamento de turmas.",
    },
    {
        "slug": "restaurantes-buffets-eventos",
        "name": "Restaurantes, Buffets e Espaços de Eventos",
        "category_group": "Gastronomia, Fitness & Eventos",
        "search_terms": ["buffet infantil", "espaço para eventos", "restaurante"],
        "cnae_codes": ["5620-1/02", "8230-0/02", "5611-2/01"],
        "recommended_offer": "SISTEMA_COMPLEXO",
        "description": "Precisam de cardápio digital sem taxas de marketplace, página de reservas e sistema de orçamento de eventos.",
    },
]


def get_niches_by_slugs(slugs: List[str]) -> List[Dict[str, Any]]:
    if not slugs:
        return DEFAULT_NICHES
    slug_set = set(slugs)
    return [n for n in DEFAULT_NICHES if n["slug"] in slug_set]
