// Funciones globales para la aplicación

// Función para mostrar/ocultar modales
function openModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.add("show")
    modal.style.display = "flex"
    document.body.style.overflow = "hidden"

    // Animación de entrada
    const modalContent = modal.querySelector(".modal-content")
    modalContent.style.animation = "slideInUp 0.3s ease"
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    const modalContent = modal.querySelector(".modal-content")
    modalContent.style.animation = "fadeOut 0.3s ease"

    setTimeout(() => {
      modal.classList.remove("show")
      modal.style.display = "none"
      document.body.style.overflow = "auto"
    }, 300)
  }
}

// Cerrar modal al hacer clic fuera
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal")) {
    const modalId = e.target.id
    closeModal(modalId)
  }
})

// Cerrar modal con tecla ESC
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const modals = document.querySelectorAll(".modal.show")
    modals.forEach((modal) => {
      closeModal(modal.id)
    })
  }
})

// Sistema de notificaciones
function showNotification(message, type = "info", duration = 5000) {
  const notification = document.createElement("div")
  notification.className = `flash-message flash-${type}`

  const icon = getNotificationIcon(type)
  notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        ${message}
        <button class="close-flash" onclick="this.parentElement.remove()">×</button>
    `

  // Crear contenedor si no existe
  let container = document.querySelector(".flash-messages")
  if (!container) {
    container = document.createElement("div")
    container.className = "flash-messages"
    document.body.appendChild(container)
  }

  container.appendChild(notification)

  // Auto-remover después del tiempo especificado
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.animation = "slideOutRight 0.3s ease"
      setTimeout(() => {
        notification.remove()
      }, 300)
    }
  }, duration)
}

function getNotificationIcon(type) {
  const icons = {
    success: "check-circle",
    error: "exclamation-triangle",
    warning: "exclamation-circle",
    info: "info-circle",
  }
  return icons[type] || "info-circle"
}

// Validaciones de formularios
function validateCURP(curp) {
  // Validación básica: 18 caracteres, formato general
  if (curp.length !== 18) {
    return false
  }

  // Verificar que tenga el formato básico: LLLLNNNNNNHLLLLLNN
  const curpRegex = /^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9]{2}$/
  return curpRegex.test(curp)
}

// Función mejorada para validar CURP en tiempo real
function setupCURPValidation() {
  const curpInput = document.getElementById("curp")
  if (curpInput) {
    curpInput.addEventListener("input", (e) => {
      let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "")

      // Limitar a 18 caracteres
      if (value.length > 18) {
        value = value.substring(0, 18)
      }

      e.target.value = value

      // Validación visual en tiempo real
      if (value.length === 18) {
        if (validateCURP(value)) {
          e.target.style.borderColor = "var(--success)"
          clearFieldError(e.target)
        } else {
          e.target.style.borderColor = "var(--error)"
          showFieldError(e.target, "Formato de CURP inválido")
        }
      } else if (value.length > 0) {
        e.target.style.borderColor = "var(--warning)"
        clearFieldError(e.target)
      } else {
        e.target.style.borderColor = ""
        clearFieldError(e.target)
      }
    })

    // Ayuda visual con placeholder dinámico
    curpInput.addEventListener("focus", (e) => {
      if (!e.target.value) {
        e.target.placeholder = "HEAA850101HTLRNN01"
      }
    })
  }
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Formatear fechas
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString("es-ES", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
}

function formatTime(timeString) {
  const time = new Date(`2000-01-01T${timeString}`)
  return time.toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
  })
}

// Funciones de utilidad para tablas
function sortTable(table, column, direction = "asc") {
  const tbody = table.querySelector("tbody")
  const rows = Array.from(tbody.querySelectorAll("tr"))

  rows.sort((a, b) => {
    const aVal = a.cells[column].textContent.trim()
    const bVal = b.cells[column].textContent.trim()

    if (direction === "asc") {
      return aVal.localeCompare(bVal)
    } else {
      return bVal.localeCompare(aVal)
    }
  })

  rows.forEach((row) => tbody.appendChild(row))
}

// Función para filtrar tablas
function filterTable(table, searchTerm) {
  const tbody = table.querySelector("tbody")
  const rows = tbody.querySelectorAll("tr")

  rows.forEach((row) => {
    const text = row.textContent.toLowerCase()
    const matches = text.includes(searchTerm.toLowerCase())
    row.style.display = matches ? "" : "none"
  })
}

// Función para exportar datos
function exportToCSV(data, filename) {
  const csv = data.map((row) => row.map((cell) => `"${cell.toString().replace(/"/g, '""')}"`).join(",")).join("\n")

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")
  const url = URL.createObjectURL(blob)

  link.setAttribute("href", url)
  link.setAttribute("download", filename)
  link.style.visibility = "hidden"

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Función para copiar al portapapeles
function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      showNotification("Copiado al portapapeles", "success", 2000)
    })
    .catch(() => {
      showNotification("Error al copiar", "error", 2000)
    })
}

