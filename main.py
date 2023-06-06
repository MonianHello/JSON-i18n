import os
import json
from PySide2.QtWidgets import QApplication, QFileSystemModel, QTreeView, QVBoxLayout, QMainWindow, QPushButton, QTextEdit, QFileDialog, QMessageBox, QTableView, QTableWidgetItem, QHeaderView,QApplication, QMainWindow, QVBoxLayout, QLineEdit,QTabWidget,QPlainTextEdit,QLabel,QSpinBox,QListView,QAction,QWidget,QDialog,QCheckBox,QFontComboBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, Qt
from PySide2 import QtCore, QtWidgets,QtGui
from PySide2.QtGui import QStandardItem, QStandardItemModel,QIntValidator
import sys
from PySide2.QtGui import QPalette, QColor
from PySide2.QtGui import QFont

from PySide2.QtWidgets import QApplication,QFontDialog
from PySide2.QtWidgets import QMainWindow
import configparser
import requests
import uuid
from bs4 import BeautifulSoup
import sys
import re
def initFolder():
    folder_path = "TranslateFiles"
    # 检查目录是否存在
    if not os.path.exists(folder_path):
        # 如果不存在，则创建新目录
        os.makedirs(folder_path)
        print(f"创建 '{folder_path}' 文件夹成功！")
    else:
        print(f"文件夹 '{folder_path}' 已存在。")
def initConfig(config_file='config.ini'):

    global api_key,secret_key,enable_translate
    # 判断配置文件是否存在，若不存在则新建配置文件并初始化
    if not os.path.exists(config_file):
        config = configparser.ConfigParser()
        config['BAIDU_TRANSLATE_API'] = {'api_key': '',
                                        'secret_key': '',
                                        'enable': 'false'}
        config['UI_FONT'] = {'font_family': '',
                                        'font_size': ''}
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

    # 读取配置文件
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # 获取百度翻译API的AK、SK和是否开启机翻
    api_key = config.get('BAIDU_TRANSLATE_API', 'api_key')
    secret_key = config.get('BAIDU_TRANSLATE_API', 'secret_key')
    enable_translate = config.getboolean('BAIDU_TRANSLATE_API', 'enable')

