import requests
import re
import os
import shutil
class GetImage(object):
    def __init__(self,url):
        print(url)
        self.url = url[0]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }
        self.dir_path = os.path.dirname(os.path.abspath(__file__))
        self.path = self.dir_path+'/'+url[1]
        isExists = os.path.exists(self.path)
        # 创建目录

        if isExists:
            shutil.rmtree(self.path)

        os.makedirs(self.path)
    def download(self,url):
        try:
            res = requests.get(url,headers=self.headers)
            return res
        except Exception as E:
            print(url+'下载失败,原因:'+E)


    def parse(self,res):
        content = res.content.decode()

        img_list = re.findall(r'background-image: url.*?&quot;(.*?)&quot;',content,re.S)

        img_list = ['https://www.anhengcloud.com/'+url for url in img_list]

        return img_list

    def parse2(self,res):
        content = res.content.decode()

        img_list = re.findall(r'<img.*?src="(.*?)"',content,re.S)

        img_list = ['https://www.anhengcloud.com/'+url for url in img_list]

        return img_list

    def save(self,res_img,file_name):
        if res_img:
            with open(file_name,'wb') as f:
                f.write(res_img.content)
            print(file_name+'下载成功')

    def run(self):
        # 下载
        res = self.download(self.url)
        # 解析
        url_list = self.parse(res)
        url_list += self.parse2(res)
        # 下载图片
        for url in url_list:
            res_img = self.download(url)
            name = url.strip().split('/').pop()
            file_name = self.path+'/'+name
            # 保存
            self.save(res_img,file_name)

if __name__ == '__main__':
    url_list = [
        # ['https://www.anhengcloud.com/','安恒云'],
        #         ['https://www.yundun.com/',"云盾"],
        #         ['https://www.aliyun.com/',"阿里云"],
        #         ['https://cloud.tencent.com/',"腾讯云"],
    ]
    for url in url_list:
        text = GetImage(url)
        text.run()