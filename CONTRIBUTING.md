# Guía de Contribución — Misitox37

Este documento define cómo deben trabajar todos los colaboradores
con Git en este repositorio. Es obligatorio seguirlo.

---

## 🌿 Cómo nombrar las ramas

Usa siempre este formato:

tipo/descripcion-corta

### Tipos permitidos:

| Tipo | Cuándo usarlo |
|---|---|
| `feature/` | Para agregar algo nuevo |
| `fix/` | Para corregir un error |
| `mejora/` | Para mejorar algo existente |
| `docs/` | Para cambios en documentación |

### Ejemplos:

feature/pagina de inicio
fix/error en el formulario
mejora/estilos de la navbar
docs/actualizar README, guía para instalar dependencias

Reglas:
- Todo en minúsculas
- Sé descriptivo, explica todos los cambios
- No satures con información innecesaria

---

## ✍️ Cómo escribir los commits

Formato obligatorio:

tipo: descripción en presente y minúsculas

### Tipos permitidos:

| Tipo | Cuándo usarlo |
|---|---|
| `agregar:` | Cuando añades algo nuevo |
| `corregir:` | Cuando arreglas un error |
| `actualizar:` | Cuando modificas algo existente |
| `eliminar:` | Cuando borras algo |
| `docs:` | Cambios en documentación |

### Ejemplos:

agregar: sección de cursos en la página principal
corregir: error en el botón de registro
actualizar: estilos del navbar
eliminar: archivos de prueba innecesarios
docs: añadir instrucciones de instalación

Reglas:
- Siempre en español
- Descripción en presente ("agregar" no "agregué")
- Máximo 72 caracteres
- Sin punto al final

---

## 📅 Flujo de trabajo diario

Sigue estos pasos cada vez que vayas a trabajar:

# 1. Partir de main actualizado
git checkout main && git pull

# 2. Crear tu rama
git checkout -b feature/mi-tarea

# 3. Trabajar y hacer commits
- git add .
- git commit -m "agregar: descripción"

# 4. Subir tu rama a GitHub
- git push origin feature/mi-tarea

# 5. Abrir un Pull Request en GitHub y esperar aprobaciones
# ⏳ Aquí esperas a que los revisores aprueben o pidan cambios

# 6. Si piden cambios, corriges, commiteas y vuelves al paso 4
- git add .
- git commit -m "corregir: lo que pidieron"
- git push origin feature/mi-tarea

# 7. Una vez aprobado, el merge lo hace GitHub
# Tú solo actualizas tu main local
git checkout main && git pull

---

## 🔀 Reglas para hacer Pull Request (PR)

1. El título del PR debe seguir el mismo formato que los commits
2. Describe brevemente qué hiciste y por qué en la descripción
3. Asigna al menos dos miembros del equipo como revisores
4. No puedes hacer merge tú mismo — espera las aprobaciones
5. Se requieren mínimo 2 aprobaciones antes de hacer merge a main
6. Si alguien solicita cambios, corrígelos y vuelve a pedir revisión
7. Resuelve todos los comentarios antes del merge

---

## ⛔ Está prohibido

- Hacer push directo a main
- Hacer merge sin las 2 aprobaciones requeridas
- Commits con mensajes vagos como "cambios", "fix", "asdf"
- Subir archivos que estén en el .gitignore
- Dejar ramas sin usar por más de 2 semanas