def add_unique_id_to_json(file_path):
    """
    为 JSON 文件添加唯一标识符。

    参数：
    file_path (str)：JSON 文件路径。

    返回值：
    str：生成或已存在的唯一标识符。
    """

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
        print("由于未知原因，无法翻译文本\"{}\"。请参考以下错误信息：\n{}\n{}".format(text, response.json(), e))
    return translated_text

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

        #QAction
        self.actionClearSpaces.triggered.connect(self.handleActionClearSpaces)
        self.actionSettings.triggered.connect(self.handleActionSettings)

        #禁止用户编辑replacelistView
        self.replacelistView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        #设置数字校验器
        self.reviewJumpPageLineEdit.setValidator(QIntValidator())
        #绑定回车事件
        self.searchLineEdit.returnPressed.connect(self.on_searchLineEdit_return_pressed)
        self.replacelineEdit.returnPressed.connect(self.on_replacelineEdit_return_pressed)
        self.reviewJumpPageLineEdit.returnPressed.connect(self.on_reviewJumpPageLineEdit_return_pressed)

        # 创建文件浏览器模型
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(desktop_path)
        self.model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllEntries)
        # 将模型设置为 QTreeView 的模型
        self.tree_view.setModel(self.model)
        # 设置根索引为桌面文件夹的索引
        root_index = self.model.index(desktop_path)
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
    def handleActionSettings(self):
        # 创建设置对话框
        settings_dialog = SettingsDialog(self)
        settings_dialog.setWindowTitle("Settings")
        
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
        row_index = int(first_piece) - 1  # 从 0 开始计算行数

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
        print(searchResult)
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
        # 获取当前的模型
        model = self.dict_table.model()
        index = self.tree_view.currentIndex()
        file_path = self.get_file_path(index)
        uuid = add_unique_id_to_json(file_path)
        print(uuid)
        TranslateFilespath = 'TranslateFiles/' + uuid + '.json'
        if os.path.exists(TranslateFilespath):
            print('翻译文件存在')
            for row in range(model.rowCount()):
                # 跳过第一列值为'MonianHelloTranslateUUID'的行
                item = model.item(row, 0)
                print(item.text())
                if item and item.text() == 'MonianHelloTranslateUUID':
                    continue
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
            print(uuid)
            TranslateFilespath = 'TranslateFiles/' + uuid + '.json'
            if os.path.exists(TranslateFilespath):
                print('翻译文件存在')
                translationFileExists = True
            else:
                print('翻译文件不存在')
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
            json.dump(data, f, indent=4)

        # 显示保存成功消息框
        msg_box = QMessageBox(QMessageBox.Information, "提示信息", "文件保存成功！")
        msg_box.exec_()
    def on_reviewNextPushButton_clicked(self):
        model = self.dict_table.model()
        
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
        print(f"Selected row: {logicalIndex}")
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
        
        print(f"Selected tab index: {index}")
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

        if not enable_translate:
            QMessageBox.warning(self, '错误', '配置文件中未启用翻译功能')
            return

        # 打开选中的 JSON 文件，并按 key:value 的形式显示其中的内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            content = json.loads(file_content)
            keys = []
            values = []
            for key, value in content.items():
                keys.append(key)
                values.append(value)

        # 准备翻译
        translates = []
        item_count = len(keys)
        from_lang = "en"  # 源语言为英语
        to_lang = "zh"  # 目标语言为中文

        # 翻译每个条目，并保存到新的字典中
        for i, key in enumerate(keys):
            if key == "MonianHelloTranslateUUID":
                del content[key]
                continue
            value = str(values[i])
            try:
                access_token = get_access_token(api_key, secret_key)
            except:
                QMessageBox.warning(self, '鉴权错误', '无法通过鉴权认证。请检查您提供的百度AK/SK是否正确并具有访问该服务的权限')
            translates.append(translate_text(str(value), from_lang, to_lang, access_token))
            progress = (i + 1) / item_count * 100
            print(f'翻译进度：{progress:.2f}%')  # 更新进度条
        print("完成")
        translated_dict = dict(zip(keys, translates))

        # 将翻译结果保存到新的 JSON 文件中
        uuid = add_unique_id_to_json(file_path)
        with open('TranslateFiles/'+uuid+'.json', 'w', encoding='utf-8') as f:
            json.dump(translated_dict, f, indent=4)

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
            print("读取到替换字符串：",newString)
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
                    
                    if self.oldString in i:
                        updates.append(temp)
                        # new_values.append("op")
                        # print("在",i,"中发现",self.oldString)
                        new_values.append(i.replace(self.oldString, newString))
                    else:
                        # print("在",i,"中未发现",self.oldString)
                        pass
                    temp += 1
                # print(updates)
                # print(new_values)
                
                updates = [updates[i-1] for i in needReplaces]
                new_values = [new_values[i-1] for i in needReplaces]

                newdata=[]
                newdata.append(f"更新了以下数据：")
                for i, update in enumerate(updates):
                    newdata.append(f"{data[update]} => {new_values[i]} ")
                
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
            print("读取到被替换字符串：",self.oldString)
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
                if self.oldString in i:
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

        self.akLineEdit = self.settings_ui.findChild(QLineEdit, 'akLineEdit')
        self.skLineEdit = self.settings_ui.findChild(QLineEdit, 'skLineEdit')
        self.tranCheckBox = self.settings_ui.findChild(QCheckBox, 'tranCheckBox')
        self.tranTestPushButton = self.settings_ui.findChild(QPushButton, 'tranTestPushButton')

        self.fontSizeSpinBox = self.settings_ui.findChild(QSpinBox, 'fontSizeSpinBox')
        self.fontComboBox = self.settings_ui.findChild(QFontComboBox, 'fontComboBox')
        self.fontPreviewLabel = self.settings_ui.findChild(QLabel, 'fontPreviewLabel')

        # 将前两个控件的值改变信号与相应的槽函数关联
        self.fontComboBox.currentFontChanged.connect(self.changeFontFamily)
        self.fontSizeSpinBox.valueChanged.connect(self.changeFontSize)

    def changeFontFamily(self, font):
        # 更改字体类型，更新字体预览标签
        font_size = self.fontSizeSpinBox.value()
        font = QFont(font.family(), font_size)
        self.fontPreviewLabel.setFont(font)
        print(font)

    def changeFontSize(self, font_size):
        # 更改字体大小，更新字体预览标签
        font_family = self.fontComboBox.currentFont().family()
        font = QFont(font_family, int(font_size))
        self.fontPreviewLabel.setFont(font)
        print(font_size)
def darkmode():
    app.setStyle('Fusion')
    

    # 获取系统默认调色板
    palette = QPalette()

    # 将窗口背景色设置为灰暗
    palette.setColor(QPalette.Window, QColor(53, 53, 53))

    # 将窗口文本颜色设置为浅色
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))

    # 背景色和文本颜色为灰暗和浅色
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.Base, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(233, 233, 233))
    palette.setColor(QPalette.Text, QColor(233, 233, 233))

    # 禁用按钮的文本颜色为暗色
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    # 将应用程序的调色板设置为新的调色板
    app.setPalette(palette)

if __name__ == '__main__':
    initFolder()
    initConfig()
    app = QApplication([])
    # darkmode()
    # 创建文件浏览器
    file_browser = FileBrowser()
    # 运行应用程序事件循环
    sys.exit(app.exec_())