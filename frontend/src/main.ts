/* ============================================================
   TaskFlow - Frontend en TypeScript
   Se compila con: npm run build  →  dist/main.js
   ============================================================ */

/* ---------- Tipos: el contrato de datos de la API ---------- */
interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
}

type TaskStatus = "pending" | "in_progress" | "done";
type TaskPriority = "low" | "medium" | "high";

interface Task {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  project_id: number;
  assigned_to: number | null;
  created_at: string;
  updated_at: string;
}

interface ActivityLog {
  action: string;
  entity: string;
  entity_id: number | null;
  detail: Record<string, unknown>;
  timestamp: string;
  source: string;
}

/* ---------- Cliente HTTP genérico y tipado ---------- */
const API_BASE = "";

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // Errores 422 de Pydantic: [{loc: [...], msg: "..."}, ...]
    return detail
      .slice(0, 3)
      .map((e: { loc?: unknown[]; msg?: string }) => `${(e.loc ?? []).slice(1).join(".")}: ${e.msg ?? "inválido"}`)
      .join(" | ");
  }
  return JSON.stringify(detail);
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) init.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, init);
  if (res.status === 204) return undefined as T; // DELETE sin contenido

  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const detail =
      data !== null && typeof data === "object" && "detail" in data
        ? formatDetail((data as { detail: unknown }).detail)
        : `Error ${res.status}`;
    throw new Error(detail);
  }
  return data as T;
}

/* ---------- Helpers de DOM (seguridad: textContent, nunca innerHTML con datos del usuario) ---------- */
function byId(id: string): HTMLElement {
  const node = document.getElementById(id);
  if (node === null) throw new Error(`Elemento #${id} no encontrado`);
  return node;
}

function button(label: string, onClick: () => void, className = "btn btn-small"): HTMLButtonElement {
  const b = document.createElement("button");
  b.type = "button";
  b.className = className;
  b.textContent = label;
  b.addEventListener("click", onClick);
  return b;
}

function fieldValue(form: HTMLFormElement, name: string): string {
  const field = form.elements.namedItem(name);
  if (field === null) throw new Error(`Campo ${name} no encontrado`);
  if (!("value" in field)) throw new Error(`Campo ${name} no tiene valor`);
  return field.value; // TypeScript afina el tipo solo tras la comprobación "in"
}

function toast(message: string, isError = false): void {
  const box = byId("toast");
  box.textContent = message;
  box.className = `toast show${isError ? " error" : ""}`;
  window.setTimeout(() => {
    box.className = "toast";
  }, 3200);
}

/* ---------- Estado de la vista ---------- */
let selectedProjectId: number | null = null;

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  done: "Terminada",
};

const NEXT_STATUS: Record<TaskStatus, TaskStatus> = {
  pending: "in_progress",
  in_progress: "done",
  done: "pending",
};

/* ---------- Carga de datos ---------- */
async function loadUsers(): Promise<void> {
  const users = await request<User[]>("GET", "/users");
  const select = byId("owner-select") as HTMLSelectElement;
  select.replaceChildren();
  for (const user of users) {
    const option = document.createElement("option");
    option.value = String(user.id);
    option.textContent = `${user.full_name} (${user.email})`;
    select.appendChild(option);
  }
}

async function loadProjects(): Promise<void> {
  const projects = await request<Project[]>("GET", "/projects");
  const list = byId("project-list") as HTMLUListElement;
  list.replaceChildren();

  if (projects.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "No hay proyectos todavía. Crea el primero ↑";
    list.appendChild(empty);
    return;
  }

  for (const project of projects) {
    const item = document.createElement("li");
    item.className = `list-item${project.id === selectedProjectId ? " selected" : ""}`;

    const info = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = project.name;
    const desc = document.createElement("span");
    desc.className = "muted";
    desc.textContent = project.description ?? "Sin descripción";
    info.append(title, desc);

    const actions = document.createElement("div");
    actions.className = "item-actions";
    actions.append(
      button("Ver tareas", () => void selectProject(project.id)),
      button("Borrar", () => void deleteProject(project), "btn btn-small btn-danger"),
    );

    item.append(info, actions);
    list.appendChild(item);
  }
}

