import pandas as pd
import requests
import time
from PIL import Image
import os
import re

def parse_coordinates(ra, dec):
    # 处理RA: 将05h34m32s格式转换为05+34+32
    ra = ra.replace('h', ' ').replace('m', ' ').replace('s', '')
    
    # 处理DEC: 将+22°00′52″格式转换为+22+00+52
    dec = dec.replace('°', ' ').replace('′', ' ').replace('″', '')
    
    return ra, dec

def calculate_size(size):
    # 如果尺寸小于等于3，返回15
    if size <= 3:
        return 15
    # 如果尺寸大于30，返回120，否则乘以4
    return 120 if size > 30 else size * 4

def resize_image(image_path, max_size=1000):
    # 打开图片
    with Image.open(image_path) as img:
        # 获取原始尺寸
        width, height = img.size
        
        # 如果宽和高都不超过1000像素，直接返回，不做处理
        if width <= max_size and height <= max_size:
            return
        
        # 计算缩放比例
        ratio = min(max_size / max(width, height), 1.0)
        
        # 计算新的尺寸
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 调整图片大小
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 保存调整后的图片
        resized_img.save(image_path)

def main():
    # 读取CSV文件
    df = pd.read_csv('targets_dss.csv')
    
    # 打印列名以便调试
    print("CSV文件的列名:", df.columns.tolist())
    
    # 确定正确的列名
    id_col = None
    ra_col = None
    dec_col = None
    size_col = None
    
    # 尝试找到正确的列名
    for col in df.columns:
        if col.lower() in ['id', 'target', 'name', 'object']:
            id_col = col
        elif any(x in col.lower() for x in ['ra', 'right ascension']):
            ra_col = col
        elif any(x in col.lower() for x in ['dec', 'declination']):
            dec_col = col
        elif any(x in col.lower() for x in ['size', 'major', 'axis']):
            size_col = col
    
    if not all([id_col, ra_col, dec_col, size_col]):
        print("无法识别所有必要的列。请检查CSV文件格式。")
        print(f"识别到的列: ID={id_col}, RA={ra_col}, DEC={dec_col}, Size={size_col}")
        return
    
    print(f"使用以下列: ID={id_col}, RA={ra_col}, DEC={dec_col}, Size={size_col}")
    
    base_url = "https://archive.stsci.edu/cgi-bin/dss_search"
    
    for index, row in df.iterrows():
        # 解析坐标
        ra, dec = parse_coordinates(row[ra_col], row[dec_col])
        
        # 计算尺寸
        size = calculate_size(row[size_col])
        
        # 构建URL参数
        params = {
            'v': 'poss2ukstu_red',
            'r': ra,
            'd': dec,
            'e': 'J2000',
            'h': str(size),
            'w': str(size),
            'f': 'gif',
            'c': 'none',
            'fov': 'NONE',
            'v3': ''
        }
        
        try:
            # 发送请求
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                # 保存图片
                output_file = f"{row[id_col]}.gif"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                # 调整图片大小
                resize_image(output_file)
                
                print(f"Successfully downloaded and resized {output_file}")
            else:
                print(f"Failed to download {row[id_col]}: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error processing {row[id_col]}: {str(e)}")
        
        # 等待5秒
        time.sleep(5)

if __name__ == "__main__":
    main()