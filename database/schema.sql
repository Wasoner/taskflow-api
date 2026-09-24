-- ============================================================
-- TaskFlow API - Esquema de base de datos (PostgreSQL 16)
-- Proyecto de práctica - Gestión de tareas/proyectos
-- ============================================================
-- Ejecutar en DBeaver sobre la base de datos "proyecto_api"
-- ============================================================

-- ---------- TABLA: usuarios ----------
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,      -- NUNCA la contraseña en texto plano
    full_name     VARCHAR(100)  NOT NULL,
    is_active     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------- TABLA: proyectos ----------
CREATE TABLE projects (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id    INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- TABLA: tareas ----------
CREATE TABLE tasks (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'done')),
    priority    VARCHAR(10)  NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    due_date    DATE,
    project_id  INTEGER      NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assigned_to INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- ÍNDICES (rendimiento: consultas frecuentes) ----------
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_tasks_project  ON tasks(project_id);
CREATE INDEX idx_tasks_assignee ON tasks(assigned_to);

-- ---------- DATOS DE PRUEBA ----------
INSERT INTO users (email, password_hash, full_name) VALUES
    ('ana@example.com', '$2b$12$hash_de_ejemplo_ana',   'Ana García'),
    ('luis@example.com', '$2b$12$hash_de_ejemplo_luis', 'Luis Pérez');

INSERT INTO projects (name, description, owner_id) VALUES
    ('API TaskFlow', 'Backend REST para la entrevista', 1),
    ('Web Personal', 'Portafolio con HTML5/CSS3/TS',    1);

INSERT INTO tasks (title, status, priority, project_id, assigned_to) VALUES
    ('Definir endpoints REST', 'done',        'high', 1, 1),
    ('Crear esquema SQL',      'in_progress', 'medium', 1, 1),
    ('Diseñar mockups UI',     'pending',     'low',  2, 2);
