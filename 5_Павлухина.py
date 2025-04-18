from qgis.core import *

# Получаем слои (добавим проверку существования слоев)
stations_layer = QgsProject.instance().mapLayersByName('stations')
districts_layer = QgsProject.instance().mapLayersByName('districts')

if not stations_layer or not districts_layer:
    raise ValueError("Не найдены один или оба требуемых слоя (stations/districts)")

stations_layer = stations_layer[0]
districts_layer = districts_layer[0]

# Проверяем наличие необходимых полей в станциях
required_fields = ['some_value', 'random_1']
for field in required_fields:
    if field not in stations_layer.fields().names():
        raise ValueError(f"В слое stations отсутствует обязательное поле: {field}")

# Создаем слой буферов
buffer_layer = QgsVectorLayer('Polygon?crs=' + stations_layer.crs().authid(), 'buffers',
                              'memory')  # Используем CRS исходного слоя
buffer_provider = buffer_layer.dataProvider()
buffer_provider.addAttributes(stations_layer.fields())
buffer_layer.updateFields()

# Часть 1: Буферизация станций с random_1 < 70
buffer_features = []
for station in stations_layer.getFeatures():
    try:
        some_value = float(station['some_value'])
        random_1 = float(station['random_1'])

        if random_1 < 70:
            radius = some_value * 30
            # Добавим проверку геометрии
            if station.geometry():
                buffer_geom = station.geometry().buffer(radius, 8)
                if buffer_geom.isGeosValid():
                    new_feature = QgsFeature()
                    new_feature.setGeometry(buffer_geom)
                    new_feature.setAttributes(station.attributes())
                    buffer_features.append(new_feature)

    except (ValueError, TypeError) as e:
        print(f"Ошибка обработки станции ID {station.id()}: {str(e)}")
        continue

if buffer_features:
    buffer_provider.addFeatures(buffer_features)
    buffer_layer.updateExtents()
    QgsProject.instance().addMapLayer(buffer_layer)
else:
    print("Нет станций, удовлетворяющих условию random_1 < 70")

# Часть 2: Поиск пересечений с районами
selected_districts = []
for buffer_feature in buffer_layer.getFeatures():
    if not buffer_feature.geometry():
        continue

    for district in districts_layer.getFeatures():
        if district.geometry() and buffer_feature.geometry().intersects(district.geometry()):
            selected_districts.append(district.id())

# Выделяем районы и выводим статистику
if selected_districts:
    districts_layer.select(selected_districts)
    print(f"Успешно! Выделено районов: {len(selected_districts)}")
    # Добавим визуальное выделение
    iface.mapCanvas().zoomToSelected(districts_layer)
    iface.mapCanvas().refresh()
else:
    print("Нет пересекающихся районов")