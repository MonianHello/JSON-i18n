import webview
import json
import requests
from bs4 import BeautifulSoup
import configparser
import os

# JSON文件路径
json_file = "en_us.json"

# 配置文件路径
config_file = 'config.ini'

# 加载JSON文件
with open(json_file, "r") as file:
    data = json.load(file)

# 判断配置文件是否存在，若不存在则新建配置文件并初始化
if not os.path.exists(config_file):
    config = configparser.ConfigParser()
    config['BAIDU_TRANSLATE_API'] = {'api_key': '',
                                    'secret_key': '',
                                    'enable': 'false'}
    with open(config_file, 'w') as f:
        config.write(f)

# 读取配置文件
config = configparser.ConfigParser()
config.read(config_file)

# 获取百度翻译API的AK、SK和是否开启机翻
api_key = config.get('BAIDU_TRANSLATE_API', 'api_key')
secret_key = config.get('BAIDU_TRANSLATE_API', 'secret_key')
enable_translate = config.getboolean('BAIDU_TRANSLATE_API', 'enable')


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
    translated_text = result["result"]["trans_result"][0]["dst"]
    return translated_text

class Api:
    def get_data(self):
        return data

    def update_value(self, key, value):
        if key in data:
            data[key] = value
            with open(json_file, "w") as file:
                json.dump(data, file)
            return True
        else:
            return False

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
            "max":10,
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
            return "无结果"

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

        def format_array_as_html_table(array):
            table_rows = ""
            for sublist in array:
                row = "<tr>"
                for element in sublist:
                    row += "<td>{}</td>".format(element)
                row += "</tr>"
                table_rows += row
            html_table = "<table>{}</table>".format(table_rows)
            return html_table

        # 调用函数提取每个一维数组的前两个元素
        extracted_array = extract_first_two_elements(data)
        swapped_array = swap_values(extracted_array)
        # 将提取的数组格式化为 HTML 表格
        html_table = format_array_as_html_table(swapped_array)

        return html_table
    

def generate_table_rows(data, translate=False):
    table_rows = ""


    if translate:
        from_lang = "en"  # 源语言为英语
        to_lang = "zh"  # 目标语言为中文
        try:
            access_token = get_access_token(api_key, secret_key)
        except:
            os.system('cscript assets/alert.vbs')
            for key, value in data.items():
                table_rows += "<tr><td>%s</td><td><input type='text' id='%s' value='%s' %s/></td><td id='currentValue_%s'>%s</td></tr>" % (
                    key,
                    key,
                    value,
                    "readonly" if isinstance(value, dict) or isinstance(value, list) else "",
                    key,
                    ""  # 设置新的值列标识的初始值
                )
            return table_rows
        
        translatelist = []
        
        def translate_and_track_progress(data, from_lang, to_lang, access_token):
            total_items = len(data)
            translated_items = 0

            for key, value in data.items():
                translated_text = str(translate_text(str(value), from_lang, to_lang, access_token))
                translatelist.append((key, value, translated_text))
                # print((key, value, translated_text))
                translated_items += 1

                # 计算进度百分比
                progress = int((translated_items / total_items) * 100)

                # 更新进度条
                print(f"翻译进程: [{progress}%] {'=' * progress}>{' ' * (100 - progress)}", end="\r")

            # print("\n翻译完成")

        # 在主函数 main() 中调用 translate_and_track_progress() 函数，并传递必要的参数。
        translate_and_track_progress(data, from_lang, to_lang, access_token)

        for key, value, translated_text in translatelist:
            table_rows += "<tr><td>%s</td><td><input type='text' id='%s' value='%s' %s/></td><td id='currentValue_%s'>%s</td></tr>" % (
                key,
                key,
                value,
                "readonly" if isinstance(value, dict) or isinstance(value, list) else "",
                key,
                translated_text
            )
    else:
        for key, value in data.items():
            table_rows += "<tr><td>%s</td><td><input type='text' id='%s' value='%s' %s/></td><td id='currentValue_%s'>%s</td></tr>" % (
                key,
                key,
                value,
                "readonly" if isinstance(value, dict) or isinstance(value, list) else "",
                key,
                ""  # 设置新的值列标识的初始值
            )

    return table_rows



def main():
    
    # HTML模板，用于显示JSON数据和更新值
    html_template = open("assets/index.html", "r", encoding="utf-8").read()

    # 生成HTML表格内容
    table_rows = ""
    # print(data.items())
    
    api = Api()

    table_rows = generate_table_rows(data, translate=enable_translate)

    html_content = html_template % table_rows

    # 创建webview窗口并加载HTML内容和API
    window = webview.create_window("JSON Editor", html=html_content, js_api=api,width=1500, height=900)

    # 启动webview
    webview.start()


if __name__ == "__main__":
    main()
