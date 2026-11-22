# Mis Tareas: lista de tareas en MIT App Inventor

Solución completa de una app de lista de tareas ("to-do list") hecha en
[MIT App Inventor](https://ai2.appinventor.mit.edu). Sirve como **referencia para
comparar** con la versión que está construyendo tu sobrino: no hace falta que la suya
sea idéntica, sino que funcione y que él entienda por qué funciona.

## Qué hace la app

- Escribes una tarea y tocas **Agregar**: aparece en la lista.
- No te deja agregar una tarea vacía ni una repetida (te avisa con un mensaje).
- Tocas una tarea: te pregunta *"¿Ya terminaste…?"* y, si dices **Eliminar**, la borra.
- **Borrar todo** vacía la lista, después de pedir confirmación.
- Un texto arriba de la lista cuenta cuántas tareas quedan pendientes.
- Las tareas **se guardan en el teléfono**: siguen ahí al cerrar y volver a abrir la app.

## Cómo abrirla en App Inventor

1. Descarga [`MisTareas.aia`](MisTareas.aia). En GitHub, botón **Download raw file**.
2. Entra en <https://ai2.appinventor.mit.edu>.
3. Menú **Projects → Import project (.aia) from my computer** y elige el archivo.
4. Para probarla en el celular: instala **MIT AI2 Companion** desde Play Store y, en App
   Inventor, usa **Connect → AI Companion** para escanear el código QR.

> Si tu sobrino ya tiene un proyecto que se llama `MisTareas`, App Inventor no deja
> importar otro con el mismo nombre. Renombra el archivo antes de importarlo (por
> ejemplo, `MisTareas_solucion.aia`).

---

## 1. La pantalla (Designer)

Los componentes, de arriba hacia abajo:

| Componente | Nombre | Para qué sirve | Propiedades importantes |
|---|---|---|---|
| Screen | `Screen1` | La pantalla | Title: `Mis Tareas`, AlignHorizontal: centro |
| Label | `EtiquetaTitulo` | Título grande | Text: `Mis Tareas`, FontSize 26, negrita |
| HorizontalArrangement | `FilaAgregar` | Pone la caja y el botón uno al lado del otro | Width: *Fill parent* |
| ↳ TextBox | `CajaTarea` | Donde se escribe la tarea | Width: *Fill parent*, Hint: `Escribe una tarea nueva...` |
| ↳ Button | `BotonAgregar` | Agrega la tarea | Text: `Agregar` |
| Label | `EtiquetaContador` | "Tareas pendientes: 3" | Text vacío (lo llenan los bloques) |
| ListView | `ListaTareas` | Muestra las tareas | Width y Height: *Fill parent* |
| Button | `BotonBorrarTodo` | Borra todas | Text: `Borrar todo`, fondo rojo |
| TinyDB *(invisible)* | `TinyDB1` | Guarda las tareas en el teléfono | — |
| Notifier *(invisible)* | `NotificadorTarea` | Avisos y la pregunta "¿Ya terminaste…?" | — |
| Notifier *(invisible)* | `NotificadorTodo` | La pregunta "¿Borrar todo?" | — |

**¿Por qué dos Notifier?** Cuando el usuario responde a una pregunta, se dispara el
evento `AfterChoosing` *del Notifier que la hizo*. Con dos Notifier, cada pregunta
tiene su propia respuesta y no se mezclan.

**Sobre los nombres:** cambiar `Button1` por `BotonAgregar` parece un detalle, pero es
de las mejores costumbres que puede aprender. Con 3 botones ya cuesta acordarse de
cuál era `Button2`.

---

## 2. Los bloques (Blocks)

Aquí están escritos como texto. En App Inventor se ven como piezas de colores, pero la
estructura es la misma.

### Variables globales

```
inicializar global tareas a  crear lista vacía
inicializar global indiceSeleccionado a  0
```

- `tareas` es **la lista de verdad**. El ListView solo *muestra* lo que hay en ella.
- `indiceSeleccionado` recuerda qué tarea se tocó (1 = la primera, 2 = la segunda…)
  mientras el usuario decide si la borra.

### Al abrir la app

```
cuando Screen1.Initialize
    poner global tareas a  llamar TinyDB1.GetValue
                               etiqueta: "tareas"
                               valorSiNoHayEtiqueta: crear lista vacía
    llamar mostrarTareas
```

La primera vez no hay nada guardado, así que `GetValue` devuelve la lista vacía.

### Botón Agregar

```
cuando BotonAgregar.Click
    inicializar local nuevaTarea a  recortar(CajaTarea.Text)
    en
        si   ¿está vacío? nuevaTarea
        entonces  llamar NotificadorTarea.ShowAlert  "Primero escribe una tarea"
        sino si   ¿está en la lista? cosa: nuevaTarea  lista: global tareas
        entonces  llamar NotificadorTarea.ShowAlert  "Esa tarea ya está en la lista"
        sino
            añadir elementos a la lista  lista: global tareas  elemento: nuevaTarea
            poner CajaTarea.Text a  ""
            llamar guardarTareas
            llamar mostrarTareas
```

- `recortar` (*trim*) quita los espacios del principio y del final. Sin él, una tarea
  de puros espacios "no está vacía" y entraría a la lista.
- El `si / sino si / sino` se arma con el engranaje azul del bloque `si`.

### Tocar una tarea

```
cuando ListaTareas.AfterPicking
    poner global indiceSeleccionado a  ListaTareas.SelectionIndex
    llamar NotificadorTarea.ShowChooseDialog
        mensaje:       unir("¿Ya terminaste \"", ListaTareas.Selection, "\"?")
        título:        "Tarea"
        textoBotón1:   "Eliminar"
        textoBotón2:   "Cancelar"
        cancelable:    falso

cuando NotificadorTarea.AfterChoosing  (choice)
    si   comparar textos  choice = "Eliminar"
    entonces
        quitar elemento de la lista  lista: global tareas  índice: global indiceSeleccionado
        llamar guardarTareas
        llamar mostrarTareas
```

`ShowChooseDialog` **no espera** la respuesta. Muestra la pregunta y el programa sigue.
La respuesta llega después, en otro evento (`AfterChoosing`). Por eso hay que
guardar el índice en una variable global: cuando llega la respuesta, el primer evento
ya terminó.

### Botón Borrar todo

```
cuando BotonBorrarTodo.Click
    si   ¿la lista está vacía? global tareas
    entonces  llamar NotificadorTarea.ShowAlert  "No hay tareas para borrar"
    sino      llamar NotificadorTodo.ShowChooseDialog
                  "¿Seguro que quieres borrar TODAS las tareas?", "Borrar todo",
                  "Sí, borrar", "No", falso

cuando NotificadorTodo.AfterChoosing  (choice)
    si   comparar textos  choice = "Sí, borrar"
    entonces
        poner global tareas a  crear lista vacía
        llamar guardarTareas
        llamar mostrarTareas
```

### Procedimientos (bloques propios)

```
como guardarTareas
    llamar TinyDB1.StoreValue  etiqueta: "tareas"  valorAGuardar: global tareas

como mostrarTareas
    poner ListaTareas.Elements a  global tareas
    si   ¿la lista está vacía? global tareas
    entonces  poner EtiquetaContador.Text a  "¡No tienes tareas pendientes!"
    sino      poner EtiquetaContador.Text a  unir("Tareas pendientes: ", longitud de la lista global tareas)
```

Se llaman desde cuatro lugares distintos. Sin procedimientos, habría que copiar esos
mismos bloques cuatro veces y, si algo cambia, arreglarlo en los cuatro.

---

## 3. Qué aprende con este proyecto

| Concepto | Dónde aparece |
|---|---|
| **Eventos**: el código corre cuando pasa algo | `Click`, `Initialize`, `AfterPicking`, `AfterChoosing` |
| **Variables** globales y locales | `tareas`, `indiceSeleccionado`, `nuevaTarea` |
| **Listas** | agregar, quitar por índice, buscar, contar |
| **Condiciones** | `si / sino si / sino` para validar |
| **Procedimientos** | `guardarTareas`, `mostrarTareas` |
| **Guardar datos** | `TinyDB` |
| **Separar datos de pantalla** | la lista `tareas` frente al `ListView` que la muestra |

---

## 4. Para comparar con la versión de tu sobrino

No hay una única forma correcta. Estas preguntas ayudan a revisarla:

**¿Funciona?** Pruébalo en el celular:
- [ ] Agregar una tarea la muestra en la lista.
- [ ] La caja de texto queda vacía después de agregar.
- [ ] Tocar **Agregar** sin escribir nada no agrega una línea en blanco.
- [ ] Escribir solo espacios tampoco.
- [ ] Se puede borrar una tarea, y se borra **la que se tocó** (prueba con la del medio).
- [ ] Al cerrar la app del todo y volver a abrirla, las tareas siguen ahí.
- [ ] Borrar una tarea, cerrar y abrir: la tarea borrada **no** vuelve.

El último punto es el error más común: borrar de la lista pero olvidarse de guardar
otra vez en TinyDB.

**¿Está ordenado?**
- ¿Los componentes tienen nombres claros o siguen como `Button1`, `Button2`?
- ¿Usa una variable con la lista, o intenta leer y escribir directamente en el ListView?
- ¿Hay bloques repetidos que podrían ir en un procedimiento?

**Diferencias que están bien:**
- Usar un solo botón para borrar en vez de preguntar antes.
- Escribir directamente en `ListaTareas.Elements` en vez de tener `mostrarTareas`.
- Otros nombres, colores o textos.

## 5. Desafíos para seguir

Cuando lo tenga funcionando, puede intentar:

1. **Título con contador**: que la barra de arriba diga "Mis Tareas (3)"
   (pista: `Screen1.Title` dentro de `mostrarTareas`).
2. **Contador de completadas**: "Hoy terminaste 5 tareas".
3. **Prioridad**: poner `⭐` al principio de las tareas importantes.
4. **Ordenar**: un botón que ordene la lista alfabéticamente (bloque *sort*).
5. **Editar**: tocar una tarea y poder cambiar su texto.
6. **Segunda pantalla**: una pantalla de "Tareas completadas".

---

## Archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `MisTareas.aia` | El proyecto, listo para importar en App Inventor |
| `proyecto/` | El contenido del `.aia` sin comprimir, para poder leerlo |
| `generar_aia.py` | Script que crea `proyecto/` y `MisTareas.aia` (`python3 generar_aia.py`) |

Un `.aia` es un `.zip` con otra extensión. Adentro, `Screen1.scm` describe la pantalla
(componentes y propiedades) y `Screen1.bky` describe los bloques.
