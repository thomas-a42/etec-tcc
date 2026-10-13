-- ==========================================
-- BANCO DE DADOS: PLATAFORMA DE ADOCAO ANIMAL
-- PostgreSQL
-- ==========================================

-- 1. USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    telefone VARCHAR(20),
    foto_perfil TEXT,
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'ativo',

    CONSTRAINT chk_users_status
        CHECK (status IN ('ativo', 'suspenso'))
);


-- 2. ONGS
CREATE TABLE ongs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    telefone VARCHAR(20),
    descricao TEXT,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    endereco TEXT,
    foto_perfil TEXT,
    status_verificacao VARCHAR(20) NOT NULL DEFAULT 'pendente',
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_ongs_estado
        CHECK (estado ~ '^[A-Z]{2}$'),

    CONSTRAINT chk_ongs_verificacao
        CHECK (
            status_verificacao IN (
                'pendente',
                'verificada',
                'rejeitada'
            )
        )
);


-- 3. ANUNCIOS
CREATE TABLE anuncios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ong_id UUID NOT NULL,
    nome_animal VARCHAR(100) NOT NULL,
    especie VARCHAR(30) NOT NULL,
    raca VARCHAR(100),
    sexo VARCHAR(20),
    idade INTEGER,
    porte VARCHAR(20),
    descricao TEXT NOT NULL,
    vacinado BOOLEAN NOT NULL DEFAULT FALSE,
    castrado BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'disponivel',
    data_publicacao TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_anuncios_ongs
        FOREIGN KEY (ong_id)
        REFERENCES ongs(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_anuncios_idade
        CHECK (idade IS NULL OR idade >= 0),

    CONSTRAINT chk_anuncios_sexo
        CHECK (
            sexo IS NULL OR
            sexo IN ('macho', 'femea', 'desconhecido')
        ),

    CONSTRAINT chk_anuncios_porte
        CHECK (
            porte IS NULL OR
            porte IN ('pequeno', 'medio', 'grande')
        ),

    CONSTRAINT chk_anuncios_status
        CHECK (
            status IN (
                'disponivel',
                'reservado',
                'adotado',
                'inativo'
            )
        )
);


-- 4. IMAGENS_ANUNCIOS
CREATE TABLE imagens_anuncios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anuncio_id UUID NOT NULL,
    url TEXT NOT NULL,
    principal BOOLEAN NOT NULL DEFAULT FALSE,
    ordem SMALLINT NOT NULL DEFAULT 0,
    data_upload TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_imagens_anuncios
        FOREIGN KEY (anuncio_id)
        REFERENCES anuncios(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_imagens_ordem
        CHECK (ordem >= 0)
);

-- Permite somente uma imagem principal por anuncio.
CREATE UNIQUE INDEX uq_imagem_principal_anuncio
    ON imagens_anuncios (anuncio_id)
    WHERE principal = TRUE;


-- 5. CHAT
CREATE TABLE chat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anuncio_id UUID NOT NULL,
    user_id UUID NOT NULL,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_ultima_mensagem TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',

    CONSTRAINT fk_chat_anuncios
        FOREIGN KEY (anuncio_id)
        REFERENCES anuncios(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_chat_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_chat_status
        CHECK (
            status IN ('aberto', 'encerrado', 'bloqueado')
        )
);


-- 6. MENSAGENS
CREATE TABLE mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL,
    remetente_user_id UUID,
    remetente_ong_id UUID,
    conteudo TEXT NOT NULL,
    data_envio TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lida_em TIMESTAMPTZ,

    CONSTRAINT fk_mensagens_chat
        FOREIGN KEY (chat_id)
        REFERENCES chat(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_mensagens_users
        FOREIGN KEY (remetente_user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_mensagens_ongs
        FOREIGN KEY (remetente_ong_id)
        REFERENCES ongs(id)
        ON DELETE RESTRICT,

    -- Exatamente um remetente por mensagem.
    CONSTRAINT chk_mensagens_remetente
        CHECK (
            (
                remetente_user_id IS NOT NULL
                AND remetente_ong_id IS NULL
            )
            OR
            (
                remetente_user_id IS NULL
                AND remetente_ong_id IS NOT NULL
            )
        ),

    CONSTRAINT chk_mensagens_conteudo
        CHECK (LENGTH(TRIM(conteudo)) > 0),

    CONSTRAINT chk_mensagens_leitura
        CHECK (lida_em IS NULL OR lida_em >= data_envio)
);


-- 7. ADMINS
CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ativo',
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_admins_status
        CHECK (status IN ('ativo', 'suspenso'))
);


-- ==========================================
-- INDICES PARA CONSULTAS FREQUENTES
-- ==========================================

CREATE INDEX idx_anuncios_ong
    ON anuncios (ong_id);

CREATE INDEX idx_anuncios_busca
    ON anuncios (status, especie, porte);

CREATE INDEX idx_imagens_anuncio
    ON imagens_anuncios (anuncio_id);

CREATE INDEX idx_chat_user
    ON chat (user_id);

CREATE INDEX idx_chat_anuncio
    ON chat (anuncio_id);

CREATE INDEX idx_mensagens_chat_data
    ON mensagens (chat_id, data_envio);

CREATE INDEX idx_mensagens_nao_lidas
    ON mensagens (chat_id)
    WHERE lida_em IS NULL;
