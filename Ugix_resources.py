# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Ugix_resources
                                 A QGIS plugin
 This plugin is used to get the data from ugix server
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-03
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Sirpi
        email                : shine@sirpi.io
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import pandas as pd
import requests
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog, QListWidgetItem
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsFields, QgsField, QgsProject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
                       QgsPointXY, QgsMultiPolygon, QgsMultiLineString,
                       QgsLineString, QgsPolygon, QgsMultiPoint, QgsPoint,
                        QgsWkbTypes, QgsProject,QgsCoordinateReferenceSystem,QgsCoordinateTransform,)
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem,QVBoxLayout
import webbrowser
from PyQt5.QtWidgets import QApplication, QProgressDialog
import time
import os.path
import requests
import json
from .resources import *
from .Ugix_resources_dialog import Ugix_resourcesDialog
from .login_dialog import LoginDialog
from qgis.gui import QgsMapToolIdentifyFeature,QgsMapTool
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import  QgsRaster
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY, QgsFeature
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsMarkerSymbol, QgsSvgMarkerSymbolLayer

class MapToolIdentifyFeature(QgsMapToolIdentifyFeature):
    def __init__(self, canvas, iface):
        super().__init__(canvas)
        self.iface = iface
        self.canvas = canvas


    def canvasReleaseEvent(self, event):
        results = self.identify(event.x(), event.y(), self.TopDownStopAtFirst, self.VectorLayer)
        if results:
            # Extract feature from results
            feature = results[0].mFeature
            
            # Get attribute names and values
            field_names = [field.name() for field in feature.fields()]
            attrs = feature.attributes()

            # Format the attributes as key-value pairs
            formatted_attrs = "\n".join(f"{field_names[i]}: {attrs[i]}" for i in range(len(attrs)))
            
            # Show formatted feature attributes in a message box
            QMessageBox.information(None, "Feature Attributes", formatted_attrs)


            