// Función para confirmar acciones
function confirmAction(message, callback) {
  if (confirm(message)) {
    callback()
  }
}

// Inicialización cuando se carga la página
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar tooltips si existen
  const tooltips = document.querySelectorAll("[data-tooltip]")
  tooltips.forEach((element) => {
    element.addEventListener("mouseenter", showTooltip)
    element.addEventListener("mouseleave", hideTooltip)
  })

  // Inicializar formularios
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!validateForm(form)) {
        e.preventDefault()
      }
    })
  })

  // Auto-cerrar mensajes flash después de 5 segundos
  const flashMessages = document.querySelectorAll(".flash-message")
  flashMessages.forEach((message) => {
    setTimeout(() => {
      if (message.parentElement) {
        message.style.animation = "slideOutRight 0.3s ease"
        setTimeout(() => {
          message.remove()
        }, 300)
      }
    }, 5000)
  })

  // Configurar validación de CURP
  setupCURPValidation()
})

// Validación de formularios
function validateForm(form) {
  let isValid = true
  const requiredFields = form.querySelectorAll("[required]")

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      showFieldError(field, "Este campo es obligatorio")
      isValid = false
    } else {
      clearFieldError(field)

      // Validaciones específicas
      if (field.type === "email" && !validateEmail(field.value)) {
        showFieldError(field, "Formato de email inválido")
        isValid = false
      }

      if (field.name === "curp" && !validateCURP(field.value)) {
        showFieldError(field, "Formato de CURP inválido")
        isValid = false
      }
    }
  })

  return isValid
}

function showFieldError(field, message) {
  clearFieldError(field)

  const errorDiv = document.createElement("div")
  errorDiv.className = "field-error"
  errorDiv.textContent = message
  errorDiv.style.color = "var(--error)"
  errorDiv.style.fontSize = "0.9rem"
  errorDiv.style.marginTop = "0.5rem"

  field.parentNode.appendChild(errorDiv)
  field.style.borderColor = "var(--error)"
}

function clearFieldError(field) {
  const existingError = field.parentNode.querySelector(".field-error")
  if (existingError) {
    existingError.remove()
  }
  field.style.borderColor = ""
}

// Funciones para tooltips
function showTooltip(e) {
  const tooltip = document.createElement("div")
  tooltip.className = "tooltip"
  tooltip.textContent = e.target.getAttribute("data-tooltip")
  tooltip.style.cssText = `
        position: absolute;
        background: var(--text);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-size: 0.9rem;
        z-index: 9999;
        pointer-events: none;
        white-space: nowrap;
    `

  document.body.appendChild(tooltip)

  const rect = e.target.getBoundingClientRect()
  tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + "px"
  tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + "px"

  e.target._tooltip = tooltip
}

function hideTooltip(e) {
  if (e.target._tooltip) {
    e.target._tooltip.remove()
    delete e.target._tooltip
  }
}

// Función para manejar la carga de archivos
function handleFileUpload(input, callback) {
  const file = input.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      callback(e.target.result, file)
    }
    reader.readAsDataURL(file)
  }
}

// Función para formatear números
function formatNumber(number, decimals = 0) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number)
}

// Función para debounce (útil para búsquedas)
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Función para throttle (útil para scroll events)
function throttle(func, limit) {
  let inThrottle
  return function () {
    const args = arguments

    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// Agregar estilos adicionales para animaciones
const additionalStyles = `
@keyframes slideOutRight {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100px);
    }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

.field-error {
    animation: fadeInUp 0.3s ease;
}

.tooltip {
    animation: fadeInUp 0.2s ease;
}
`

// Agregar estilos al documento
const styleSheet = document.createElement("style")
styleSheet.textContent = additionalStyles
document.head.appendChild(styleSheet)
