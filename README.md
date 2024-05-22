# XXT_Library_Auto 
**超星学习通图书馆系统自动化实现**
> 包括签到、预约、退座、暂离、查询空座位等功能 支持新旧两版系统

![svg](https://forthebadge.com/images/badges/made-with-python.svg)

![svg](https://forthebadge.com/images/badges/made-with-javascript.svg)

[![svg](https://github.com/WangJerry1229/WangJerry1229/raw/main/badge.svg)](https://wangjiayi.cool)

主体部分基于**Doone-skser**的 <a href="https://github.com/Doone-skser/SSA">SSA项目</a>
在项目基础上进行了一些功能修改 (原项目现已关闭)

新增的滑动验证码部分 逻辑主要参考了**9cats**的 <a href="https://github.com/9cats/caviar">caviar项目</a> 具体识别部分采用了 <a href="https://github.com/sml2h3/ddddocr">ddddocr</a>完成

本项目仅供**学习参考**使用 项目代码质量较差且**不保证未来维护**

UPDATE: 2023-5-31 
1. 添加了对最新的enc加密字段的支持(check/enc()) 相关部分并未完善 有需要的同学可以自行修改
2. 测试发现旧版系统中取消了seatId字段 可能还有其他改动尚未发现 欢迎反馈

UPDATE: 2024-5-22
适配了当前最新版本（未经过详细测试，提供修改内容供大家参考） Thanks to **Mr-Chenxii**
```python
# CX_Library.py.pdf
# 获取到最近一次预约的座位ID
def get_my_seat_id(self):
  # 270行的URL发生了改变，原URL会显示非法请求。
  response = self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/reservelist?seatId=602').json()['data']['reserveList']
  # 改为如下代码
  response = self.session.get(url='https://office.chaoxing.com/data/apps/seatengine/index?r=84.74181536220152&seatId=602&seatIdEnc=9e3e9d2f2ef09ac1').json()['data']['curReserves']
  # 279行的代码整行注释掉，type这段没有了
  #if index['type'] == -1:
  if index['today'] == self.today or index['today'] == self.tomorrow:
    result.append(index)

# check.py
  data = {
  'callback': "callback",
  'captchaId': "xxxxxxx",
  'type': "slide",
  'version': "1.1.14", -> 改为"1.1.18"
  'captchaKey': ckey,
  'token': token,
  'referer':  "https://office.chaoxing.com/front/third/apps/seatengine/select",
  }
  res = session.post('http://captcha.chaoxing.com/captcha/get/verification/image', data = data)
  captcha_data = json.loads(re.search(r'\{.*\}', res.text)[0])
  background = requests.get(captcha_data["imageVerificationVo"]["shadeImage"]).content
  target = requests.get(captcha_data["imageVerificationVo"]["cutoutImage"]).content
  # 这里把requests.get改为session.get
  token_new = captcha_data["token"]
```

```diff
! 滥用本项目代码所导致的一切后果与作者本人无关 请勿用于非法用途
```
