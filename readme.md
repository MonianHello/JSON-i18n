# JSON翻译工具

这是一个使用Python编写的可以快速翻译JSON文件的工具。

程序第一次启动后会生成config.ini。使用机翻前需要前往百度开放平台获取ak/sk [文本翻译_机器翻译-百度AI开放平台 (baidu.com)](https://ai.baidu.com/tech/mt/text_trans)

之后修改config.ini文件中的AK和SK（不用加引号，例如`api_key = XXXXXXXXX`），并修改`enable`的值为True。

## 使用方法

将需要翻译的json文件重命名为en_us.json放在程序根目录下

运行main.py文件即可打开编辑器窗口，界面如下：

- `搜索`按钮：搜索模组翻译参考词典，用法为输入搜索内容，点击该按钮，出现搜索结果
- `复制机翻`按钮：将JSON文件键值对中的英文内容翻译为中文并自动替换
- `导出`按钮：将修改后的JSON文件导出为zh_cn.json

注意：目前只支持英文翻译为中文，若翻译失败则显示为空白。

## 实现原理

程序使用了webview模块创建窗口，并以HTML模板的形式呈现JSON文件内容。同时，使用BeautifulSoup库搜索模组翻译参考词典，实现查询，再使用百度翻译API实现中英文翻译，并在表格中作为第三列显示。

程序读取config.ini中的配置信息，判断是否启用机器翻译，若启用，则将键值对中的英文内容翻译为中文。

## 依赖库

- webview
- json
- requests
- bs4
- configparser
- os