import flet as ft
from pynput import keyboard
import pyautogui
import pyperclip
from googletrans import Translator
from threading import Thread
import csv
import docx

def main(page):
    
    """
    HoverZoom main menu:
    1. Run in background and translate selected text on the go
    2. Upload file
    3. Write and translate + save to file
    4. Settings
    5. Quit
    """

    def click_background(e):
        page.go("/run_background")

    def click_uploadf(e):
        page.go("/upload_files")
    
    def click_write_translate(e):
        page.go("/write_and_translate")
    
    def click_settings(e):
        page.go("/settings")

    def click_quit(e):
        page.window_close()

    # interrupt translating if key == the setting selected by sett_stop_key (default F12)
    def on_press(key):
        try:
            if key == keyboard.Key[sett_stop_key.value.lower()]:
                print(sett_stop_key.value + ' Pressed')
                page.go('/run_background')
                return False
            
        except AttributeError:
            pass

    # triggers the listner on Rshift presses to translate selected text
    def on_release(key):
        try:
            if key ==  keyboard.Key.shift_r:
                print('Rshift Pressed')

                pyautogui.hotkey('ctrl', 'c')
                text_from_clipboard = pyperclip.paste()
                print(text_from_clipboard)

                # create thread and translate
                t = Thread(target=trans_and_store, daemon=True, args=(text_from_clipboard, ))
                t.start()
                if sett_app_fw.value == True:
                    bring_to_foreground()

        except AttributeError:
            pass
    
    # when the translated pair rows are selected on/off
    # checked: add data to the exported data table
    # unchecked: remove the entry from th exported data table
    def selected_row(e):
        if e.control.value == True:
            #add_text = e.control.data.controls[0].value
            #add_translated = e.control.data.controls[1].value
            data_to_export.rows.append(e.control.data)
        if e.control.value == False:
            data_to_export.rows.remove(e.control.data)
        page.update()

    # close modal dialog box on NO press
    def close_dlg(e=None):
        dlg_modal.open = False
        page.update()

    # after the user has selected the path to save the file
    # use csv lib to write the text + translations selected to the path selected in the file picker
    def create_and_export_csv(e: ft.FilePickerResultEvent):
        if e.path == None:
            close_dlg()
        else:
            CSV_SUFFIX = '.csv'
            selected_path = e.path + CSV_SUFFIX

            with open(selected_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Original Text", "Translated Text"])
                for row in data_to_export.rows:
                    text = row.cells[0].content.value
                    translated= row.cells[1].content.value
                    writer.writerow([text, translated])

    # after the user has selecting files to 'upload'
    # handle the doc/docx file or txt file
    # start translating the text by chunks of 1000 characters
    # save translated text as a new .txt file with the same name of the file with the suffix _translated
    def translate_selected_files(e: ft.FilePickerResultEvent):
        if e.files == None:
            pass
        else:
            page.views[-1].controls[1].controls.append(ft.ProgressRing(tooltip='Translating your files..', scale=0.8))
            page.update()
            #page.view.add(ft.ProgressRing(tooltip='Translating your files..'))
            for obj in e.files:
                if ("doc" in obj.path[-4:]) or ("docx" in obj.path[-4:]):
                    doc = docx.Document(obj.path)
                    txt = ""
                    for para in doc.paragraphs:
                        txt += para.text

                elif "txt" in  obj.path[-4:]:
                    with open (obj.path, 'r', encoding='utf-8') as file:
                        txt = file.read()

                global translated
                translated = ""
                start = 0
                stop = 1000
                chunk = txt[start:stop]
                print(chunk)
                while chunk != "":
                    t = Thread(target=trans_and_save, daemon=True, args=(chunk, ))
                    t.start()
                    t.join()
                    start += 1000
                    stop += 1000
                    chunk = txt[start:stop]
                print(translated)
                if obj.path[0:-3] == ('txt' or 'doc'):
                    with open (obj.path[0:-3]+"_translated.txt", 'w', encoding='utf-8') as file:
                        file.write(translated)
                else:
                    with open (obj.path[0:-4]+"_translated.txt", 'w', encoding='utf-8') as file:
                        file.write(translated)

            page.views[-1].controls[1].controls.pop()
            page.views[-1].controls[1].controls.append(ft.Icon(name=ft.icons.CHECK_ROUNDED))
            page.update()


    # if pressed yes on dialog window start the save_file with file picker obj
    def yes_export_to_csv(e):
        dlg_modal.open = False
        page.update()
        fp.save_file(allowed_extensions=["csv"])

    # open fp to select files to upload
    def on_upload_files(e):
        fp_upload.pick_files(allow_multiple=True, allowed_extensions=["doc", "docx", "txt"])

    # pressing on the export data button triggers a modal dialog to confirm
    def clicked_export_translations(e):
        page.update()
        fp.save_file(allowed_extensions=["csv"])
        #page.dialog = dlg_modal
        #dlg_modal.open = True
        page.update()


    # helper func after the thread running trans_and_store func has finished translating
    # to add the text, translated text pair to a data table and to be displayed
    def add_to_data_table(text, translated):
        trans_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(text)), 
                                                  ft.DataCell(ft.Text(translated)),
                                                  ft.DataCell(ft.Checkbox(value=False, on_change=selected_row, 
                                                                          data=ft.DataRow(cells=[ft.DataCell(ft.Text(text)), 
                                                                                                 ft.DataCell(ft.Text(translated))])))]
                                                  ))
        page.update()


    # helper func to translate text using googletrans lib Translator obj
    # this gets called in a seperate thread after rShift is triggered by the keyboard listener thread
    # passes the text, translated to helper func add_to_data_table
    def trans_and_store(text):
        try:
            translation = trans.translate(text, dest=sett_dest_lan.value.lower()).text
            add_to_data_table(text,translation)
        except TypeError:
            pass

    def trans_and_save(text):
        try:
            translation = trans.translate(text, dest=sett_dest_lan.value.lower()).text
            global translated
            #print(translation)
            translated += translation
        except TypeError:
            pass

    
    # pressing start translating in the background starts the keyboard listner that listens for Rshift to rranslate selected text
    # this take the page to the /stop_background view
    def click_start_trans(e):
        page.go("/stop_background")
        kl = keyboard.Listener(on_press=on_press, on_release=on_release)
        kl.start()


    # triggers the on press event for the keyboard listner, stopping the translation, same as if you pressed the shortcut
    def click_stop_trans(e):
        pyautogui.hotkey(sett_stop_key.value.lower())


    # helper func to bring window to foreground (used when user selected to bring fw on translation activations)
    def bring_to_foreground():
        page.window_to_front()
        page.update()


    def translate_new_text(e):
        global translated
        translated = ""
        #print(e.data)
        print(page.views[-1].controls[1].controls[1].content.value)
        entered_text = page.views[-1].controls[1].controls[1].content.value
        t = Thread(target=trans_and_save, daemon=True, args=(entered_text, ))
        t.start()
        t.join()

        page.views[-1].controls[1].controls[0].content.value = translated
        page.update()

        #page.views[-1].controls[1].controls.pop(0)
        #page.views[-1].controls[1].controls.insert(0, ft.Text(translated))
        page.update()



    # sets the theme mode based on selected theme. default is dark mode
    def change_theme(e):
        if sett_theme.value == str(ft.ThemeMode.DARK):
            page.theme_mode = ft.ThemeMode.DARK
            page.update()
        if sett_theme.value == str(ft.ThemeMode.LIGHT):
            page.theme_mode = ft.ThemeMode.LIGHT
            page.update()    
        if sett_theme.value == str(ft.ThemeMode.SYSTEM):
            page.theme_mode = ft.ThemeMode.SYSTEM
            page.update()


    # basic page settings setup
    page.title = "HoverTranslate"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    #page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK #DARK/SYSTEM
    page.padding = 30


    # main menu button setup
    main_label = (ft.Text("HoverTranslate", style=ft.TextThemeStyle.DISPLAY_LARGE, weight=ft.FontWeight.BOLD, text_align=ft.MainAxisAlignment.START))    
    background_btn = ft.ElevatedButton(content=ft.Container(
                                                            content=ft.Row([ft.Icon(name=ft.icons.STAR, color= 'yellow'), 
                                                                           ft.Text("Run in the background and translate on the go!"),
                                                                           ft.Icon(name=ft.icons.STAR, color='yellow')
                                                                           ])
                                                                    
                                                            ), on_click=click_background, width=420)
    
    uploadf_btn = ft.ElevatedButton("Upload files and translate", on_click=click_uploadf)
    write_tra_btn = ft.ElevatedButton("Enter text and translate", on_click=click_write_translate)
    settings_btn = ft.ElevatedButton("Settings", on_click=click_settings)
    quit_btn = ft.ElevatedButton("Quit", on_click=click_quit)
    back_icon_btn = ft.IconButton(icon=ft.icons.ARROW_BACK_ROUNDED, on_click=lambda _: page.go("/"))
    menu_btn_col = ft.Column([background_btn, uploadf_btn, write_tra_btn, settings_btn, quit_btn], 
                             alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.START, expand=True)


    # data table for the text + translation pair, displayed when translating inbackground mode
    trans_table = ft.DataTable(
                                border=ft.border.all(2, "grey"),
                                border_radius=10,
                                vertical_lines=ft.border.BorderSide(3, "grey"),
                                horizontal_lines=ft.border.BorderSide(1, "grey"),
                                columns=
                                [
                                ft.DataColumn(ft.Text("Original Text")), 
                                ft.DataColumn(ft.Text("Translated Text")),
                                ft.DataColumn(ft.Text("Select"))
                                ], 
                                rows=[], show_checkbox_column=True)


    """
    Settings:
    1. sett_app_fw - Bring app to foreground on translation requests when this is checked
    2. sett_stop_key - Stop background translation shortcut button for background translation mode
    3. sett_dest_lan - Translation destination language for background translation mode
    4. sett_font - Font selection
    5. sett_font_size - Font size selection
    6. sett_theme - theme mode selection
    """
    sett_app_fw = ft.Checkbox(label="Bring app to foreground on translation requests", value=False, width=500, height=70)
    shortcuts = []
    for i in range(1,13):
        shortcuts.append(ft.dropdown.Option("F"+str(i)))
    sett_stop_key = ft.Dropdown(label="Shortcut to stop background translations", options=shortcuts, value='F12', width=500)
    sett_dest_lan = ft.Dropdown(label="Translation destination language", options=[ft.dropdown.Option(key='en', text='English'),
                                                                       ft.dropdown.Option(key='es', text='Spanish'),
                                                                       ft.dropdown.Option(key='de', text='German'),
                                                                       ft.dropdown.Option(key='he', text='Hebrew')],
                                                                       value='en', width=500)

    translate_btn = ft.ElevatedButton("Translate", on_click=translate_new_text)

    #TODO: font + font size setting func
    sett_font = ft.Dropdown(label="Font", options=[], width=500)
    sett_font_size = ft.Dropdown(label="Font Size", options=[], width=500)
    sett_theme = ft.Dropdown(label="App Theme", options=[
                                                        ft.dropdown.Option(key=ft.ThemeMode.DARK, text='Dark'),
                                                        ft.dropdown.Option(key=ft.ThemeMode.LIGHT, text='Light'),
                                                        ft.dropdown.Option(key=ft.ThemeMode.SYSTEM, text='System Default')],
                                                                       value=ft.ThemeMode.DARK, width=500, on_change=change_theme)



    """
    App view navigation (illusion of multiple 'pages'):

    Root (Main menu) -                              '/'
    Background mode NOT ACTIVE -                    '/run_background'
    Background mode ACTIVE -                        '/stop_background'
    Upload files mode -                             '/upload_files'
    Write and translate mode -                      '/write_and_translate'
    Settings -                                      '/settings'
    Store (troll) -                                 '/store'
    """
    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        main_label,
                        ft.Divider(opacity=0, thickness=30),
                        menu_btn_col,
                        ft.AppBar(title=ft.Text("Give me your credit card information."), bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.ElevatedButton("Visit Store", on_click=lambda _: page.go("/store")),
                    ],
                )
            )
        if page.route == "/run_background":
            page.views.append(
                ft.View(
                    "/run_background",
                    [
                        ft.AppBar(leading=back_icon_btn,title=ft.Text("Select any text and press Right-Shift. The app will translate it for you."), 
                                  bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.ElevatedButton("Start Translating", on_click=click_start_trans),
                        ft.ElevatedButton("Settings", on_click=click_settings),
                        ft.ElevatedButton("Export Selected translations", on_click=clicked_export_translations),
                        trans_table
                    ], scroll=ft.ScrollMode.AUTO
                )
            )
        if page.route == "/stop_background":
            page.views.append(
                ft.View(
                    "/stop_background",
                    [
                        ft.AppBar(leading=None, title=ft.Text("Select any text and press Right-Shift. The app will translate it for you."), 
                                  bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.ElevatedButton("Stop Translating", on_click=click_stop_trans),
                        ft.ElevatedButton("Export Selected translations", on_click=clicked_export_translations),
                        trans_table
                    ], scroll=ft.ScrollMode.AUTO
                )
            )
        if page.route == "/upload_files":
            page.views.append(
                ft.View(
                    "/upload_files",
                    [
                        ft.AppBar(leading=back_icon_btn, title=ft.Text("Upload your files & translate to your chosen language"), 
                                  bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.Row(controls=[ft.ElevatedButton("Upload Files..", on_click=on_upload_files)]),
                        ft.ElevatedButton("Settings", on_click=click_settings),
                        ft.ElevatedButton("Go Home", on_click=lambda _: page.go("/")),
                    ],
                )
            )
        if page.route == "/write_and_translate":
            page.views.append(
                ft.View(
                    "/write_and_translate",
                    [
                        ft.AppBar(leading=back_icon_btn, title=ft.Text("Enter text and translate"), bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.Row(controls=[ft.Container(content=ft.Text("Translation..", selectable=True), width=500, height=500, border=ft.border.all(1, "grey"), padding=10),
                                         ft.Container(content=ft.TextField(label="Enter Text..", multiline=True, autofocus=True, max_length=3900),
                                                      width=500, height=500, border=ft.border.all(1, "grey"), padding=10)
                                        ]
                              ),
                        ft.Row(controls=[sett_dest_lan,
                                         translate_btn]),
                    ],
                )
            )
        if page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(leading=back_icon_btn, title=ft.Text("Settings"), bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.Text("HoverTranslate Settings", style=ft.TextThemeStyle.DISPLAY_SMALL),
                        sett_app_fw,
                        sett_stop_key,
                        sett_dest_lan,

                        ft.Text("General Settings", style=ft.TextThemeStyle.DISPLAY_SMALL),
                        sett_font,
                        sett_font_size,
                        sett_theme
                    ],
                )
            )
        if page.route == "/store":
            page.views.append(
                ft.View(
                    "/store",
                    [
                        ft.AppBar(leading=back_icon_btn, title=ft.Text("Store (Give me your credit card information.)"), 
                                  bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.ElevatedButton("Go Home", on_click=lambda _: page.go("/")),
                    ],
                )
            )
        page.update()

    # pop current view when swapping views ('pages')
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

    # googletrans lib object
    trans = Translator()

    # table where selected rows will get exported
    data_to_export = ft.DataTable(
                                border=ft.border.all(2, "grey"),
                                border_radius=10,
                                vertical_lines=ft.border.BorderSide(3, "grey"),
                                horizontal_lines=ft.border.BorderSide(1, "grey"),
                                columns=
                                [
                                ft.DataColumn(ft.Text("Original Text")), 
                                ft.DataColumn(ft.Text("Translated Text"))
                                ], 
                                rows=[])
    
    # modal dialog button setup
    dlg_modal = ft.AlertDialog(
        #modal=True,
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you really want to delete System32?"),
        actions=[
            ft.TextButton("Yes", on_click=yes_export_to_csv),
            ft.TextButton("No", on_click=close_dlg),
        ],
        on_dismiss=lambda e: print("Modal dialog dismissed!")
    )

    # filepicker object setup for saving
    fp = ft.FilePicker(on_result=create_and_export_csv)
    page.overlay.append(fp)
    page.update()

    # filepicker object setup for "uploading" files
    fp_upload = ft.FilePicker(on_result=translate_selected_files)
    page.overlay.append(fp_upload)
    page.update()

    translated = ""



ft.app(target=main)
