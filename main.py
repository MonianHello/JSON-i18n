import os
import base64
import json
import sys
import configparser
import requests
import uuid
from bs4 import BeautifulSoup

from PySide2 import QtCore, QtWidgets,QtGui
from PySide2.QtWidgets import QTreeView, QVBoxLayout, QMainWindow, QPushButton, QFileDialog, QMessageBox, QTableView, QTableWidgetItem, QHeaderView,QApplication, QVBoxLayout, QLineEdit,QTabWidget,QPlainTextEdit,QLabel,QSpinBox,QListView,QAction,QDialog,QCheckBox,QFontComboBox,QProgressBar,QShortcut
from PySide2.QtGui import QKeySequence,QFont,QPalette, QColor,QStandardItem, QStandardItemModel,QIntValidator
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QThread, Signal,QFile, Qt



def initFolder():
    folder_path = "TranslateFiles"
    # 检查目录是否存在
    if not os.path.exists(folder_path):
        # 如果不存在，则创建新目录
        os.makedirs(folder_path)
        # print(f"创建 '{folder_path}' 文件夹成功！")
    else:
        pass
        # print(f"文件夹 '{folder_path}' 已存在。")
def initConfig():
    global config
    # global api_key,secret_key,enable_translate,ui_font_Family,ui_font_Size,dirname
    # 判断配置文件是否存在，若不存在则新建配置文件并初始化
    if not os.path.exists('config.ini'):
        config = configparser.ConfigParser()
        config['BAIDU_TRANSLATE_API'] = {'api_key': '',
                                        'secret_key': '',
                                        'enable': 'false'}
        config['UI_FONT'] = {'ui_font_Family': '5b6u6L2v6ZuF6buR',
                             'ui_font_Size': '10'}
        config['SYSTEM_SETTINGS'] = {'dirname': '',
                                     'dark_mode':'false',
                                     'auto_save_layout':'false',
                                     'layout':'',
                                     'case_sensitive':'false'}
        with open('config.ini', 'w', encoding='utf-8') as f:
            config.write(f)

    # 读取配置文件
    config = configparser.ConfigParser()
    with open('config.ini', 'r', encoding='utf-8') as f:
        config.read_file(f)
    
    # 获取百度翻译API的AK、SK和是否开启机翻
    try:
        api_key = config.get('BAIDU_TRANSLATE_API', 'api_key')
        secret_key = config.get('BAIDU_TRANSLATE_API', 'secret_key')
        enable_translate = config.getboolean('BAIDU_TRANSLATE_API', 'enable')
        ui_font_Family = config.get('UI_FONT', 'ui_font_Family')
        ui_font_Size = config.getint('UI_FONT', 'ui_font_Size')
        dirname = base64.b64decode(config.get('SYSTEM_SETTINGS', 'dirname')).decode('utf-8')
        dark_mode = config.getboolean('SYSTEM_SETTINGS', 'dark_mode')
        auto_save_layout = config.getboolean('SYSTEM_SETTINGS', 'auto_save_layout')
        case_sensitive = config.getboolean('SYSTEM_SETTINGS', 'case_sensitive')
        layout = config.get('SYSTEM_SETTINGS', 'layout')
    except:
        QMessageBox.warning(None, "错误", "配置文件出现错误，已重置为初始值")
        if os.path.exists("config.ini"):
            os.remove("config.ini")
        initConfig()
def add_unique_id_to_json(file_path):

    # 加载并解析 JSON 文件
    def parse_json_file(file_path):
        with open(file_path, 'r',encoding='utf-8') as f:
            data = json.load(f)
        return data

    # 保存 JSON 文件
    def save_json_file(data, file_path):
        with open(file_path, 'w',encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    # 解析 JSON 文件
    data = parse_json_file(file_path)
    
    # 检查是否已经包含 "MonianHelloTranslateUUID" 键
    if "MonianHelloTranslateUUID" in data:
        return data["MonianHelloTranslateUUID"]

    # 获取第一个键值对的键
    key = list(data.keys())[0]

    # 生成唯一标识符
    unique_id = str(uuid.uuid4())

    # 将唯一标识符添加到字典中
    data['MonianHelloTranslateUUID'] = unique_id

    # 保存 JSON 文件
    save_json_file(data, file_path)

    # 返回唯一标识符
    return unique_id
def get_access_token(api_key, secret_key):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    response = requests.get(url, params=params)
    result = response.json()
    access_token = result["access_token"]
    return access_token
def translate_text(text, from_lang, to_lang, access_token):
    url = "https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1"
    headers = {
        "Content-Type": "application/json;charset=utf-8"
    }
    body = {
        "from": from_lang,
        "to": to_lang,
        "q": text
    }
    params = {
        "access_token": access_token
    }
    response = requests.post(url, headers=headers, params=params, json=body)

    result = response.json()
    try:
        translated_text = result["result"]["trans_result"][0]["dst"]
    except Exception as e:
        translated_text = ""
        QMessageBox.warning(QMessageBox.warning, '翻译错误', "由于未知原因，无法翻译文本\"{}\"。请参考以下错误信息：\n{}\n{}".format(text, response.json(), e))
    return translated_text
class TranslatorThread(QThread):
    finished = Signal()
    progress = Signal(int)
    error = Signal(str)

    def __init__(self, file_path, from_lang, to_lang, api_key, secret_key):
        super().__init__()
        self.file_path = file_path
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.api_key = api_key
        self.secret_key = secret_key

    def run(self):
        initFolder()
        try:
            access_token = get_access_token(self.api_key, self.secret_key)
        except Exception as e:
            self.error.emit(str(e))
        else:
            uuid = add_unique_id_to_json(self.file_path)
            try:
                # 如果已经有保存翻译结果的文件，则读取该文件，将其转为 Python 字典
                with open('TranslateFiles/'+uuid+'.json', 'r', encoding='utf-8') as f:
                    translated_dict = json.load(f)
            except FileNotFoundError:
                # 如果没有保存翻译结果的文件，则将 translated_dict 初始化为空字典
                translated_dict = {}

            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)

                keys = []
                values = []
                for key, value in content.items():
                    keys.append(key)
                    values.append(value)

                item_count = len(keys)
                for i, key in enumerate(keys):
                    # 如果 key 已经在字典中，则跳过本次循环
                    if key in translated_dict:
                        continue

                    # 跳过特定 key
                    if key == "MonianHelloTranslateUUID":
                        continue

                    value = str(values[i])
                    translated_value = translate_text(str(value), self.from_lang, self.to_lang, access_token)

                    # 添加新翻译到字典中
                    translated_dict[key] = translated_value

                    progress = (i+1) / item_count * 100
                    self.progress.emit(progress)  # 更新进度条

                    # 将字典实时保存到文件中
                    with open('TranslateFiles/'+uuid+'.json', 'w', encoding='utf-8') as f:
                        json.dump(translated_dict, f, indent=4)
            self.finished.emit()
