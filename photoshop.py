from multiprocessing.sharedctypes import Value
from turtle import position
import PySimpleGUI as sg
import os
import tempfile
import io
import os
from turtle import color
from PIL import Image
import requests
from PIL import ImageFilter
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path
import webbrowser
from PIL import ImageEnhance
import shutil

flips = {
'FLIP_TOP_BOTTOM': Image.FLIP_TOP_BOTTOM,
'FLIP_LEFT_RIGHT': Image.FLIP_LEFT_RIGHT,
'TRANSPOSE': Image.TRANSPOSE
}

filters = {
    'SBlur': ImageFilter.BLUR,
    'BoxBlur': ImageFilter.BoxBlur(radius=9),
    'GaussianBlur': ImageFilter.GaussianBlur,
    'Contour': ImageFilter.CONTOUR,
    'Detail': ImageFilter.DETAIL,
    'Edge Enhance': ImageFilter.EDGE_ENHANCE,
    'Emboss': ImageFilter.EMBOSS,
    'Find Edges': ImageFilter.FIND_EDGES,
    'Sharpen': ImageFilter.SHARPEN,
    'Smooth': ImageFilter.SMOOTH
}

fields = {
"File name" : "File name",
"File size" : "File size",
"Model" : "Camera Model",
"ExifImageWidth" : "Width",
"ExifImageHeight" : "Height",
"DateTime" : "Creating Date",
"static_line" : "*",
"MaxApertureValue" : "Aperture",
"ExposureTime" : "Exposure",
"FNumber" : "F-Stop",
"Flash" : "Flash",
"FocalLength" : "Focal Length",
"ISOSpeedRatings" : "ISO",
"ShutterSpeedValue" : "Shutter Speed",
}


def saveThumb(input_file,output_file,format,qualit,width, height):
    Image = Image.open(input_file)
    Image.save(output_file, format=format, optmize = True, quality = qualit)
    Image.thumbnail((width,height))
    Image.save(output_file)

def saveRedux(input_file,output_file):
    Image = Image.open(input_file)
    Image.save(output_file,format = "JPEG",optmize = True,quality=1)


def imageConverter(input_file,output_file,format):
    out = output_file +'.'+ format
    Image = Image.open(input_file)
    Image.save(out, format = format,optmize =True)


def resize(input_image, coords, window):
    if os.path.exists(input_image):
        image = Image.open(input_image)
        resized_image = image.crop(coords)
        showImage(resized_image, window)

def applyEffect(originalfile,tmp_file,event,values,window):
    factor = values["-FACTOR-"]
    if event in ["P/B","Color Quantity","Sepia"]:
        Effects[event](tmp_file)
    elif event == "Normal":
        Effects[event](originalfile, tmp_file)
    else:
        Effects[event](originalfile, factor, tmp_file)

    Image = Image.open(tmp_file)
    Image.thumbnail((500,500))
    bio = io.BytesIO()
    Image.save(bio, "png")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))



def filter(tmp_file,filter,window):
    image = Image.open(tmp_file)
    if filter in ["TRANSPOSE","FLIP_TOP_BOTTOM","FLIP_LEFT_RIGHT"]:
        image = image.transpose(flips[filter])
    else:
        image = image.filter(filters[filter])
        
    image.save(tmp_file)
    image.thumbnail((500,500))
    bio = io.BytesIO()
    image.save(bio, "png")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))

def convertToPb(filename):
    image = Image.open(filename)
    image = image.convert("L")
    image.save(filename)

def convertToQtdColor(filename):
    if os.path.exists(filename):
        qtdcolors = sg.popup_get_text("Digite a quantidade de colors")
        image = Image.open(filename)
        image = image.convert("P", palette=Image.Palette.ADAPTIVE,colors = int(qtdcolors))
        image.save(filename)

def calcColorPalet(cor):
    palet = []
    r,g,b = cor
    for i in range(255):
        new_red = r * i // 255
        new_green = g * i // 255
        new_blue = b * i // 255
        palet.extend((new_red,new_green,new_blue))
    return palet

def toSepia(filename):
    if os.path.exists(filename):
        whiteVal = (255,240,192)
        palet = calcColorPalet(whiteVal)
        image = Image.open(filename)
        image = image.convert("L")
        image.putpalette(palet)
        sepia = image.convert("RGB")
        image.save(filename)

def openImage(temp_file,event,window):
    if event == "Load Image":
        filename = sg.popup_get_file('Get File')
        image = Image.open(filename)
        image.save(temp_file)
    else:
        url = sg.popup_get_text("Coloque a URL")
        image = requests.get(url)
        image = Image.open(io.BytesIO(image.content))
    showImage(image, window)
    return filename

def showImage(Image, window):
    Image.thumbnail((500,500))
    bio = io.BytesIO()
    Image.save(bio, "PNG")
    window["-IMAGE-"].erase()
    window["-IMAGE-"].draw_image(data=bio.getvalue(), location=(0,400))    