async function loadTasks(): Promise<void> {
  const list = byId("task-list") as HTMLUListElement;
  const label = byId("current-project");
  list.replaceChildren();

  if (selectedProjectId === null) {
    label.textContent = "";
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Selecciona un proyecto para ver sus tareas";
    list.appendChild(empty);
    return;
  }

  const tasks = await request<Task[]>("GET", `/tasks?project_id=${selectedProjectId}`);

  if (tasks.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Este proyecto no tiene tareas todavía";
    list.appendChild(empty);
    return;
  }

  for (const task of tasks) {
    const item = document.createElement("li");
    item.className = "list-item";

    const info = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = task.title;

    const meta = document.createElement("div");
    meta.className = "meta";
    const statusBadge = document.createElement("span");
    statusBadge.className = `badge badge-${task.status}`;
    statusBadge.textContent = STATUS_LABELS[task.status];
    const priorityBadge = document.createElement("span");
    priorityBadge.className = `badge badge-${task.priority}`;
    priorityBadge.textContent = task.priority;
    meta.append(statusBadge, priorityBadge);

    info.append(title, meta);

    const actions = document.createElement("div");
    actions.className = "item-actions";
    actions.append(
      button(`→ ${STATUS_LABELS[NEXT_STATUS[task.status]]}`, () => void cycleStatus(task)),
      button("Borrar", () => void deleteTask(task), "btn btn-small btn-danger"),
    );

    item.append(info, actions);
    list.appendChild(item);
  }
}

async function loadLogs(): Promise<void> {
  const logs = await request<ActivityLog[]>("GET", "/activity-logs?limit=8");
  const list = byId("log-list") as HTMLUListElement;
  list.replaceChildren();

  if (logs.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "Sin actividad registrada todavía";
    list.appendChild(empty);
    return;
  }

  for (const log of logs) {
    const item = document.createElement("li");
    const when = new Date(log.timestamp).toLocaleString("es-ES");
    item.textContent = `${when} — ${log.action} (#${log.entity_id ?? "s/n"})`;
    list.appendChild(item);
  }
}

/* ---------- Acciones ---------- */
async function refreshAll(): Promise<void> {
  await Promise.all([loadProjects(), loadTasks(), loadLogs()]);
}

async function selectProject(id: number): Promise<void> {
  selectedProjectId = id;
  const projects = await request<Project[]>("GET", "/projects");
  const current = projects.find((p) => p.id === id);
  byId("current-project").textContent = current ? `— ${current.name}` : "";
  await Promise.all([loadProjects(), loadTasks()]);
}

async function cycleStatus(task: Task): Promise<void> {
  const next = NEXT_STATUS[task.status];
  await request<Task>("PATCH", `/tasks/${task.id}`, { status: next });
  toast(`"${task.title}" → ${STATUS_LABELS[next]}`);
  await Promise.all([loadTasks(), loadLogs()]);
}

async function deleteTask(task: Task): Promise<void> {
  if (!window.confirm(`¿Borrar la tarea "${task.title}"?`)) return;
  await request<void>("DELETE", `/tasks/${task.id}`);
  toast("Tarea borrada");
  await Promise.all([loadTasks(), loadLogs()]);
}

async function deleteProject(project: Project): Promise<void> {
  if (!window.confirm(`¿Borrar el proyecto "${project.name}" y todas sus tareas?`)) return;
  await request<void>("DELETE", `/projects/${project.id}`);
  if (selectedProjectId === project.id) {
    selectedProjectId = null;
    byId("current-project").textContent = "";
  }
  toast("Proyecto borrado (tareas eliminadas en cascada)");
  await refreshAll();
}

/* ---------- Formularios ---------- */
function bindForms(): void {
  const projectForm = byId("project-form") as HTMLFormElement;
  projectForm.addEventListener("submit", (event: Event) => {
    event.preventDefault();
    void (async () => {
      try {
        const description = fieldValue(projectForm, "description");
        await request<Project>("POST", "/projects", {
          name: fieldValue(projectForm, "name"),
          description: description === "" ? null : description,
          owner_id: Number(fieldValue(projectForm, "owner_id")),
        });
        projectForm.reset();
        toast("Proyecto creado ✔");
        await Promise.all([loadProjects(), loadLogs()]);
      } catch (err) {
        toast(err instanceof Error ? err.message : "Error al crear el proyecto", true);
      }
    })();
  });

  const taskForm = byId("task-form") as HTMLFormElement;
  taskForm.addEventListener("submit", (event: Event) => {
    event.preventDefault();
    void (async () => {
      try {
        if (selectedProjectId === null) {
          throw new Error("Selecciona primero un proyecto");
        }
        await request<Task>("POST", "/tasks", {
          title: fieldValue(taskForm, "title"),
          priority: fieldValue(taskForm, "priority"),
          project_id: selectedProjectId,
        });
        taskForm.reset();
        toast("Tarea creada ✔");
        await Promise.all([loadTasks(), loadLogs()]);
      } catch (err) {
        toast(err instanceof Error ? err.message : "Error al crear la tarea", true);
      }
    })();
  });
}

/* ---------- Arranque ---------- */
async function init(): Promise<void> {
  try {
    bindForms();
    await Promise.all([loadUsers(), loadProjects(), loadTasks(), loadLogs()]);
  } catch (err) {
    toast(err instanceof Error ? err.message : "No se pudo conectar con la API", true);
  }
}

void init();