class FileBrowser(QMainWindow):
    def __init__(self):

        super(FileBrowser, self).__init__()
        self.row = 0
        self.replacelineEditonEdit = False
        
        # 加载UI文件
        ui_file = QFile('MainWindow.ui')
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # 从配置文件中读取字体信息
        font_family = base64.b64decode(config.get('UI_FONT', 'ui_font_Family')).decode('utf-8')
        font_size = config.getint('UI_FONT', 'ui_font_Size')

        # 应用保存在配置文件中的字体
        ui_font = QFont(font_family, font_size)
        app.setFont(ui_font)

        self.tree_view = self.window.findChild(QTreeView, 'treeView')
        self.printbutton = self.window.findChild(QPushButton, 'printButton')
        self.savebutton = self.window.findChild(QPushButton, 'saveButton')
        self.translatebutton = self.window.findChild(QPushButton, 'translateButton')
        self.copyButton = self.window.findChild(QPushButton, 'copyButton')
        self.selectAllPushButton = self.window.findChild(QPushButton, 'selectAllPushButton')
        self.invertSelectionPushButton = self.window.findChild(QPushButton, 'invertSelectionPushButton')
        self.dict_table = self.window.findChild(QTableView, 'TableView')
        self.searchLineEdit = self.window.findChild(QLineEdit, 'searchLineEdit')
        self.reviewJumpPageLineEdit = self.window.findChild(QLineEdit, 'reviewJumpPageLineEdit')
        self.searchTableView = self.window.findChild(QTableView, 'searchTableView')
        self.tabWidget = self.window.findChild(QTabWidget, 'tabWidget')
        self.originalReviewPlainTextEdit = self.window.findChild(QPlainTextEdit, 'originalReviewPlainTextEdit')
        self.translateReviewPlainTextEdit = self.window.findChild(QPlainTextEdit, 'translateReviewPlainTextEdit')
        self.machineTranslateReviewPlainTextEdit = self.window.findChild(QPlainTextEdit, 'machineTranslateReviewPlainTextEdit')
        self.reviewPreviousPushButton = self.window.findChild(QPushButton,'reviewPreviousPushButton')
        self.reviewNextPushButton = self.window.findChild(QPushButton,'reviewNextPushButton')
        self.reviewLabel = self.window.findChild(QLabel,'reviewLabel')
        self.replacelineEdit = self.window.findChild(QLineEdit,'replacelineEdit')
        self.replacelistView = self.window.findChild(QListView,'replacelistView')
        self.actionClearSpaces = self.window.findChild(QAction, 'actionClearSpaces')
        self.actionSettings = self.window.findChild(QAction, 'actionSettings')
        self.actionAbout = self.window.findChild(QAction, 'actionAbout')
        self.translateProgressBar = self.window.findChild(QProgressBar, 'translateProgressBar')
        
        #快捷键
        
        shortcutCtrl_F = QShortcut(QKeySequence('Ctrl+F'), self.searchLineEdit)
        shortcutCtrl_F.activated.connect(self.handle_Ctrl_F_action)
        shortcutCtrl_H = QShortcut(QKeySequence('Ctrl+H'), self.searchLineEdit)
        shortcutCtrl_H.activated.connect(self.handle_Ctrl_H_action)
        shortcutCtrl_Down = QShortcut(QKeySequence('Ctrl+Down'), self.replacelineEdit)
        shortcutCtrl_Down.activated.connect(self.handle_Ctrl_Down_action)
        shortcutCtrl_Up = QShortcut(QKeySequence('Ctrl+Up'), self.replacelineEdit)
        shortcutCtrl_Up.activated.connect(self.handle_Ctrl_Up_action)
        shortcutCtrl_A = QShortcut(QKeySequence('Ctrl+Shift+A'), self.selectAllPushButton)
        shortcutCtrl_A.activated.connect(self.handle_Ctrl_A_action)

        self.translateProgressBar.hide()
        #QAction
        self.actionClearSpaces.triggered.connect(self.handleActionClearSpaces)
        self.actionSettings.triggered.connect(self.handleActionSettings)
        self.actionAbout.triggered.connect(self.handleActionAbout)

        #禁止用户编辑replacelistView
        self.replacelistView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        #设置数字校验器
        self.reviewJumpPageLineEdit.setValidator(QIntValidator())
        #绑定回车事件
        self.searchLineEdit.returnPressed.connect(self.on_searchLineEdit_return_pressed)
        self.replacelineEdit.returnPressed.connect(self.on_replacelineEdit_return_pressed)
        self.reviewJumpPageLineEdit.returnPressed.connect(self.on_reviewJumpPageLineEdit_return_pressed)

        # 创建文件浏览器模型
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(base64.b64decode(config.get('SYSTEM_SETTINGS', 'dirname')).decode('utf-8'))
        self.model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllEntries)
        # 将模型设置为 QTreeView 的模型
        self.tree_view.setModel(self.model)
        # 设置根索引为桌面文件夹的索引
        root_index = self.model.index(base64.b64decode(config.get('SYSTEM_SETTINGS', 'dirname')).decode('utf-8'))
        self.tree_view.setRootIndex(root_index)
        
        self.tabWidget.currentChanged.connect(self.tabChanged)

        # 隐藏列
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        # 将“Name”列的宽度设置为固定值
        self.tree_view.setColumnWidth(0, 200)  # 设置“Name”列的宽度为 200 像素

        # 绑定双击事件
        self.tree_view.doubleClicked.connect(self.on_treeView_doubleClicked)
        # 将按钮与其回调函数关联
        self.printbutton.clicked.connect(self.on_printbutton_clicked)
        self.savebutton.clicked.connect(self.on_savebutton_clicked)
        self.translatebutton.clicked.connect(self.on_translatebutton_clicked)
        self.copyButton.clicked.connect(self.on_copyButton_clicked)
        self.reviewPreviousPushButton.clicked.connect(self.on_reviewPreviousPushButton_clicked)
        self.reviewNextPushButton.clicked.connect(self.on_reviewNextPushButton_clicked)
        self.invertSelectionPushButton.clicked.connect(self.on_invertSelectionPushButton_clicked)
        self.selectAllPushButton.clicked.connect(self.on_selectAllPushButton_clicked)
        self.invertSelectionPushButton.hide()
        self.selectAllPushButton.hide()
        self.dict_table.verticalHeader().sectionClicked.connect(self.handleHeaderClicked)

        # 显示窗口
        self.window.show()

        # 初始化百度翻译API
        self.translate = None

        # 在 __init__ 函数中连接 clicked 信号到响应函数
        self.replacelistView.clicked.connect(self.handle_replacelistView_cell_clicked)
    def handle_Ctrl_F_action(self):
        self.searchLineEdit.setFocus()
    def handle_Ctrl_H_action(self):
        self.replacelineEdit.setFocus()
    def handle_Ctrl_Down_action(self):
        self.on_reviewNextPushButton_clicked()
    def handle_Ctrl_A_action(self):
        self.on_selectAllPushButton_clicked()
    def handle_Ctrl_Up_action(self):
        self.on_reviewPreviousPushButton_clicked()
    def updateRootIndex(self):
        # 更新文件浏览器的根索引
        root_index = self.model.index(base64.b64decode(config.get('SYSTEM_SETTINGS', 'dirname')).decode('utf-8'))
        self.tree_view.setRootIndex(root_index)
    def handleActionSettings(self):
        # 创建设置对话框
        settings_dialog = SettingsDialog(self)
        # 显示新窗口
        settings_dialog.exec_()
    def handleActionClearSpaces(self):
        self.tabWidget.setCurrentIndex(0)
        model = self.dict_table.model()
        # 遍历所有行
        for row in range(model.rowCount()):
            # 获取当前行的 value 列的 QStandardItem 实例
            item = model.item(row, 1)
            # 获取该实例中的字符串并清除其中的空格
            text = item.text().replace(' ', '')
            # 将新字符串设置回该实例中
            item.setText(text)
    def handle_replacelistView_cell_clicked(self, index):
        # 获取所单击单元格的值
        value = self.replacelistView.model().data(index)
        # 将其按照空格分割并获取第一片
        try:
            first_piece = value.split(' ')[0]
        except IndexError:
            # 如果切片不成功就取消焦点
            self.dict_table.clearSelection()
            return
        # 将该数字转换为整数
        try:
            row_index = int(first_piece) - 1  # 从 0 开始计算行数
        except:
            pass
        # 将焦点移动到 dict_table 中对应的行
        model = self.dict_table.model()
        if row_index >= 0 and row_index < model.rowCount():
            self.dict_table.selectRow(row_index)
    def get_file_path(self, index):
        return self.model.filePath(index)
    def on_treeView_doubleClicked(self, index):
        file_path = self.get_file_path(index)
        if os.path.isfile(file_path):
            # 如果是文件则执行打印文件的回调函数
            self.on_printbutton_clicked()

        # “打印文件”按钮的回调函数
    def set_model_data(self, table, data):
        table.clear()
        table.setRowCount(len(data))
        table.setColumnCount(len(data[0]))
        header = QHeaderView(Qt.Orientation.Horizontal)
        table.setHorizontalHeader(header)
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                item = QTableWidgetItem(str(col))
                table.setItem(i, j, item)
    def search_dictionary(self, key):
        url = "https://dict.mcmod.cn/connection/search.php"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://dict.mcmod.cn",
            "Referer": "https://dict.mcmod.cn/"
        }
        data = {
            "key": key,
            "max":16,
            "range": 1
        }

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        # print(response.text)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            rows = table.find_all('tr')
        except:
            return 0

        data = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            data.append(row_data)

        # print(data)

        def extract_first_two_elements(array):
            extracted_array = [[sublist[0], sublist[1]] for sublist in array]
            # print(extracted_array)
            return extracted_array
        def swap_values(array):
            swapped_array = [[sublist[1], sublist[0]] for sublist in array]
            return swapped_array

        # 调用函数提取每个一维数组的前两个元素
        extracted_array = extract_first_two_elements(data)
        swapped_array = swap_values(extracted_array)
        return swapped_array 
    def on_searchLineEdit_return_pressed(self):
        searchResult= self.search_dictionary(self.searchLineEdit.text())
        # print(searchResult)
        if searchResult:
            keys = []
            values = []
            for i in searchResult:
                if i==['原文', '翻译结果']:
                    continue
                keys.append(i[0])
                values.append(i[1])
            model = QStandardItemModel(len(keys), 2, self)
            for i, key in enumerate(keys):

                value = str(values[i])
                model.setItem(i, 0, QStandardItem(key))
                model.setItem(i, 1, QStandardItem(value))
            # 将填充好数据的表格模型应用到 QTableView 中
            self.searchTableView.setModel(model)

            # 设置表头标题
            model.setHeaderData(0, Qt.Horizontal, "原文")
            model.setHeaderData(1, Qt.Horizontal, "翻译结果")
        else:
            model = QStandardItemModel(1, 1, self)
            model.setItem(0, 0, QStandardItem("无搜索结果"))
            self.searchTableView.setModel(model)
            model.setHeaderData(0, Qt.Horizontal, "")
    def on_copyButton_clicked(self):
        self.tabWidget.setCurrentIndex(0)
        # 获取当前的模型
        model = self.dict_table.model()
        index = self.tree_view.currentIndex()
        file_path = self.get_file_path(index)
        uuid = add_unique_id_to_json(file_path)
        # print(uuid)
        TranslateFilespath = 'TranslateFiles/' + uuid + '.json'
        if os.path.exists(TranslateFilespath):
            # print('翻译文件存在')
            for row in range(model.rowCount()):
                # 跳过第一列值为'MonianHelloTranslateUUID'的行
                # item = model.item(row, 0)
                # print(item.text())
                # if item and item.text() == 'MonianHelloTranslateUUID':
                #     continue
                # 交换第2、3列的值
                index1 = model.index(row, 1)
                index2 = model.index(row, 2)
                data1 = model.data(index1)
                data2 = model.data(index2)
                model.setData(index1, data2)
                model.setData(index2, data1)
    def on_printbutton_clicked(self):
        self.row = 0
        # 获取当前选中文件的路径
        self.tabWidget.setCurrentIndex(0)
        index = self.tree_view.currentIndex()
        file_path = self.get_file_path(index)

        # 判断是否为 JSON 文件
        if not os.path.splitext(file_path)[1].lower() == '.json':
            QMessageBox.warning(self, '错误', '不是 JSON 文件！')
            return

        try:
            # 打开选中的 JSON 文件，并按 key:value 的形式显示其中的内容
            uuid = add_unique_id_to_json(file_path)
            # print(uuid)
            TranslateFilespath = 'TranslateFiles/' + uuid + '.json'
            if os.path.exists(TranslateFilespath):
                # print('翻译文件存在')
                translationFileExists = True
            else:
                # print('翻译文件不存在')
                translationFileExists = False
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                content = json.loads(file_content)
                keys = []
                values = []
                for key, value in content.items():
                    if key == "MonianHelloTranslateUUID":
                        continue
                    keys.append(key)
                    values.append(value)

                if translationFileExists:
                    with open(TranslateFilespath, 'r',encoding='utf-8') as ff:
                        data2 = json.load(ff)
                    model = QStandardItemModel(len(keys), 3, self)
                    for i, key in enumerate(keys):
                        value = str(values[i])
                        model.setItem(i, 0, QStandardItem(key))
                        model.setItem(i, 1, QStandardItem(value))
                        model.setItem(i, 2, QStandardItem(data2.get(key)))
                else:
                    model = QStandardItemModel(len(keys), 2, self)
                    for i, key in enumerate(keys):
                        value = str(values[i])
                        model.setItem(i, 0, QStandardItem(key))
                        model.setItem(i, 1, QStandardItem(value))
                        
                # 将填充好数据的表格模型应用到 QTableView 中
                self.dict_table.setModel(model)

                # 设置表头标题
                model.setHeaderData(0, Qt.Horizontal, "键名")
                model.setHeaderData(1, Qt.Horizontal, "原文")
                model.setHeaderData(2, Qt.Horizontal, "译文")

        except ValueError:
            # 不是 JSON 格式，直接显示文本
            self.text_edit.setPlainText(file_content) 
    def on_savebutton_clicked(self):
        self.tabWidget.setCurrentIndex(0)
        # 获取表格中的数据
        model = self.dict_table.model()
        data = {}
        for row in range(model.rowCount()):
            key = model.index(row, 0).data()
            value = model.index(row, 1).data()
            data[key] = value
        # 将数据写入文件
        file_name = self.tree_view.selectedIndexes()[0].data()
        with open(file_name, 'w',encoding='utf-8') as f:
            json.dump(data, f, indent=4,ensure_ascii=False)

        # 显示保存成功消息框
        msg_box = QMessageBox(QMessageBox.Information, "提示信息", "文件保存成功！")
        msg_box.exec_()
    def on_reviewNextPushButton_clicked(self):
        model = self.dict_table.model()
        self.tabWidget.setCurrentIndex(1)
        if 0<=self.row and self.row<model.rowCount()-1:
            try:
            # 更新模型中的数据
                model.setData(model.index(self.row, 0), self.originalReviewPlainTextEdit.toPlainText())
                model.setData(model.index(self.row, 1), self.translateReviewPlainTextEdit.toPlainText())
            except:
                return 0
            self.row += 1
            self.reviewLabel.setText("第{}个/共{}个".format(self.row+1,model.rowCount()))
            self.tabChanged(1)
    def on_reviewPreviousPushButton_clicked(self):
        model = self.dict_table.model()
        self.tabWidget.setCurrentIndex(1)
        if 0<self.row and  self.row<=model.rowCount():
            try:
            # 更新模型中的数据
                model.setData(model.index(self.row, 0), self.originalReviewPlainTextEdit.toPlainText())
                model.setData(model.index(self.row, 1), self.translateReviewPlainTextEdit.toPlainText())
            except:
                return 0
            self.row -= 1   
            self.reviewLabel.setText("第{}个/共{}个".format(self.row+1,model.rowCount()))
            self.tabChanged(1)
    def handleHeaderClicked(self, logicalIndex):
        # print(f"Selected row: {logicalIndex}")
        if self.tabWidget.currentIndex() == 0:
            self.reviewLabel.setText("第{}个/共{}个".format(logicalIndex+1,self.dict_table.model().rowCount()))
            self.row = logicalIndex
            self.tabWidget.setCurrentIndex(1)
    def on_reviewJumpPageLineEdit_return_pressed(self):

        inputrow = 1
        inputrow = int(self.reviewJumpPageLineEdit.text())
        self.reviewJumpPageLineEdit.clear()
        try:
            model = self.dict_table.model()
            assert 0<= self.row <=model.rowCount()
            try:
                # 更新模型中的数据
                    model.setData(model.index(self.row, 0), self.originalReviewPlainTextEdit.toPlainText())
                    model.setData(model.index(self.row, 1), self.translateReviewPlainTextEdit.toPlainText())
            except:
                return 0
        except:
            return 0
        if 0 < inputrow and inputrow <= model.rowCount():
            self.row = inputrow-1
            try:
                self.reviewLabel.setText("第{}个/共{}个".format(self.row+1,self.dict_table.model().rowCount()))
                self.originalReviewPlainTextEdit.setPlainText(model.index(self.row, 0).data())
                self.translateReviewPlainTextEdit.setPlainText(model.index(self.row, 1).data())
                self.machineTranslateReviewPlainTextEdit.setPlainText(model.index(self.row, 2).data())
            except:
                return 0
    def tabChanged(self,index):
        
        # print(f"Selected tab index: {index}")
        try:
            model = self.dict_table.model()
            assert 0<= self.row <=model.rowCount()
        except:
            return 0

        if index == 1:
            try:
                self.reviewLabel.setText("第{}个/共{}个".format(self.row+1,self.dict_table.model().rowCount()))
                self.originalReviewPlainTextEdit.setPlainText(model.index(self.row, 0).data())
                self.translateReviewPlainTextEdit.setPlainText(model.index(self.row, 1).data())
                self.machineTranslateReviewPlainTextEdit.setPlainText(model.index(self.row, 2).data())
            except:
                return 0
        if index == 0:
            
            try:
            # 更新模型中的数据
                self.dict_table.selectRow(self.row)
                model.setData(model.index(self.row, 0), self.originalReviewPlainTextEdit.toPlainText())
                model.setData(model.index(self.row, 1), self.translateReviewPlainTextEdit.toPlainText())
            except:
                return 0
    def on_translatebutton_clicked(self):
        # 获取选中文件的路径
        index = self.tree_view.currentIndex()
        file_path = self.get_file_path(index)

        # 判断是否为 JSON 文件
        if not os.path.splitext(file_path)[1].lower() == '.json':
            QMessageBox.warning(self, '错误', '不是 JSON 文件！')
            return

        if not config.getboolean('BAIDU_TRANSLATE_API', 'enable'):
            QMessageBox.warning(self, '错误', '配置文件中未启用翻译功能')
            return

        # 显示进度条
        self.translateProgressBar.show()

        # 创建翻译线程，启动翻译
        self.translator_thread = TranslatorThread(file_path, "en", "zh", config.get('BAIDU_TRANSLATE_API', 'api_key'), config.get('BAIDU_TRANSLATE_API', 'secret_key'))
        self.translator_thread.finished.connect(self.on_translation_finished)
        self.translator_thread.progress.connect(self.translateProgressBar.setValue)
        self.translator_thread.error.connect(self.on_translation_failed)
        self.translator_thread.start()
    def on_translation_finished(self):
        # 隐藏进度条，恢复用户界面
        self.translateProgressBar.hide()
        # 刷新树形视图和属性视图
        self.on_printbutton_clicked()
    def on_translation_failed(self, error_msg):
        # 隐藏进度条，恢复用户界面
        self.translateProgressBar.hide()
        # 弹出错误提示框
        QMessageBox.warning(self, '翻译错误', f'翻译过程中发生错误：{error_msg}')
    def on_selectAllPushButton_clicked(self):
        # 获取视图绑定的模型
        model = self.replacelistView.model()

        # 遍历模型中的所有项，并将其选中状态设置为Checked
        for i in range(model.rowCount()-1):
            item = model.item(i+1)
            item.setCheckState(QtCore.Qt.Checked)  
    def on_invertSelectionPushButton_clicked(self):
        # 获取视图绑定的模型
        model = self.replacelistView.model()

        # 遍历模型中的所有项，并将其选中状态取反
        for i in range(model.rowCount()-1):
            item = model.item(i+1)
            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
    def on_replacelineEdit_return_pressed(self):
        if self.replacelineEditonEdit:
            newString = self.replacelineEdit.text()
            # print("读取到替换字符串：",newString)
            if not newString:
                self.replacelistView.model().removeRows(0, self.replacelistView.model().rowCount())
                self.replacelineEditonEdit = False
                self.replacelineEdit.clear()
                self.replacelineEdit.setPlaceholderText("请输入要替换的值")
                self.invertSelectionPushButton.hide()
                self.selectAllPushButton.hide()
                return 0
            self.invertSelectionPushButton.hide()
            self.selectAllPushButton.hide()
            self.tabWidget.setCurrentIndex(0)
            tab_index = self.tabWidget.currentIndex()

            needReplaces = []

            model = self.replacelistView.model()
            for row in range(model.rowCount()):
                item = model.item(row)
                # 判断该行item是否为复选框
                if item.isCheckable():
                    # 获取复选框状态
                    checked = item.checkState() == QtCore.Qt.CheckState.Checked
                    if checked:
                        needReplaces.append(row)

            if tab_index == 0:
                model = self.dict_table.model()
                
                data = []  # 一维数组
                for row in range(model.rowCount()):
                    key_item = model.item(row, 0)
                    value_item = model.item(row, 1)
                    if key_item and value_item:
                        data.append(value_item.text())

                updates = []     # 匹配到的序号列表
                new_values = []  # 替换的内容列表
                temp = 0

                for i in data:
                    if config.getboolean('SYSTEM_SETTINGS', 'case_sensitive'):
                        if self.oldString in i:
                            updates.append(temp)
                            new_values.append(i.replace(self.oldString, newString))
                        else:
                            pass
                        temp += 1
                    else:
                        if self.oldString.lower() in i.lower():
                            updates.append(temp)
                            new_values.append(i.replace(self.oldString, newString))
                        else:
                            pass
                        temp += 1
                # print(updates)
                # print(new_values)
                
                updates = [updates[i-1] for i in needReplaces]
                new_values = [new_values[i-1] for i in needReplaces]

                newdata=[]
                newdata.append(f"更新了以下数据：")
                for i, update in enumerate(updates):
                    newdata.append(f"{data[update]} → {new_values[i]} ")
                
                model2 = QtGui.QStandardItemModel()
                for item in newdata:
                    model2.appendRow(QtGui.QStandardItem(item))
                self.replacelistView.setModel(model2)

                # 遍历更新需要更新的单元格
                for row, new_value in zip(updates, new_values):
                    item = model.item(row, 1)
                    item.setData(new_value, QtCore.Qt.EditRole) 
            # model3 = QtGui.QStandardItemModel()
            # self.replacelistView.setModel(model3)
            self.replacelineEditonEdit = False
            self.replacelineEdit.clear()
            self.replacelineEdit.setPlaceholderText("请输入要替换的值")
        else:
            self.oldString = self.replacelineEdit.text()
            # print("读取到被替换字符串：",self.oldString)
            if not self.oldString:
                self.replacelistView.model().removeRows(0, self.replacelistView.model().rowCount())
                self.replacelineEditonEdit = False
                self.replacelineEdit.clear()
                self.replacelineEdit.setPlaceholderText("请输入要替换的值")
                self.invertSelectionPushButton.hide()
                self.selectAllPushButton.hide()
                return 0
            self.tabWidget.setCurrentIndex(0)
            tab_index = self.tabWidget.currentIndex()
            if tab_index == 0:
                model = self.dict_table.model()
                data = []  # 一维数组
                for row in range(model.rowCount()):
                    key_item = model.item(row, 0)
                    value_item = model.item(row, 1)
                    if key_item and value_item:
                        data.append(f"{row+1} {value_item.text()}")
            newdata2 = []
            newdata2.append(QtGui.QStandardItem("匹配到以下数据："))
            
            self.oldString = self.replacelineEdit.text()
            self.invertSelectionPushButton.show()
            self.selectAllPushButton.show()

            for i in data:
                if config.getboolean('SYSTEM_SETTINGS', 'case_sensitive'):
                    if self.oldString in i:
                        item = QtGui.QStandardItem(i)
                        item.setCheckable(True)  # 设置复选框
                        newdata2.append(item)
                else:
                    if self.oldString.lower() in i.lower():
                        item = QtGui.QStandardItem(i)
                        item.setCheckable(True)  # 设置复选框
                        newdata2.append(item)
                    
            model2 = QtGui.QStandardItemModel()
            for item in newdata2:
                model2.appendRow(item)

            self.replacelistView.setModel(model2)

            self.replacelineEditonEdit = True
            self.replacelineEdit.clear()
            self.replacelineEdit.setPlaceholderText("请输入替换后的值，留空以放弃操作")
            return 0
    def handleActionAbout(self):
        QMessageBox.information(None, '关于', 
'''<font size="4" color="red"><b>JSON-i18n</b></font><br/>
示例版本 2023.06.07<br/>
作者 : <a href="http://monianhello.top/" style="color:gray">MonianHello</a><br/>
QF-project : <a href="https://github.com/QF-project" style="color:gray">QF-project</a><br/>
代码库 : <a href="https://github.com/MonianHello/JSON-i18n" style="color:gray">github.com/MonianHello/JSON-i18n</a>''')
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        
        # 加载设置对话框UI文件
        ui_file = QFile('Settings.ui')
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.settings_ui = loader.load(ui_file)
        ui_file.close()
        
        # 将UI添加到对话框中
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.settings_ui)

        # 初始化 UI 控件
        self.akLineEdit = self.settings_ui.findChild(QLineEdit, 'akLineEdit')
        self.skLineEdit = self.settings_ui.findChild(QLineEdit, 'skLineEdit')
        self.tranCheckBox = self.settings_ui.findChild(QCheckBox, 'tranCheckBox')
        self.tranTestPushButton = self.settings_ui.findChild(QPushButton, 'tranTestPushButton')
        self.moveWorkFolderPushButton = self.settings_ui.findChild(QPushButton, 'moveWorkFolderPushButton')

        self.fontSizeSpinBox = self.settings_ui.findChild(QSpinBox, 'fontSizeSpinBox')
        self.fontComboBox = self.settings_ui.findChild(QFontComboBox, 'fontComboBox')
        self.fontPreviewLabel = self.settings_ui.findChild(QLabel, 'fontPreviewLabel')

        self.darkModeCheckBox = self.settings_ui.findChild(QCheckBox, 'darkModeCheckBox')
        self.caseSensitiveCheckBox = self.settings_ui.findChild(QCheckBox, 'caseSensitiveCheckBox')
        self.autoSaveLayoutCheckBox = self.settings_ui.findChild(QCheckBox, 'autoSaveLayoutCheckBox')
        self.layoutButton = self.settings_ui.findChild(QPushButton, 'layoutButton')
        self.savePushButton = self.settings_ui.findChild(QPushButton, 'savePushButton')
        self.cancelPushButton = self.settings_ui.findChild(QPushButton, 'cancelPushButton')
        

        # 在 UI 控件中显示当前设置
        self.akLineEdit.setText(config.get('BAIDU_TRANSLATE_API', 'api_key'))
        self.skLineEdit.setText(config.get('BAIDU_TRANSLATE_API', 'secret_key'))
        self.tranCheckBox.setChecked(config.getboolean('BAIDU_TRANSLATE_API', 'enable'))
        

        self.fontSizeSpinBox.setValue(config.getint('UI_FONT', 'ui_font_Size'))

        self.fontComboBox.setCurrentFont(QFont(base64.b64decode(config.get('UI_FONT', 'ui_font_Family')).decode('utf-8')))
        self.fontPreviewLabel.setFont(QFont(base64.b64decode(config.get('UI_FONT', 'ui_font_Family')).decode('utf-8'), config.getint('UI_FONT', 'ui_font_Size')))

        self.darkModeCheckBox.setChecked(config.getboolean('SYSTEM_SETTINGS', 'dark_mode'))
        self.autoSaveLayoutCheckBox.setChecked(config.getboolean('SYSTEM_SETTINGS', 'auto_save_layout'))
        self.caseSensitiveCheckBox.setChecked(config.getboolean('SYSTEM_SETTINGS', 'case_sensitive'))

        # 连接控件信号和槽函数
        self.fontComboBox.currentFontChanged.connect(self.changeFontFamily)
        self.fontSizeSpinBox.valueChanged.connect(self.changeFontSize)
        self.darkModeCheckBox.clicked.connect(self.changeDarkMode)
        self.caseSensitiveCheckBox.clicked.connect(self.changeCaseSensitive)
        self.autoSaveLayoutCheckBox.clicked.connect(self.changeAutoSaveLayout)
        self.savePushButton.clicked.connect(self.saveSettings)
        self.tranTestPushButton.clicked.connect(self.tranTest)
        self.moveWorkFolderPushButton.clicked.connect(self.moveWorkFolder)
        self.cancelPushButton.clicked.connect(self.close)

        shortcutESC = QShortcut(QKeySequence('ESC'), self.cancelPushButton)
        shortcutESC.activated.connect(self.close)
        
    def moveWorkFolder(self):
        config.set('SYSTEM_SETTINGS', 'dirname', base64.b64encode(str(QFileDialog.getExistingDirectory(None, "选择工作目录", "/", options=QFileDialog.Options()|QFileDialog.ShowDirsOnly)).encode("utf-8")).decode('utf-8'))
    def tranTest(self):
        try:
           get_access_token(self.akLineEdit.text(), self.skLineEdit.text())
        except:
            QMessageBox.warning(self, '鉴权错误', '无法通过鉴权认证。请检查您提供的百度AK/SK是否正确并具有访问该服务的权限')
        else:
            QMessageBox.information(self, '鉴权成功', "验证成功")
    def changeFontFamily(self, font):
        self.fontPreviewLabel.setFont(QFont(font.family(), self.fontSizeSpinBox.value()))

    def changeFontSize(self, size):
        self.fontPreviewLabel.setFont(QFont(self.fontComboBox.currentFont().family(), size))

    def changeDarkMode(self):
        if self.darkModeCheckBox.isChecked():
            config.set('SYSTEM_SETTINGS', 'dark_mode', 'True')
        else:
            config.set('SYSTEM_SETTINGS', 'dark_mode', 'False')
    def changeCaseSensitive(self):
        if self.caseSensitiveCheckBox.isChecked():
            config.set('SYSTEM_SETTINGS', 'case_sensitive', 'True')
        else:
            config.set('SYSTEM_SETTINGS', 'case_sensitive', 'False')
    def changeAutoSaveLayout(self):
        if self.autoSaveLayoutCheckBox.isChecked():
            config.set('SYSTEM_SETTINGS', 'auto_save_layout', 'True')
        else:
            config.set('SYSTEM_SETTINGS', 'auto_save_layout', 'False')

    def saveSettings(self):
        # 保存输入框和复选框的值到配置文件
        config.set('BAIDU_TRANSLATE_API', 'api_key', self.akLineEdit.text())
        config.set('BAIDU_TRANSLATE_API', 'secret_key', self.skLineEdit.text())
        config.set('BAIDU_TRANSLATE_API', 'enable', str(self.tranCheckBox.isChecked()))

        config.set('UI_FONT', 'ui_font_Family', base64.b64encode(str(self.fontComboBox.currentFont().family()).encode("utf-8")).decode('utf-8'))
        config.set('UI_FONT', 'ui_font_Size', str(self.fontSizeSpinBox.value()))
        try:
            with open('config.ini', 'w') as f:
                config.write(f)
        except:
            QMessageBox.warning(self, "警告", "保存失败")
        else:
            QMessageBox.information(self, "提示", "保存成功")
            file_browser.updateRootIndex()
            font_family = base64.b64decode(config.get('UI_FONT', 'ui_font_Family')).decode('utf-8')
            font_size = config.getint('UI_FONT', 'ui_font_Size')
            if config.getboolean('SYSTEM_SETTINGS', 'dark_mode'):
                darkmode()
            else:
                lightmode()
            # 应用保存在配置文件中的字体
            ui_font = QFont(font_family, font_size)
            app.setFont(ui_font)

            # 关闭设置对话框
            self.close()
    def changeFontFamily(self, font):
        # 更改字体类型，更新字体预览标签
        font_size = self.fontSizeSpinBox.value()
        font = QFont(font.family(), font_size)
        self.fontPreviewLabel.setFont(font)
        # print(font)

    def changeFontSize(self, font_size):
        # 更改字体大小，更新字体预览标签
        font_family = self.fontComboBox.currentFont().family()
        font = QFont(font_family, int(font_size))
        self.fontPreviewLabel.setFont(font)
        # print(font_size)
