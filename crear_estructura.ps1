# Script para crear la estructura completa del proyecto
Write-Host "🏗️  Creando estructura del proyecto..." -ForegroundColor Green

# Crear directorios principales
$directorios = @(
    "control_asistencia_ayuntamiento",
    "control_asistencia_ayuntamiento\templates",
    "control_asistencia_ayuntamiento\static",
    "control_asistencia_ayuntamiento\static\css",
    "control_asistencia_ayuntamiento\static\js",
    "control_asistencia_ayuntamiento\database"
)

foreach ($dir in $directorios) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "✅ Creado: $dir" -ForegroundColor Green
    } else {
        Write-Host "📁 Ya existe: $dir" -ForegroundColor Yellow
    }
}

Write-Host "🎉 Estructura creada exitosamente!" -ForegroundColor Green
Write-Host "📝 Ahora copia los archivos del código en sus respectivas carpetas:" -ForegroundColor Cyan
Write-Host "   - main.py -> control_asistencia_ayuntamiento\" -ForegroundColor White
Write-Host "   - templates/*.html -> control_asistencia_ayuntamiento\templates\" -ForegroundColor White
Write-Host "   - static/css/styles.css -> control_asistencia_ayuntamiento\static\css\" -ForegroundColor White
Write-Host "   - static/js/main.js -> control_asistencia_ayuntamiento\static\js\" -ForegroundColor White
