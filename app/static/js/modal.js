let sesionesSemana = [];

// Botón "nueva sesión"
$('#btn-nueva-sesion').on('click', function () {
    $('#modalSesionLabel').text('Nueva Sesión');
    $('#modo').val('agregar');
    $('#form-sesion')[0].reset();
    $('#form-sesion').attr('action', "{{ url_for('participantes.sesion_agregar') }}");
    $('#btn-guardar').removeClass('btn-warning').addClass('btn-success').text('Guardar sesión');
});

// Al seleccionar una sesión del desplegable
$('#cursos-semana').on('change', function () {
    const id = $(this).val();
    const sesion = sesionesSemana.find(s => s.id_sesion == id);
    if (sesion) {
        $('#modalSesionLabel').text('Editar Sesión');
        $('#modo').val('editar');
        $('#id_sesion').val(sesion.id_sesion);
        $('#id_curso').val(sesion.nombre_curso);
        $('#fecha').val(sesion.fecha);
        $('#horario').val(sesion.horario);
        $('#form-sesion').attr('action', `/sesiones/editar/${sesion.id_sesion}`);
        $('#btn-guardar').removeClass('btn-success').addClass('btn-warning').text('Actualizar sesión');
        const modal = new bootstrap.Modal(document.getElementById('modalSesion'));
        modal.show();
    }
});
