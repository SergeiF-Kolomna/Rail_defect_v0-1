import cv2
import numpy as np
import PySimpleGUI as sg
import sys

# -*- coding: utf-8 -*-

point1 = None
point2 = None
frame_start = None
frame_end = None
frame_resizing = False
image = None
image_mini = None
threshold_value = 207
etalon_line = 100
scale_percent = 30 # percent of original size. To compress the image
names = []
dark_spots_dict = {}
sum=0

def calculate_distance(p1, p2):
    return (p2[0] - p1[0]) 

def calculate_area(distance, pixel_per_cm):
    return ((etalon_line**2) * distance / (pixel_per_cm*etalon_line)** 2)

def calculate_dimensions(cropped_image, pixel_per_cm):
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dark_spots = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 0:
            dimensions = calculate_area(area, pixel_per_cm)
            if dimensions > 0.1 and dimensions < 5.1:  # Check if area is more than 0,1 sq.cm. and less then 5,1 sq.sm
                (x, y, w, h) = cv2.boundingRect(contour)

                # Draw rectangle around the dark spot
                cv2.rectangle(cropped_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Store the detected dark spot
                dark_spots.append((x, y, w, h, dimensions))

    return cropped_image, dark_spots

def mouse_callback(event, x, y, flags, param):
    global point1, point2, frame_start, frame_end, frame_resizing, image_mini

    if event == cv2.EVENT_LBUTTONDOWN:
        if frame_start is None:
            frame_start = (x, y)
        elif frame_end is None:
            frame_end = (x, y)
            frame_resizing = True

    elif event == cv2.EVENT_MOUSEMOVE:
        if frame_resizing:
            frame_end = (x, y)
            temp_image = image_mini.copy()
            cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
            cv2.imshow("Image", temp_image)

    elif event == cv2.EVENT_LBUTTONUP:
        frame_resizing = False
        temp_image = image_mini.copy()
        cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
        cv2.imshow("Image", temp_image)

        # Set point1 and point2 when frame selection is complete
        if frame_start and frame_end:
            point1 = frame_start
            point2 = frame_end

def on_key(event):
    global point1, point2, image_mini, frame_start, frame_end
    
    if (event == ord('a') or event == ord("A") or event == ord("ф") or event == ord("Ф")) and frame_start and frame_end:
        frame_start = (min(frame_start[0], frame_end[0]), min(frame_start[1], frame_end[1]))
        frame_end = (max(frame_start[0], frame_end[0]), max(frame_start[1], frame_end[1]))

        if frame_start[0] == frame_end[0] or frame_start[1] == frame_end[1]:
            print("Invalid frame size. Please try again.")
            return

        cropped_image = image_mini[frame_start[1]:frame_end[1], frame_start[0]:frame_end[0]]

        pixel_per_cm = calculate_distance(point1, point2) / etalon_line
        cropped_image_with_dimensions, dark_spots = calculate_dimensions(cropped_image, pixel_per_cm)

        cv2.imshow("Cropped Image", cropped_image_with_dimensions)

        return dark_spots

def listbox_drawing(lst):
    global window_list

    event, values = window_list.read()
    print(event, values)

    if event == 'Add':
        names.append(values['-INPUT-'])
        window_list['-LIST-'].update(names)
        msg = "A new item added : {}".format(values['-INPUT-'])
        window_list['-MSG-'].update(msg)
    if event == 'Remove':
        val = lst.get()[0]
        names.remove(val)
        window_list['-LIST-'].update(names)
        msg = "A new item removed : {}".format(val)
        window['-MSG-'].update(msg)
        #window_list.close()

def on_trackbar(val):
    global threshold_value
    threshold_value = val
    cv2.imshow("Image", image_mini)

def get_dict_key(dict, value):
    for k, v in dict.items():
        if v == value:
            return k
    
#*Рисуем интерфейс*
#Open file window
layout = [
            [sg.Text('File'), sg.InputText(), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
         ]
window = sg.Window('Open file to find defects', layout)

#while True:
event, values = window.read()
#if event in (None, 'Exit', 'Cancel'):
#    break

if event == 'Submit':
    image_path = values[0] 

    #image_path = r'C:\Users\Фокин\source\repos\Rail_defect5\image_test2.jpg'
    #image_path = r'E:\AAA\image_test2.jpg'
    #image_path = 'E:\БББ\image_test2.jpg'
    #

    image = cv2.imread(image_path)
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)
    cv2.createTrackbar("Threshold", "Image", threshold_value, 255, on_trackbar)
        
    #compress image
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    image_mini = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    window.close()
    
    # I should put this variables to proprty of class
    first_enter=False #  bool variable for once fill the list
    ipass = 0       # variable for pass in listBox
    
    cv2.imshow("Image", image_mini)
    key = cv2.waitKey(0)

    dark_spots = on_key(key)
    if dark_spots:

        #формируем словарь   ///этот кусок кода для отображения окошка со списком найденных дефектов
        numbers = list(range(0, len(dark_spots)))
        dark_spots_dict =dict(zip(numbers, dark_spots))

        for i in range(len(dark_spots_dict)):
            names.append(str(i))
        layout_lst = [[sg.Text('Rail',size=(20, 1), font='Lucida',justification='left')],
                        [sg.Listbox(names, select_mode='single', key='list1', size=(30, 6))],
                        [sg.Button('Remove', font=('Times New Roman', 12)),sg.Button('Cancel', font=('Times New Roman',12)), 
                         sg.Button('Back', font=('Times New Roman',12)), sg.Button('Next', font=('Times New Roman',12)), sg.Button('Calculate', font=('Times New Roman',12))]]
        window_list=sg.Window('Defects', layout_lst)
        first_enter =True
        
        while True:
            if key == ord("q"):
                break
            sum=0
            e,v=window_list.read()
            if  v['list1'] == [] or v['list1'] == ['0']:
                v['list1']=str(ipass)
            print(e, v, ' ipass > ', ipass)

            temp_list=list(dark_spots_dict.keys())
            v['list1']=str(temp_list[int(ipass)])

            if e == 'Remove':
                names.remove(v['list1'])
                dark_spots_dict.pop(int(v['list1']))
                window_list['list1'].update(names)
                
                temp_list=list(dark_spots_dict.keys())
                #v['list1']=str(temp_list[int(ipass)])
                #ipass=int(v['list1'])
                temp2_image = image_mini.copy()
                for new_spot_list in dark_spots_dict:
                    (x, y, w, h, dimensions) = dark_spots_dict[new_spot_list]
                    cv2.rectangle(temp2_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (255, 175, 0), 2)
                ipass-=1
            elif e == 'Cancel':
                window_list.close()
                break
            elif e == 'Next':
                if ipass<len(dark_spots_dict)-1:
                    ipass+=1
                else:
                    ipass=0
                temp_list=list(dark_spots_dict.keys())
                v['list1']=str(temp_list[ipass])
            elif e == 'Back':
                if ipass>1:
                    ipass-=1
                else:
                    ipass=len(dark_spots_dict)-1
                temp_list=list(dark_spots_dict.keys())
                v['list1']=str(temp_list[ipass])
            elif e == 'Calculate':
                for i in dark_spots_dict:
                    sum += dark_spots_dict[i][4]
                cv2.putText(temp2_image, f"Summary Square: {sum:.5f} cm^2", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

            #  /// окончание куска кода для  отображения окошка со списком найденных дефектов
            temp_list=list(dark_spots_dict.keys())
            v['list1']=str(temp_list[ipass])
            #(x, y, w, h, dimensions) = dark_spots_dict[[temp_list[int(ipass)]][0]]
            (x, y, w, h, dimensions) = dark_spots_dict[int(v['list1'])]
            temp_image = image_mini.copy()
            cv2.rectangle(temp_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (0, 0, 255), 2)

            # Add dimensions text to the dark spot
            width_cm = w / (calculate_distance(point1, point2)/etalon_line)
            height_cm = h / (calculate_distance(point1, point2)/etalon_line)
            cv2.putText(temp_image, f"Square: {dimensions:.5f} cm^2", (x + frame_start[0], y + frame_start[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(temp_image, f"Width: {width_cm:.5f} cm", (x + frame_start[0], y + frame_start[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(temp_image, f"Height: {height_cm:.5f} cm", (x + frame_start[0], y + frame_start[1] + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.imshow("Image", temp_image)
            try:
                cv2.imshow("temp2_image", temp2_image)
            except: pass

cv2.destroyAllWindows()