def darkmode():
    # 初始化应用程序
    app = QApplication.instance()

    # 设置 Fusion 风格
    app.setStyle('Fusion')

    # 获取系统默认调色板
    palette = QPalette()

    # 将窗口背景色设置为灰暗
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)

    # 将禁用状态下的文本颜色设置为暗色
   
    # 将控件的背景颜色和文本颜色设置为灰暗和浅色
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    # 将滚动条的背景颜色和文本颜色设置为灰暗和浅色
    palette.setColor(QPalette.Highlight, QColor(64, 64, 64).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.white)

    # 将应用程序的调色板设置为新的调色板
    app.setPalette(palette)
def lightmode():
    app.setStyle('Fusion')

    # 获取系统默认调色板
    palette = QPalette()

    # 将窗口背景色设置为浅灰色
    palette.setColor(QPalette.Window, QColor(240, 240, 240))

    # 将窗口文本颜色设置为黑色
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))

    # 背景色和文本颜色为浅灰色和黑色
    palette.setColor(QPalette.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))

    # 禁用按钮的文本颜色为深灰色
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    # 将应用程序的调色板设置为新的调色板
    app.setPalette(palette)
if __name__ == '__main__':
    app = QApplication([])

    initConfig()
    initFolder()
    dirname = None
    if not config.get('SYSTEM_SETTINGS', 'dirname'):
        dirname = QFileDialog.getExistingDirectory(None, "选择工作目录", "/", options=QFileDialog.Options()|QFileDialog.ShowDirsOnly)
        if not dirname:
            sys.exit()
        config.set('SYSTEM_SETTINGS', 'dirname', base64.b64encode(str(dirname).encode("utf-8")).decode('utf-8'))
        with open("config.ini", 'w', encoding='utf-8') as f:
            config.write(f)
    if config.getboolean('SYSTEM_SETTINGS', 'dark_mode'):
        darkmode()
    else:
        lightmode()
    # 创建文件浏览器
    file_browser = FileBrowser()
    # 运行应用程序事件循环
    sys.exit(app.exec_())