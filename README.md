# Hover-Translate
Python Flet app for translating any selected text, with some additional features


The main features of the app are:
1. Background translations for any selected text. Just hit R-Shift. You can select the the pairs of text+translation to be exported to a CSV file.
2. Upload docx/doc/txt files and have them translated.
3. Input text and translate just like google translate.

The app supports dark theme :)

*The input language is set to be automatically detected, and the output translation language can be changed from the settings tab.*
At the moment the app is configured with the following output languages: Enligsh, Spanish, German, and Hebrew.
113 languages are supported by Googletrans-lib, visit the docs to see the dict and choose your languages:
https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages

To add the new language to the selection of output languages just edit *sett_dest_lan* to have a new *ft.dropdown.Option(key='SELECTED_LANG_KEY', text='LANG_NAME')*

