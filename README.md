# tfg-workday-integration
Trabajo de fin de grado. Doble Grado en ingeniería informática y matemáticas, Universidad Complutense de Madrid.

#Descripción

El proyecto consiste en la integración del ERP Workday con el sistema cloud Mantis Bug Tracker y con el CRM (customer relationship management) Hubspot.

Workday es una de las aplicaciones más importantes en el campo de las aplicaciones de negocio para Finanzas y Recursos Humanos.

Mantis Bug Tracker es un software libre destinado a gestionar tareas de un equipo de trabajo. MBT es utilizada para probar soluciones, hacer un registro histórico con todas las alteraciones y poder gestionar un equipo de manera remota.

El proyecto tiene como objetivo que desde el portal de WorkDay se puedan llevar a cabo la mayoría de funcionalidades disponibles en MBT.
Cada usuario que vaya a hacer uso del MBT tendrá la posibilidad de logearse desde el portal de Workday.

Estando disponibles así las principales funcionalidades de MBT desde el portal de Workday.
Entre otras acciones será posible abrir una nueva incidencia, así como configurar y consultar la transición de estados de una incidencia en concreto. También se podrá cerrar las incidencias cuando se den por finalizadas, y escribir comentarios asociados a cada incidencia para comunicarse entre los usuarios.

Adicionalmente, una vez creada una nueva incidencia, existirá la posibilidad de que esta se autoasigne.
Para ello utilizaré algún algoritmo de clasificación que determinará al trabajador al que se le asigna la incidencia, basándose en el tipo de empleado, ritmo de trabajo, carga de trabajo actual, histórico de asignaciones, resoluciones de previas incidencias...