class Ugix_resources:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.map_tool_identify_feature = MapToolIdentifyFeature(self.canvas, self.iface)
        self.canvas.setMapTool(self.map_tool_identify_feature)


        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, 'gdi_plugin_icon.png')
        # self.marker_path = os.path.join(self.plugin_dir, 'generic_marker.png')

        self.access_token = None  # Initialize access token

        # Initialize client_id and client_secret
        self.client_id = None
        self.client_secret = None
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'Ugix_resources_{locale}.qm')

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Ugix_resources')

        self.first_start = None

        # Dialog instances
        self.login_dialog = None
        self.dlg = None

        # Initialize dialog and connect radio buttons to filter function
        self.dlg = Ugix_resourcesDialog()
        self.dlg.radioButtonAll.toggled.connect(self.filter_data)
        self.dlg.radioButtonPublic.toggled.connect(self.filter_data)
        self.dlg.radioButtonPrivate.toggled.connect(self.filter_data)

    def activate_map_tool(self):
        self.canvas.setMapTool(self.map_tool_identify_feature)


    def show_dialog(self):
        # Code to show your main dialog
        self.activate_map_tool()


    def on_login_successful(self, access_token,client_id,client_secret):
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.show_dialog()
        
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate('Ugix_resources', message)

    def fetch_api_data(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.original_data = data.get('results', [])  # Store data to be filtered
            return self.original_data
        except requests.RequestException as e:
            QMessageBox.critical(None, 'Error', f'Failed to fetch data from API: {e}')
            return None


    def filter_data(self):
        if not self.dlg:
            return

        list_widget = self.dlg.listWidget
        list_widget.clear()

        # Determine the selected radio button
        if self.dlg.radioButtonPublic.isChecked():
            filtered_data = [item for item in self.all_data if item.get('accessPolicy') == 'OPEN']
        elif self.dlg.radioButtonPrivate.isChecked():
            filtered_data = [item for item in self.all_data if item.get('accessPolicy') == 'SECURE']
        else:
            filtered_data = self.all_data  # Show all data if 'All' is selected

        # Extract labels and sort them
        sorted_data = sorted(filtered_data, key=lambda item: item.get('label', 'No label available'))

        for item in sorted_data:
            label_text = item.get('label', 'No label available')
            access_policy = item.get('accessPolicy', 'Unknown')  # Fetch access policy

            # Determine the background color based on access policy
            if access_policy == 'OPEN':
                access_policy_text = 'Public'
                access_policy_color = 'green'
            elif access_policy == 'SECURE':
                access_policy_text = 'Private'
                access_policy_color = 'red'
            else:
                access_policy_text = access_policy
                access_policy_color = 'black'

            # Create a QWidget to hold the label and the colored box
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(10, 20, 10, 20)
            layout.setSpacing(20)

            # Create the label
            label = QLabel(label_text)
            label.setFixedWidth(200)  # Set a fixed width for the label
            label.setWordWrap(True)

            # Create the colored box
            color_box = QWidget()
            color_box.setFixedSize(60, 20)  # Set a fixed size for the colored box
            color_box.setStyleSheet(f"background-color: {access_policy_color};")

            # Create the text label inside the colored box
            text_label = QLabel(access_policy_text)
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setStyleSheet("color: white;")

            # Use a layout for the color box to center the text
            color_box_layout = QVBoxLayout(color_box)
            color_box_layout.setContentsMargins(0, 0, 0, 0)
            color_box_layout.addWidget(text_label)

            # Add the label and colored box to the layout
            layout.addWidget(label)
            layout.addWidget(color_box)

            # Create a QListWidgetItem and set the widget
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())  # Ensure the size hint is set
            list_widget.addItem(list_item)
            list_widget.setItemWidget(list_item, item_widget)

            # Store the item data
            list_item.setData(Qt.UserRole + 1, item)  # Ensure proper data setting

        # Connect item selection event to a handler
        list_widget.itemSelectionChanged.connect(self.save_selected_item_id)



    def save_selected_item_id(self):
        list_widget = self.dlg.listWidget
        selected_items = list_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            item_data = selected_item.data(Qt.UserRole + 1)
            # Handle the selected item data
            print(f"Selected item data: {item_data}")

    def display_data_in_scroll_area(self, data):
        self.all_data = data  # Store all data initially

        # Call the filter function to display data based on the selected radio button
        self.filter_data()



    def create_vector_layer(self, geometry_type, coordinates, label, name, description):
        layer_name = label
        layer = QgsVectorLayer(geometry_type, layer_name, "memory")
        
        provider = layer.dataProvider()
        
        fields = QgsFields()
        fields.append(QgsField("Label", QVariant.String))
        fields.append(QgsField("Name", QVariant.String))
        fields.append(QgsField("Description", QVariant.String))
        provider.addAttributes(fields)
        layer.updateFields()

        features = []

        # Function to create a custom marker symbol
        def create_custom_marker_symbol(icon_path):
            if os.path.exists(icon_path):
                symbol_layer = QgsSvgMarkerSymbolLayer(icon_path)
                symbol_layer.setSize(8)  # Adjust the size as needed
                symbol = QgsMarkerSymbol.createSimple({})
                symbol.changeSymbolLayer(0, symbol_layer)
                return symbol
            else:
                QMessageBox.warning(None, 'Warning', f"Icon file not found: {icon_path}")
                return QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red'})  # Fallback to a default symbol

        if geometry_type == "MultiPolygon" or geometry_type == "Polygon":
            for polygon_coords in coordinates:
                if isinstance(polygon_coords, list):
                    polygon = []
                    for ring in polygon_coords:
                        ring_coords = []
                        for coord in ring:
                            if isinstance(coord, list) and len(coord) >= 2:
                                point = QgsPointXY(coord[0], coord[1])
                                ring_coords.append(point)
                            else:
                                QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {coord}")
                        if ring_coords:
                            polygon.append(ring_coords)
                    if polygon:
                        geom = QgsGeometry.fromPolygonXY(polygon) if geometry_type == "Polygon" else QgsGeometry.fromMultiPolygonXY([polygon])
                        feature = QgsFeature()
                        feature.setGeometry(geom)
                        feature.setAttributes([label, name, description])  # Set attributes
                        features.append(feature)
                else:
                    QMessageBox.warning(None, 'Warning', f"Invalid coordinate list format: {polygon_coords}")

        elif geometry_type == "MultiLineString" or geometry_type == "LineString":
            for line_coords in coordinates:
                if isinstance(line_coords, list):
                    polyline = []
                    for coord in line_coords:
                        if isinstance(coord, list) and len(coord) >= 2:
                            point = QgsPointXY(coord[0], coord[1])
                            polyline.append(point)
                        else:
                            QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {coord}")
                    if polyline:
                        geom = QgsGeometry.fromPolylineXY(polyline) if geometry_type == "LineString" else QgsGeometry.fromMultiPolylineXY([polyline])
                        feature = QgsFeature()
                        feature.setGeometry(geom)
                        feature.setAttributes([label, name, description])  # Set attributes
                        features.append(feature)
                else:
                    QMessageBox.warning(None, 'Warning', f"Invalid coordinate list format: {line_coords}")

        # elif geometry_type == "MultiPoint" or geometry_type == "Point":
        #     if geometry_type == "Point":
        #         for point_coords in coordinates:
        #             if isinstance(point_coords, list) and len(point_coords) >= 2:
        #                 point = QgsPointXY(point_coords[0], point_coords[1])
        #                 geom = QgsGeometry.fromPointXY(point)
        #                 feature = QgsFeature()
        #                 feature.setGeometry(geom)
        #                 feature.setAttributes([label, name, description])  # Set attributes
        #                 features.append(feature)
        #             else:
        #                 QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {point_coords}")
        #     elif geometry_type == "MultiPoint":
        #         points = []
        #         for point_coords in coordinates:
        #             if isinstance(point_coords, list) and len(point_coords) >= 2:
        #                 point = QgsPointXY(point_coords[0], point_coords[1])
        #                 points.append(point)
        #             else:
        #                 QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {point_coords}")
        #         if points:
        #             geom = QgsGeometry.fromMultiPointXY(points)
        #             feature = QgsFeature()
        #             feature.setGeometry(geom)
        #             feature.setAttributes([label, name, description])  # Set attributes
        #             features.append(feature)
            
            
        elif geometry_type == "MultiPoint" or geometry_type == "Point":
            if geometry_type == "Point":
                for point_coords in coordinates:
                    # Debug print to check the coordinates being processed
                    print(f"Processing point_coords: {point_coords}")
                    if isinstance(point_coords, list):
                        if len(point_coords) >= 2:
                            try:
                                point = QgsPointXY(float(point_coords[0]), float(point_coords[1]))
                                geom = QgsGeometry.fromPointXY(point)
                                feature = QgsFeature()
                                feature.setGeometry(geom)
                                feature.setAttributes([label, name, description])  # Set attributes
                                features.append(feature)
                            except (ValueError, IndexError) as e:
                                QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {point_coords}. Error: {str(e)}")
                        else:
                            QMessageBox.warning(None, 'Warning', f"Coordinate should have at least two elements: {point_coords}")
                    else:
                        QMessageBox.warning(None, 'Warning', f"Coordinate is not a list: {point_coords}")
            elif geometry_type == "MultiPoint":
                points = []
                for point_coords in coordinates:
                    # Debug print to check the coordinates being processed
                    print(f"Processing point_coords: {point_coords}")
                    if isinstance(point_coords, list):
                        if len(point_coords) >= 2:
                            try:
                                point = QgsPointXY(float(point_coords[0]), float(point_coords[1]))
                                points.append(point)
                            except (ValueError, IndexError) as e:
                                QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {point_coords}. Error: {str(e)}")
                        else:
                            QMessageBox.warning(None, 'Warning', f"Coordinate should have at least two elements: {point_coords}")
                    else:
                        QMessageBox.warning(None, 'Warning', f"Coordinate is not a list: {point_coords}")
                if points:
                    geom = QgsGeometry.fromMultiPointXY(points)
                    feature = QgsFeature()
                    feature.setGeometry(geom)
                    feature.setAttributes([label, name, description])  # Set attributes
                    features.append(feature)
            
            # Apply custom icon to the point geometries
            icon_path = ':/plugins/Ugix_resources/generic_marker.svg'  # Update this path to your icon file
            marker_symbol = create_custom_marker_symbol(icon_path)
            layer.renderer().setSymbol(marker_symbol)

        provider.addFeatures(features)
        QgsProject.instance().addMapLayer(layer)





    def on_ok_clicked(self):
        if not self.access_token:
            QMessageBox.warning(None, 'Warning', 'Access token not available. Please log in first.')
            return

        # # Display the access token in a popup
        # QMessageBox.information(None, 'Access Token', f"Access Token: {self.access_token}")

        # QMessageBox.information(None, 'Access Token', f"client_id: {self.client_id}")
        Public_data_access_token = self.access_token
        
        list_widget = self.dlg.listWidget
        selected_item = list_widget.currentItem()

        if selected_item is None:
            QMessageBox.warning(None, 'Warning', 'No item selected.')
            return

        item_data = selected_item.data(Qt.UserRole + 1)
        if item_data is None:
            QMessageBox.warning(None, 'Warning', 'No valid data available for the selected item.')
            return

        access_policy = item_data.get('accessPolicy', 'Unknown')
        # if access_policy == 'SECURE':
        #     resource_group = item_data.get('resourceGroup', 'Unknown')
        #     url = f'https://catalogue.geospatial.org.in/dataset/{resource_group}'
            
        #     message_box = QMessageBox()
        #     message_box.setIcon(QMessageBox.Information)
        #     message_box.setWindowTitle('Private Data')
        #     message_box.setText('You do not have access to view this data.')
        #     message_box.setInformativeText('Please visit the UGIX page to request access.')
        #     visit_page_button = message_box.addButton('Visit Page', QMessageBox.ActionRole)
        #     message_box.addButton(QMessageBox.Ok)
        #     message_box.exec_()

        #     if message_box.clickedButton() == visit_page_button:
        #         webbrowser.open(url)

        #     return

        # item_id = item_data.get('id')
        # if not item_id:
        #     QMessageBox.warning(None, 'Warning', 'No ID available for the selected item.')
        #     return

        # progress_dialog = QProgressDialog("Fetching and processing data, please wait...", "Cancel", 0, 100)
        # progress_dialog.setWindowTitle("Loading")
        # progress_dialog.setWindowModality(Qt.ApplicationModal)
        # progress_dialog.setMinimumDuration(0)
        # progress_dialog.setValue(0)
        # progress_dialog.setStyleSheet("QLabel { color : black; }")
        # progress_dialog.show()

        # QApplication.processEvents()

        # offset = 1
        # all_features = []

        # try:
        #     while True:
        #         url = f'https://geoserver.dx.gsx.org.in/collections/{item_id}/items'
        #         params = {'offset': offset}
        #         headers = {
        #             'Content-Type': 'application/json',
        #             'Authorization': f'Bearer {self.access_token}'
        #         }

        #         response = requests.get(url, params=params, headers=headers)
        #         response.raise_for_status()


        #         # # Display headers in a popup
        #         # response_headers = response.headers
        #         # headers_str = "\n".join(f"{key}: {value}" for key, value in response_headers.items())
        #         # QMessageBox.information(None, 'Response Headers', headers_str)



        #         response_data = response.json()

        #         features = response_data.get('features', [])
        #         all_features.extend(features)

        #         number_matched = response_data.get('numberMatched', 0)
        #         number_returned = response_data.get('numberReturned', 0)

        #         offset += number_returned

        #         if number_matched > 0:
        #             progress_value = int((offset / number_matched) * 100)
        #             progress_dialog.setValue(progress_value)
        #             QApplication.processEvents()

        #         if offset >= number_matched:
        #             break



        if access_policy == 'SECURE':
            resource_group = item_data.get('resourceGroup', 'Unknown')
            url = f'https://catalogue.geospatial.org.in/dataset/{resource_group}'
            
            # client_id = "f1309bc3-5f84-4840-b489-185f62521238"
            # client_secret = "20efea7113f58dd7a7b56f2dca4a3a14e4192859"
            
            # client_id =self.client_id
            # client_secret =self.client_secret

        



            # Fetch token for secure access
            token_url = 'https://dx.gsx.org.in/auth/v1/token'
            token_headers = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret,
                'Content-Type': 'application/json',
                # 'Authorization': f'Bearer {self.access_token}'
                }
            token_body = {
                "itemId": item_data.get('id'),
                "itemType": "resource",
                "role": "consumer"
            }

            try:
                token_response = requests.post(token_url, json=token_body, headers=token_headers)
                token_response.raise_for_status()

                token_data = token_response.json()
                self.access_token = token_data['results']['accessToken']
                # response_json = json.loads(token_response.replace("'", '"'))
                # self.access_token = response_json.get('results', {}).get('accessToken', None)

                if not self.access_token:
                    raise ValueError("Access token not received.")
            except Exception as e:
                ###############
                # QMessageBox.information(None, 'Access Token', f"client_id: {self.client_id}")

                message_box = QMessageBox()
                message_box.setIcon(QMessageBox.Information)
                message_box.setWindowTitle('Private Data')
                message_box.setText('You do not have access to view this data.')
                message_box.setInformativeText('Please visit the GDI page to request access.')
                visit_page_button = message_box.addButton('Visit Page', QMessageBox.ActionRole)
                message_box.addButton(QMessageBox.Ok)
                message_box.exec_()

                if message_box.clickedButton() == visit_page_button:
                    webbrowser.open(url)

                return

        item_id = item_data.get('id')
        if not item_id:
            QMessageBox.warning(None, 'Warning', 'No ID available for the selected item.')
            return

        progress_dialog = QProgressDialog("Fetching and processing data, please wait...", "Cancel", 0, 100)
        progress_dialog.setWindowTitle("Loading")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.setStyleSheet("QLabel { color : black; }")
        progress_dialog.show()

        QApplication.processEvents()

        offset = 1
        all_features = []

        try:
            while True:
                url = f'https://geoserver.dx.geospatial.org.in/collections/{item_id}/items'
                params = {'offset': offset}
                headers = {
                    'Content-Type': 'application/json'
                }

                # Add Authorization header if access_token is available
                if self.access_token:
                    headers['Authorization'] = f'Bearer {self.access_token}'
                ####################
                # QMessageBox.information(None, 'Access Token', f"Access Token: {self.access_token}")

                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()

                response_data = response.json()

                features = response_data.get('features', [])
                all_features.extend(features)

                number_matched = response_data.get('numberMatched', 0)
                number_returned = response_data.get('numberReturned', 0)
                # QMessageBox.information(None, 'number_matched', f"number_matched: {number_matched}")
                # QMessageBox.information(None, 'number_returned', f"number_returned: {number_returned}")

                offset += number_returned

                if number_matched > 0:
                    progress_value = int((offset / number_matched) * 100)
                    progress_dialog.setValue(progress_value)
                    QApplication.processEvents()

                if offset >= number_matched:
                    break

                



        except requests.RequestException as e:
            progress_dialog.close()
            QMessageBox.critical(None, 'Error', f'Failed to fetch data from API: {e}')
            if e.response is not None:
                QMessageBox.critical(None, 'Error Response', f'Error Response:\n{e.response.text}')
            return
        
        self.access_token = Public_data_access_token    
        if not all_features:
            progress_dialog.close()
            QMessageBox.information(None, 'Info', 'No features found for the selected item.')
            return

        first_feature_geometry = all_features[0]['geometry']
        geometry_type = first_feature_geometry['type']

        crs = QgsProject.instance().crs()
        layer_name = item_data.get('label', 'Unnamed Layer')
        vector_layer = QgsVectorLayer(f"{geometry_type}?crs={crs.authid()}", layer_name, "memory")
        
        provider = vector_layer.dataProvider()

        fields = QgsFields()

        property_keys = set()
        for feature_data in all_features:
            properties = feature_data.get('properties', {})
            property_keys.update(properties.keys())

        for key in property_keys:
            fields.append(QgsField(key, QVariant.String))
        provider.addAttributes(fields)
        vector_layer.updateFields()

        features = []

        source_crs = QgsCoordinateReferenceSystem('EPSG:4326')
        target_crs = crs
        transform_context = QgsProject.instance().transformContext()
        coord_transform = QgsCoordinateTransform(source_crs, target_crs, transform_context)

        for feature_data in all_features:
            geometry = feature_data.get('geometry')  # Use `.get()` to avoid KeyError

            if geometry:  # Check if geometry is not None
                coords = geometry.get('coordinates')  # Safely get coordinates
                geom_type = geometry.get('type')  # Safely get type

                if geom_type == 'Point':
                    if isinstance(coords, list) and len(coords) >= 2:
                        try:
                            point = QgsPointXY(coords[0], coords[1])
                            transformed_point = coord_transform.transform(point)
                            geom = QgsGeometry.fromPointXY(transformed_point)
                        except Exception as e:
                            QMessageBox.warning(None, 'Warning', f"Error processing coordinates: {coords}. Exception: {str(e)}")
                    else:
                        # QMessageBox.warning(None, 'Warning', f"Invalid coordinate format: {coords}. Coordinates must contain at least two elements.")
                        continue
                elif geom_type == 'LineString':
                    polyline = [QgsPointXY(coord[0], coord[1]) for coord in coords]
                    transformed_polyline = [coord_transform.transform(point) for point in polyline]
                    geom = QgsGeometry.fromPolylineXY(transformed_polyline)
                elif geom_type == 'Polygon':
                    polygon = [QgsPointXY(coord[0], coord[1]) for coord in coords[0]]
                    transformed_polygon = [coord_transform.transform(point) for point in polygon]
                    geom = QgsGeometry.fromPolygonXY([transformed_polygon])
                elif geom_type == 'MultiPoint':
                    multipoint = [QgsPointXY(coord[0], coord[1]) for coord in coords]
                    transformed_multipoint = [coord_transform.transform(point) for point in multipoint]
                    geom = QgsGeometry.fromMultiPointXY(transformed_multipoint)
                elif geom_type == 'MultiLineString':
                    multilinestring = [[QgsPointXY(coord[0], coord[1]) for coord in line] for line in coords]
                    transformed_multilinestring = [[coord_transform.transform(point) for point in line] for line in multilinestring]
                    geom = QgsGeometry.fromMultiPolylineXY(transformed_multilinestring)
                elif geom_type == 'MultiPolygon':
                    multipolygon = [[QgsPointXY(coord[0], coord[1]) for coord in ring] for ring in coords[0]]
                    transformed_multipolygon = [[coord_transform.transform(point) for point in ring] for ring in multipolygon]
                    geom = QgsGeometry.fromMultiPolygonXY([transformed_multipolygon])
                else:
                    # QMessageBox.warning(None, 'Warning', f"Unsupported geometry type: {geom_type}. Skipping feature.")
                    continue
            else:
                # QMessageBox.warning(None, 'Warning', "Feature geometry is missing or invalid.")
                continue
    
            feature = QgsFeature()
            feature.setGeometry(geom)
            
            attributes = [properties.get(key, 'No data available') for key in property_keys]
            feature.setAttributes(attributes)
            
            features.append(feature)

        provider.addFeatures(features)
        vector_layer.updateExtents()
        QgsProject.instance().addMapLayer(vector_layer)
        
        # Zoom to the extent of the newly added layer
        extent = vector_layer.extent()
        self.iface.mapCanvas().setExtent(extent)
        self.iface.mapCanvas().refresh()

        progress_dialog.setValue(100)
        progress_dialog.close()
        QMessageBox.information(None, 'Info', 'Data successfully loaded and displayed.')




    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Ugix_resources/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Ugix_resources'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def activate_map_tool(self):
        self.canvas.setMapTool(self.map_tool_identify_feature)
        
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Ugix_resources'),
                action)
            self.iface.removeToolBarIcon(action)


    
    def run(self):
        """Run method that performs all the real work"""

        # Show the login dialog
        if self.login_dialog is None:
            self.login_dialog = LoginDialog()

        if self.login_dialog.exec_() == QDialog.Accepted:  # Use QDialog.Accepted
            # Only show the main dialog if login is successful
            if self.dlg is None:
                self.dlg = Ugix_resourcesDialog()

            # Assume LoginDialog returns access_token after successful login
            self.access_token = self.login_dialog.access_token

            self.client_id = self.login_dialog.client_id
            self.client_secret = self.login_dialog.client_secret
            
            # Create and show a QProgressDialog
            progress_dialog = QProgressDialog("Logging into your Ugix account, please wait...", None, 0, 0)
            progress_dialog.setWindowTitle("Loading")
            progress_dialog.setWindowModality(Qt.ApplicationModal)
            progress_dialog.setMinimumDuration(0)  # Ensure the dialog appears immediately
            progress_dialog.setStyleSheet("QLabel { color : black; }")
            progress_dialog.show()

            # Ensure the progress dialog updates properly
            QApplication.processEvents()

            # Simulate a delay to ensure the dialog text is displayed (if needed)
            for _ in range(5):
                time.sleep(0.1)
                QApplication.processEvents()

            # Fetch data from the API immediately after successful login
            url = 'https://dx.geospatial.org.in/dx/cat/v1/search?property=[type]&value=[[iudx:Resource]]'
            data = self.fetch_api_data(url)



            # Hide the progress dialog once data is fetched
            progress_dialog.close()

            if data:
                self.display_data_in_scroll_area(data)

            # Disconnect the signal if it's already connected to prevent duplicate connections
            try:
                self.dlg.okButton.clicked.disconnect(self.on_ok_clicked)
            except TypeError:
                pass  # No connection was established yet

            # Connect OK button click event to on_ok_clicked method
            self.dlg.okButton.clicked.connect(self.on_ok_clicked)

            self.dlg.show()


