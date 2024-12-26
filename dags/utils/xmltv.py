import xml.etree.ElementTree as ET

class xmltv():

    def __init__(self):
        self.root = ET.Element("tv")

    def add_channel(self, channel_name):
        channel = ET.SubElement(self.root, "channel", id = channel_name)
        ET.SubElement(channel, "display-name").text = channel_name
    
    def add_programme(self, channel_name, start_time, end_time, programe_name, description, icon='', category = 'Desconocido'):
            # Crear el programa en el XMLTV
        programme = ET.SubElement(self.root, "programme", channel=channel_name, start=start_time, stop=end_time)
        ET.SubElement(programme, "title").text = programe_name
        ET.SubElement(programme, "desc").text = description
        ET.SubElement(programme, "icon").text = icon
        ET.SubElement(programme, "category", lang="es").text = category

    def write_xmltv(self, filepath):
        # Escribir el XML a un archivo
        tree = ET.ElementTree(self.root)
        tree.write(filepath, encoding="UTF-8", xml_declaration=True)