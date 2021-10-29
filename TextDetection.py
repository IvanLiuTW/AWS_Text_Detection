# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 21:00:05 2021

@author: Ivan, Ren Siang, Leo
"""
# Packages needed
import pandas as pd
import numpy as np
import csv
import time

# GUI
from tkinter import messagebox, filedialog, ttk, Frame
import tkinter as tk

# To read images
import cv2                        

# To transform the pictures as a compactible form with tkinter
from PIL import ImageTk, Image    

# the package of AWS 
import boto3

# --------------------------------------------------------

# Set global variables
sfname = 0
medicineData = 0
indexOfMedicine = 0
lines = []

# GUI setting
window = tk.Tk()

window.geometry('850x500')

window.resizable(True, True)

window.title('Medicine Text Detection')

align_mode = 'nswe'

pad = 5

                 
# Use Frame class to devide the window into four different parts：
# Set window as the base and div1, div2, div3 to show each parts respectively
div_size = 200 # the size of each div
img_size = div_size * 2 # the biggest part the show image
div1 = tk.Frame(window,  width=img_size , height=img_size , bg='white')
div2 = tk.Frame(window,  width=div_size , height=div_size , bg='white')
div3 = tk.Frame(window,  width=div_size , height=div_size , bg='white')

# Use grid to set Frame, and tell the window to put them by row & column
div1.grid(column=0, row=0, padx=pad, pady=pad, rowspan=2, sticky=align_mode)
div2.grid(column=1, row=0, padx=pad, pady=pad, sticky=align_mode)
div3.grid(column=1, row=1, padx=pad, pady=pad, sticky=align_mode)


video = tk.Label(div1)

# the function is used to set row and column
def define_layout(obj, cols=1, rows=1):
    
    def method(trg, col, row):
        
        for c in range(cols):    
            trg.columnconfigure(c, weight=1) 
        for r in range(rows):
            trg.rowconfigure(r, weight=1)

    if type(obj)==list:        
        [ method(trg, cols, rows) for trg in obj ]
    else:
        trg = obj
        method(trg, cols, rows)

define_layout(window, cols=2, rows=2)
define_layout([div1, div2, div3])

# --------------------------------------------------------

# the function is used to read image
def cv_imread(filePath):
    cv_img=cv2.imdecode(np.fromfile(filePath,dtype=np.uint8),-1)
    return cv_img

# the following functions are designed for the tkinter button command
def oas():
    global sfname

    sfname = filedialog.askopenfilename(title='選擇',filetypes=[('All Files','*'),("jpeg files","*.jpg"),("png files","*.png"),("gif files","*.gif")])

    
    im = Image.open(sfname) # read image
    im = cv_imread(sfname)
    cv2image = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)         # array to image
    imgtk = ImageTk.PhotoImage(image=img)   # transform the image to fit tkinter
    image_main = tk.Label(div1, image=imgtk)         
    
    # set interface
    image_main['height'] = img_size
    image_main['width'] = img_size
    image_main.grid(column=0, row=0, sticky=align_mode)
    
    video.imgtk = imgtk
    video.configure(image=imgtk)


def ods():
    # Step 1 (!!! It's necessary to have an AWS account to access the recognition service)
    with open('/Users/ivanliu/Desktop/AI大數據/new_user_credentials.csv','r') as input:
        next(input)
        reader = csv.reader(input) 
        for line in reader:
            access_key_id = line[2]
            secret_access_key = line[3]
    
    # Step 2
    global medicineData

    file = '/Users/ivanliu/Desktop/Projects/Project 1 - Python - AWS Rekognition/medicine.csv'
    with open(file,'rt', newline='') as csvfile:
        rows = csv.reader(csvfile)
        medicineData = [data for data in rows]
    
    # Step 3
    medicineEngName = {medicineData[number][2].split(' ')[0] : number for number in range(1,8)}
    # split(' ')[0] -> use split() to split string into list, and get the item of index[0]
    
    # Step 4
    with open(sfname, 'rb') as imgfile:
        imgbytes = imgfile.read()
        imgfile.close()
        
    
    # Step 5
    client = boto3.client('rekognition',
                          aws_access_key_id = access_key_id,
                          aws_secret_access_key = secret_access_key,
                          region_name='us-east-1')
    
    
    # Filters={'WordFilter':{'MinConfidence':80}}  is the result of the confidence is lower than 80, it won't be returned
    response = client.detect_text(Filters={'WordFilter':{'MinConfidence':80}}, Image={'Bytes': imgbytes})
    
    
    textDetections = response['TextDetections']
    
    # response is a length 3 dict, only TextDections is useful
    # TextDections is a list, which is comprised of dict data
    # There are 5 keys, Confidence, Detected Text, Geometry, Id, and Type in each dict. 
    # DetectedText is used to compare with the picture's text.


    # Step 6
    # get the picture's text (second filtered, Confidence >=95 and all alphabets, no numbers)
    selectedText = set()
    for index in range(len(textDetections)):
        if textDetections[index]['DetectedText'].strip('"').isalpha():
            selectedText.add(textDetections[index]['DetectedText'])
    
       
    # Step 7
    # # Step 4: Use the loops to see whether selectedText is in medicineEngName. 
    # If yes, print the detected medicine infomation
    # ('許可證字號', '中文品名', '英文品名', '適應症', '劑型', '包裝', '藥品類別'); 
    # if not, print:'Not in our database'
    
    global indexOfMedicine

    for medNameSrt in medicineEngName.keys():
        for name in selectedText:
            if medNameSrt.lower() in name.lower(): 
                indexOfMedicine = medicineEngName[medNameSrt]
                #print(indexOfMedicine)
                break
        if medNameSrt.lower() in name.lower(): 
            for info in medicineData[indexOfMedicine][0:7]:
                print(info)
            break
    else: print('Warning: The medicine of the image is NOT in the database. You may take the wrong medicine.')
    

# clear all items
    for widget in Frame.winfo_children(div2):
        widget.destroy()

# scroll bar
    scrollBar = tk.Scrollbar(div2)
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
    
# Treeview elements
    tree = ttk.Treeview(div2,columns=['1','2'], show='headings', yscrollcommand=scrollBar.set)
    
# set the column width and the alignment
    tree.column('1',width=100,anchor='center')
    tree.column('2',width=300,anchor='center')

# set the row names
    tree.heading('1',text='序列')
    tree.heading('2',text='資料')
    tree.pack(side=tk.LEFT, fill=tk.Y)

# combine Treeview and scrollbar  
    scrollBar.config(command=tree.yview)

# insert the information, if the medicine is not in the database, then the indexOfMedicine == 0, or != 0
    if indexOfMedicine != 0:
        df = medicineData
        df1 = df[indexOfMedicine]
        df2 = df1[0:7]
        df3 = df[0]
        df4 = df3[0:7]
        for i in range(min(len(df4),len(df2))):
            tree.insert('', i, values=(df4[i], df2[i]))
    if indexOfMedicine == 0:
        df2 = '未輸入的藥品'
        df = medicineData
        df3 = df[0]
        df4 = df3[0:7]
        for i in range(min(len(df4),len(df2))):
            tree.insert(parent = '', index = i, values=(df4[i], df2))
    

def obs():
    MsgBox = tk.messagebox.askyesno("注意", "請問已食用藥物並要求紀錄時間嗎？")
    if MsgBox == True & indexOfMedicine != 0:
        local_time = time.localtime() # 取得時間元組
        timeString = time.strftime("%Y/%m/%d %H:%M", local_time) # 轉成想要的字串形式
        tk.messagebox.showinfo('題示','已儲存')
        
        df = medicineData      


        new_df = df[indexOfMedicine]

        
        file = '/Users/ivanliu/Desktop/Projects/Project 1 - Python - AWS Rekognition/records.csv'
        with open(file, 'a', newline='') as csvfile:
            csvWriter = csv.writer(csvfile)
            csvWriter.writerow([new_df[1], timeString])           


    if MsgBox == False & indexOfMedicine == 0:
        MsgBox.destroy()



def ocs():


    for widget in Frame.winfo_children(div2):
        widget.destroy()

    scrollBar = tk.Scrollbar(div2)
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(div2,columns=['1','2'], show='headings', yscrollcommand=scrollBar.set)
    
    tree.column('1', width=div_size, anchor='center')
    tree.column('2', width=div_size, anchor='center')

    tree.heading('1',text='藥品名')
    tree.heading('2',text='食藥日期')
    tree.pack(side=tk.LEFT, fill=tk.Y)

    scrollBar.config(command=tree.yview)
    
# Treeview double click
    def treeviewClick(event):
        MsgBox = tk.messagebox.askyesno("注意", "請問要刪除該筆紀錄嗎？")
        file = '/Users/ivanliu/Desktop/Projects/Project 1 - Python - AWS Rekognition/records.csv'
        if MsgBox == True:
            with open(file,'a', newline='',encoding="utf-8" ) as cvsfilie:
                csvfile = tree.selection()[0]
                tree.delete(csvfile)
            tk.messagebox.showinfo('題示','已刪除，請重新點選觀看紀錄')
        if MsgBox == False:
            MsgBox.destroy()
    tree.bind('<Double-1>', treeviewClick)  

    
    file = '/Users/ivanliu/Desktop/Projects/Project 1 - Python - AWS Rekognition/records.csv'
    for i in range(len(tree["columns"])):
        with open(file) as csvFile:
            csvReader = csv.reader(csvFile)
            datas = list(csvReader)
    for data in datas:
        tree.insert(parent = '', index = i, values = data)

# set button of the GUI   
B1 = tk.Button(div3, text="打開", command = oas)
B2 = tk.Button(div3, text="分析", command = ods)
B3 = tk.Button(div3, text="紀錄", command = obs)
B4 = tk.Button(div3, text="觀看紀錄", command = ocs)

B1.grid(column=0, row=0, sticky=align_mode)
B2.grid(column=0, row=1, sticky=align_mode)
B3.grid(column=0, row=2, sticky=align_mode)
B4.grid(column=0, row=3, sticky=align_mode)

define_layout(window, cols=2, rows=2)
define_layout(div1)
define_layout(div2, rows=2)
define_layout(div3, rows=4)

# show the window
window.mainloop()