def gpsLocation(filename):
    image_path = Path(filename)
    exif_data = getExif(image_path.absolute())
    north = exif_data["GPSInfo"]["GPSLatitude"]
    east = exif_data["GPSInfo"]["GPSLongitude"]
    latitude = round(float(((north[0] * 60 + north[1]) * 60 + north[2]) / 3600),7)
    longitude = round(float(((east[0] * 60 + east[1]) * 60 + east[2]) / 3600),7)
    url = f'https://www.google.com.br/maps/@{latitude},-{longitude},15z'
    webbrowser.open(url)
def brightness(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Brightness(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def contrast(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Contrast(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def opacity(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Color(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def sharpness(filename, event, output_filename):
    image = Image.open(filename)
    enhancer = ImageEnhance.Sharpness(image)
    new_image = enhancer.enhance(event)
    new_image.save(output_filename)

def openInfoWindow(filename, window):
    layout = []
    image_path = Path(filename)
    exif_data = getExif(image_path.absolute())
    for field in fields:
        if field == "File name":
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(image_path.name,size = (25,1))]) 
        elif field == "File size":
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(image_path.stat().st_size,size = (25,1))]) 
        else:
            layout.append([sg.Text(fields[field], size=(10,1)),sg.Text(exif_data.get(field, "No data"),size = (25,1))]) 

    window = sg.Window("Second Window", layout, modal=True)
    while True:
        event,values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
    window.close()


def getExif(path):
    exif_data = {}
    try:
        image = Image.open(path)
        info = image._getexif()
    except OSError:
        info = {}

  
    if info is None:
        info = {}
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for gps_tag in value:
                sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                gps_data[sub_decoded] = value[gps_tag]
            exif_data[decoded] = gps_data
        else:
            exif_data[decoded] = value

    return exif_data


Effects = {
"P/B" : convertToPb,
"Color Quantity" : convertToQtdColor,
"Sepia": toSepia,
"Normal": shutil.copy,
"Brightness": brightness,
"colors": opacity,
"Contrast": contrast,
"Sharpness": sharpness
}

sg.theme("Light Green")

menu_def = [
['Image', ['Load Image', 'Load URL',
'Export', ['Export Thumbnail','Export with bad res',
'Export as',['JPEG', 'PNG','BMP']]]],
['filters',['Effects', ['Normal','P/B', 'Color Quantity','Sepia','Brightness','colors','Contrast','Sharpness'],
'Blur',['GaussianBlur','SBlur','BoxBlur'],
'Contour','Detail','Edge Enhance','Emboss','Find Edges','Sharpen','Smooth']],
['Edit Image',['Mirror',['FLIP_TOP_BOTTOM','FLIP_LEFT_RIGHT','TRANSPOSE']]],
['Misc', ['About','Shoe Geolocal']],
]
tmp_file = tempfile.NamedTemporaryFile(suffix=".png").name

def main():
    layout = [
        [sg.Menu(menu_def)],
        [sg.Graph(key="-IMAGE-", canvas_size=(400,400), graph_bottom_left=(0, 0),
                 graph_top_right=(400, 400), change_submits=True, drag_submits=True)],
        [sg.Slider(range=(0, 5), default_value=2.5, resolution=0.1, orientation="v", enable_events=True, key="-FACTOR-")],
    ]
    window = sg.Window("Image Viewer",layout = layout, element_justification='rc')
    dragging = False
    initPoint = endPoint = retangulo = None
    filename = None
    actualeffect =''
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WINDOW_CLOSED:
            break
        try:            
            if event in ["Load Image","Load URL"]:
                filename = openImage(tmp_file,event,window)
            if event == "Export Thumbnail":
                saveThumb(tmp_file,"Thumbnail.png","png",75,75,75)
            if event == "Export with bad res":
                saveRedux(tmp_file,"Redux.png")
            
            if event in ["JPEG","PNG","BMP"]:
                imageConverter(tmp_file,'saved',event)
    
            if event == "About":
                openInfoWindow(filename,window)
            if event == "Shoe Geolocal":
                gpsLocation(filename)

            if event in ["P/B","Color Quantity","Sepia",
            'Brightness','colors','Contrast','Sharpness']:
                window.Element('-TEXT-').update(event)
                actualeffect = event      

            if event in ['SBlur','BoxBlur','GaussianBlur','Contour','Detail',
            'Edge Enhance','Emboss','Find Edges','Sharpen','Smooth',
            'TRANSPOSE','FLIP_TOP_BOTTOM','FLIP_LEFT_RIGHT']:
                filter(tmp_file,event,window)

            if event == "-FACTOR-":
               applyEffect(filename,tmp_file,actualeffect,values,window)
            
            if event == "-IMAGE-":
                x, y = values["-IMAGE-"]
                if not dragging:
                    initPoint = (x, y)
                    dragging = True
                else:
                    endPoint = (x, y)
                if retangulo:
                    window["-IMAGE-"].delete_figure(retangulo)
                if None not in (initPoint, endPoint):
                    retangulo = window["-IMAGE-"].draw_rectangle(initPoint, endPoint, line_color='gray')
            elif event.endswith('+UP'):
                dragging = False
               
        except Exception as e:
            sg.popup_error(e)

    window.close()
    os.remove('temp.png')


if __name__ == "__main__":
    main()
